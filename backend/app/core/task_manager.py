"""
任务管理器（单例）- 优化版

改进：
- 实现实际的 WebSocket 广播逻辑
- 批量推送优化（节流）
- 任务过期清理
- 线程安全的状态更新
"""
import uuid
import logging
import threading
import asyncio
from datetime import datetime
from typing import Optional, Dict, List, Any, Set
from collections import defaultdict
from dataclasses import dataclass, field

from app.models.schemas import ConversionTask, ConversionConfig

logger = logging.getLogger(__name__)


@dataclass
class WebSocketConnection:
    """WebSocket 连接信息"""
    websocket: Any
    subscribed_tasks: Set[str] = field(default_factory=set)
    last_ping: datetime = field(default_factory=datetime.now)


class TaskManager:
    """任务管理器（单例 - 优化版）"""

    _instance: Optional['TaskManager'] = None
    _lock = threading.Lock()

    # 批量推送配置
    BATCH_INTERVAL_SECONDS = 0.5  # 批量推送间隔
    MAX_BATCH_SIZE = 10  # 每批最大消息数

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # 双重检查锁定模式
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.tasks: Dict[str, ConversionTask] = {}
        self.websocket_connections: Dict[str, WebSocketConnection] = {}

        # 待推送消息队列（按任务ID分组）
        self._pending_messages: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._message_lock = threading.Lock()

        # 启动后台推送任务
        self._running = True
        self._batch_thread = threading.Thread(target=self._batch_broadcast_worker, daemon=True)
        self._batch_thread.start()

        self._initialized = True
        logger.info("任务管理器初始化完成（优化版）")

    def create_task(self, config: ConversionConfig) -> str:
        """创建新任务"""
        import traceback

        task_id = str(uuid.uuid4())
        now = datetime.now()

        logger.info(f"[TaskManager.create_task] 开始创建任务")
        logger.info(f"[TaskManager.create_task] config 类型: {type(config)}")
        logger.info(f"[TaskManager.create_task] config 值: {config}")

        try:
            task = ConversionTask(
                task_id=task_id,
                status="pending",
                progress=0,
                current_step="",
                config=config,
                created_at=now,
                updated_at=now
            )
            logger.info(f"[TaskManager.create_task] ConversionTask 创建成功")
        except Exception as e:
            logger.error(f"[TaskManager.create_task] ConversionTask 创建失败: {e}")
            logger.error(traceback.format_exc())
            raise

        self.tasks[task_id] = task
        logger.info(f"[TaskManager.create_task] 任务已存储: {task_id}")
        return task_id

    def get_task(self, task_id: str) -> Optional[ConversionTask]:
        """获取任务状态"""
        return self.tasks.get(task_id)

    def update_progress(self, task_id: str, progress: int, step: str):
        """更新任务进度（线程安全）"""
        with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id].progress = progress
                self.tasks[task_id].current_step = step
                self.tasks[task_id].updated_at = datetime.now()

        # 添加到待推送队列（批量发送）
        self._queue_progress_message(task_id, progress, step)

    def add_log(self, task_id: str, log: str):
        """添加日志到任务并推送到 WebSocket

        Args:
            task_id: 任务 ID
            log: 日志内容
        """
        logger.info(f"[Task {task_id}] {log}")

        # 推送日志消息到 WebSocket
        self._queue_log_message(task_id, log)

    def _queue_progress_message(self, task_id: str, progress: int, step: str):
        """将进度消息添加到待推送队列"""
        message = {
            "type": "progress",
            "task_id": task_id,
            "progress": progress,
            "step": step,
            "timestamp": datetime.now().isoformat()
        }

        with self._message_lock:
            self._pending_messages[task_id].append(message)

            # 如果消息数量超过阈值，立即刷新
            if len(self._pending_messages[task_id]) >= self.MAX_BATCH_SIZE:
                messages = self._pending_messages[task_id]
                self._pending_messages[task_id] = []
                # 在锁外发送以避免阻塞
                self._send_batch_messages(task_id, messages)

    def _queue_log_message(self, task_id: str, log: str):
        """将日志消息添加到待推送队列

        Args:
            task_id: 任务 ID
            log: 日志内容
        """
        message = {
            "type": "log",
            "task_id": task_id,
            "log": log,
            "timestamp": datetime.now().isoformat()
        }

        with self._message_lock:
            self._pending_messages[task_id].append(message)

            # 日志消息立即刷新（不等待批量）
            messages = self._pending_messages[task_id]
            self._pending_messages[task_id] = []
            self._send_batch_messages(task_id, messages)

    def _batch_broadcast_worker(self):
        """后台批量推送工作线程"""
        import time

        while self._running:
            time.sleep(self.BATCH_INTERVAL_SECONDS)
            self._flush_pending_messages()

    def _flush_pending_messages(self):
        """刷新待推送消息"""
        with self._message_lock:
            if not self._pending_messages:
                return

            # 复制并清空待推送队列
            messages_to_send = dict(self._pending_messages)
            self._pending_messages.clear()

        # 发送消息
        for task_id, messages in messages_to_send.items():
            if messages:
                self._send_batch_messages(task_id, messages)

    def _send_batch_messages(self, task_id: str, messages: List[Dict[str, Any]]):
        """发送批量消息到 WebSocket"""
        import json

        if task_id not in self.websocket_connections:
            return

        connection = self.websocket_connections[task_id]
        if not connection.websocket:
            return

        try:
            # 合并消息为最后状态
            final_message = messages[-1]  # 取最后一条消息
            final_message["batch_count"] = len(messages)  # 添加批量计数

            # 异步发送
            if hasattr(connection.websocket, 'send_json'):
                # FastAPI WebSocket
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(connection.websocket.send_json(final_message))
                else:
                    loop.run_until_complete(connection.websocket.send_json(final_message))
            else:
                # 标准 WebSocket
                connection.websocket.send(json.dumps(final_message))

            logger.debug(f"发送批量消息: task={task_id}, count={len(messages)}")

        except Exception as e:
            logger.error(f"发送 WebSocket 消息失败: {e}")
            # 移除失效连接
            self.unregister_websocket(task_id, connection.websocket)

    def register_websocket(self, task_id: str, websocket: Any):
        """注册 WebSocket 连接

        Args:
            task_id: 任务 ID
            websocket: WebSocket 连接对象
        """
        if task_id not in self.websocket_connections:
            self.websocket_connections[task_id] = WebSocketConnection(websocket=websocket)
        else:
            self.websocket_connections[task_id].websocket = websocket

        self.websocket_connections[task_id].subscribed_tasks.add(task_id)
        self.websocket_connections[task_id].last_ping = datetime.now()
        logger.info(f"WebSocket 已注册: task={task_id}")

    def unregister_websocket(self, task_id: str, websocket: Any):
        """注销 WebSocket 连接

        Args:
            task_id: 任务 ID
            websocket: WebSocket 连接对象
        """
        if task_id in self.websocket_connections:
            del self.websocket_connections[task_id]
            logger.info(f"WebSocket 已注销: task={task_id}")

    def complete_task(self, task_id: str, output_filename: str):
        """标记任务完成"""
        with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id].status = "completed"
                self.tasks[task_id].progress = 100
                self.tasks[task_id].completed_at = datetime.now()
                self.tasks[task_id].output_filename = output_filename
                self.tasks[task_id].updated_at = datetime.now()

        # 立即发送完成通知
        self._queue_status_message(task_id, "completed", output_filename=output_filename)

    def fail_task(self, task_id: str, error: str):
        """标记任务失败"""
        with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id].status = "failed"
                self.tasks[task_id].error_message = error
                self.tasks[task_id].updated_at = datetime.now()

        # 立即发送失败通知
        self._queue_status_message(task_id, "failed", error=error)

    def _queue_status_message(self, task_id: str, status: str, **kwargs):
        """排队状态消息"""
        message = {
            "type": "status",
            "task_id": task_id,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }

        with self._message_lock:
            self._pending_messages[task_id].append(message)

        # 状态变化立即刷新
        self._flush_pending_messages()

    def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """清理过期任务

        Args:
            max_age_hours: 最大任务保留时间（小时）

        Returns:
            清理的任务数量
        """
        cleaned = 0
        now = datetime.now()

        with self._lock:
            tasks_to_remove = []
            for task_id, task in self.tasks.items():
                if task.completed_at:
                    age_hours = (now - task.completed_at).total_seconds() / 3600
                else:
                    age_hours = (now - task.created_at).total_seconds() / 3600

                if age_hours > max_age_hours:
                    tasks_to_remove.append(task_id)

            for task_id in tasks_to_remove:
                del self.tasks[task_id]
                if task_id in self._pending_messages:
                    del self._pending_messages[task_id]
                cleaned += 1

        if cleaned > 0:
            logger.info(f"清理了 {cleaned} 个过期任务")

        return cleaned

    def get_stats(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        total = len(self.tasks)
        pending = sum(1 for t in self.tasks.values() if t.status == "pending")
        running = sum(1 for t in self.tasks.values() if t.status == "running")
        completed = sum(1 for t in self.tasks.values() if t.status == "completed")
        failed = sum(1 for t in self.tasks.values() if t.status == "failed")

        return {
            "total_tasks": total,
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
            "active_websockets": len(self.websocket_connections)
        }

    def shutdown(self):
        """关闭任务管理器"""
        self._running = False
        # 刷新剩余消息
        self._flush_pending_messages()
        logger.info("任务管理器已关闭")


# 单例获取函数
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """获取任务管理器单例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager
