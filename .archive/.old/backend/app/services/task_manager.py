"""
任务管理服务（简化版）
管理转换任务的创建、查询、更新和删除
使用内存存储和异步队列，无需 Redis
"""
import os
import shutil
import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator
from pathlib import Path

import structlog

from app.models.schemas import ConversionTask, ConversionConfig, TaskStatus
from app.core.config import settings

logger = structlog.get_logger(__name__)


class TaskManager:
    """任务管理器（内存存储版本）"""

    def __init__(self):
        """初始化任务管理器"""
        # 内存存储
        self._tasks: dict[str, ConversionTask] = {}
        # 订阅者管理 {task_id: [queues]}
        self._subscribers: dict[str, list[asyncio.Queue]] = {}
        # 持久化文件路径
        self._persist_file = Path(settings.TEMP_DIR) / "tasks.json"

        # 确保必要的目录存在
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        os.makedirs(settings.TEMP_DIR, exist_ok=True)
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

        # 从持久化文件加载任务
        self._load_from_disk()

    def _save_to_disk(self) -> None:
        """保存任务到磁盘（用于重启恢复）"""
        try:
            tasks_data = {
                task_id: task.model_dump()
                for task_id, task in self._tasks.items()
            }
            self._persist_file.write_text(json.dumps(tasks_data, indent=2), encoding='utf-8')
        except Exception as e:
            logger.warning("保存任务到磁盘失败", error=str(e))

    def _load_from_disk(self) -> None:
        """从磁盘加载任务"""
        try:
            if self._persist_file.exists():
                tasks_data = json.loads(self._persist_file.read_text(encoding='utf-8'))
                for task_id, task_dict in tasks_data.items():
                    self._tasks[task_id] = ConversionTask(**task_dict)
                logger.info("从磁盘恢复任务", count=len(self._tasks))
        except Exception as e:
            logger.warning("从磁盘加载任务失败", error=str(e))

    async def create_task(
        self,
        task_id: str,
        config: ConversionConfig,
        filename: str,
    ) -> ConversionTask:
        """
        创建新任务

        Args:
            task_id: 任务 ID
            config: 转换配置
            filename: 原始文件名

        Returns:
            ConversionTask: 创建的任务
        """
        now = datetime.now().isoformat()

        task = ConversionTask(
            task_id=task_id,
            status=TaskStatus.PENDING,
            progress=0,
            current_step="Waiting for processing",
            config=config,
            created_at=now,
            updated_at=now,
        )

        # 保存到内存
        self._tasks[task_id] = task
        self._save_to_disk()

        logger.info("任务创建", task_id=task_id, filename=filename)

        return task

    async def get_task(self, task_id: str) -> ConversionTask | None:
        """
        获取任务详情

        Args:
            task_id: 任务 ID

        Returns:
            ConversionTask | None: 任务详情
        """
        return self._tasks.get(task_id)

    async def list_tasks(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ConversionTask]:
        """
        获取任务列表

        Args:
            status: 过滤状态
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            list[ConversionTask]: 任务列表
        """
        tasks = list(self._tasks.values())

        # 按状态过滤
        if status:
            tasks = [t for t in tasks if t.status.value == status]

        # 按创建时间排序（最新的在前）
        tasks = sorted(tasks, key=lambda t: t.created_at, reverse=True)

        # 分页
        return tasks[offset : offset + limit]

    async def count_tasks(self, status: str | None = None) -> int:
        """
        统计任务数量

        Args:
            status: 过滤状态

        Returns:
            int: 任务数量
        """
        tasks = list(self._tasks.values())

        if status:
            return sum(1 for t in tasks if t.status.value == status)
        return len(tasks)

    async def update_task(
        self,
        task_id: str,
        status: TaskStatus | None = None,
        progress: int | None = None,
        current_step: str | None = None,
        error_message: str | None = None,
        output_filename: str | None = None,
    ) -> ConversionTask | None:
        """
        更新任务状态

        Args:
            task_id: 任务 ID
            status: 新状态
            progress: 进度百分比
            current_step: 当前步骤
            error_message: 错误消息
            output_filename: 输出文件名

        Returns:
            ConversionTask | None: 更新后的任务
        """
        task = self._tasks.get(task_id)
        if not task:
            return None

        # 更新字段
        if status:
            task.status = status
        if progress is not None:
            task.progress = progress
        if current_step:
            task.current_step = current_step
        if error_message:
            task.error_message = error_message
        if output_filename:
            task.output_filename = output_filename

        task.updated_at = datetime.now().isoformat()

        logger.info(
            "任务更新",
            task_id=task_id,
            status=task.status.value,
            progress=task.progress,
        )

        # 保存到内存和磁盘
        self._save_to_disk()

        # 通知订阅者
        await self._notify_subscribers(task_id, task.model_dump())

        return task

    async def cancel_task(self, task_id: str) -> ConversionTask | None:
        """
        取消任务

        Args:
            task_id: 任务 ID

        Returns:
            ConversionTask | None: 更新后的任务
        """
        task = self._tasks.get(task_id)
        if not task:
            return None

        # 只有 pending 或 processing 状态的任务可以取消
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            logger.warning("任务无法取消", task_id=task_id, status=task.status.value)
            return task

        # 更新为取消状态
        task.status = TaskStatus.CANCELLED
        task.current_step = "Task cancelled"
        task.updated_at = datetime.now().isoformat()

        # 保存到磁盘
        self._save_to_disk()

        logger.info("任务取消", task_id=task_id)

        # 通知订阅者
        await self._notify_subscribers(task_id, task.model_dump())

        return task

    async def delete_task(self, task_id: str) -> bool:
        """
        删除任务和相关文件

        Args:
            task_id: 任务 ID

        Returns:
            bool: 是否删除成功
        """
        task = self._tasks.get(task_id)
        if not task:
            return False

        # 删除相关文件
        work_dir = os.path.join(settings.TEMP_DIR, task_id)
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)

        # 删除上传的文件
        import glob as glob_module
        upload_pattern = os.path.join(settings.UPLOAD_DIR, f"{task_id}_*")
        for f in glob_module.glob(upload_pattern):
            os.remove(f)

        # 从内存删除
        del self._tasks[task_id]

        # 保存到磁盘
        self._save_to_disk()

        logger.info("任务删除", task_id=task_id)
        return True

    async def subscribe_task_updates(self, task_id: str) -> AsyncGenerator[dict, None]:
        """
        订阅任务更新（WebSocket 使用）

        Args:
            task_id: 任务 ID

        Yields:
            dict: 任务更新数据
        """
        queue: asyncio.Queue = asyncio.Queue()

        # 添加订阅者
        if task_id not in self._subscribers:
            self._subscribers[task_id] = []
        self._subscribers[task_id].append(queue)

        try:
            # 立即发送当前状态
            task = self._tasks.get(task_id)
            if task:
                yield task.model_dump()

            # 等待更新
            while True:
                update = await queue.get()
                yield update

                # 如果任务完成或失败，取消订阅
                if update.get("status") in ["completed", "failed", "cancelled"]:
                    break
        finally:
            # 移除订阅者
            if task_id in self._subscribers and queue in self._subscribers[task_id]:
                self._subscribers[task_id].remove(queue)

    async def _notify_subscribers(self, task_id: str, update: dict) -> None:
        """
        通知订阅者任务更新

        Args:
            task_id: 任务 ID
            update: 更新数据
        """
        if task_id not in self._subscribers:
            return

        for queue in self._subscribers[task_id]:
            await queue.put(update)

    def close(self):
        """关闭任务管理器"""
        # 内存版本无需关闭连接
        pass


# 全局单例
_task_manager: TaskManager | None = None


def get_task_manager() -> TaskManager:
    """获取任务管理器单例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager
