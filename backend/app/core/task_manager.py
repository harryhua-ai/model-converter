"""
任务管理器（单例）
"""
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict

from app.models.schemas import ConversionTask, ConversionConfig

logger = logging.getLogger(__name__)


class TaskManager:
    """任务管理器（单例）"""

    _instance: Optional['TaskManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.tasks: Dict[str, ConversionTask] = {}
        self.websocket_connections: Dict[str, list] = {}

    def create_task(self, config: ConversionConfig) -> str:
        """创建新任务"""
        task_id = str(uuid.uuid4())
        now = datetime.now()

        task = ConversionTask(
            task_id=task_id,
            status="pending",
            progress=0,
            current_step="",
            config=config,
            created_at=now,
            updated_at=now
        )

        self.tasks[task_id] = task
        return task_id

    def get_task(self, task_id: str) -> Optional[ConversionTask]:
        """获取任务状态"""
        return self.tasks.get(task_id)

    def update_progress(self, task_id: str, progress: int, step: str):
        """更新任务进度"""
        if task_id in self.tasks:
            self.tasks[task_id].progress = progress
            self.tasks[task_id].current_step = step
            self.tasks[task_id].updated_at = datetime.now()

            # WebSocket 推送
            self._broadcast_progress(task_id, progress, step)

    def _broadcast_progress(self, task_id: str, progress: int, step: str):
        """广播进度到 WebSocket 连接"""
        if task_id in self.websocket_connections:
            message = {
                "type": "progress",
                "task_id": task_id,
                "progress": progress,
                "step": step
            }
            logger.info(f"Broadcasting progress for task {task_id}: {progress}%")

    def complete_task(self, task_id: str, output_filename: str):
        """标记任务完成"""
        if task_id in self.tasks:
            self.tasks[task_id].status = "completed"
            self.tasks[task_id].progress = 100
            self.tasks[task_id].completed_at = datetime.now()
            self.tasks[task_id].output_filename = output_filename
            self.tasks[task_id].updated_at = datetime.now()

    def fail_task(self, task_id: str, error: str):
        """标记任务失败"""
        if task_id in self.tasks:
            self.tasks[task_id].status = "failed"
            self.tasks[task_id].error_message = error
            self.tasks[task_id].updated_at = datetime.now()


# 单例获取函数
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """获取任务管理器单例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager
