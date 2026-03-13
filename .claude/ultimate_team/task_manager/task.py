from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import List, Optional

class TaskStatus(IntEnum):
    """任务状态"""
    PENDING = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    FAILED = 3
    BLOCKED = 4

class TaskPriority(IntEnum):
    """任务优先级（数值越小优先级越高）"""
    URGENT = 1   # 紧急
    HIGH = 2     # 高
    MEDIUM = 3   # 中
    LOW = 4      # 低

@dataclass
class Task:
    """任务数据模型"""
    task_id: str
    subject: str
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    owner: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    def transition_to(self, new_status: TaskStatus) -> None:
        """转换到新状态"""
        if not self._is_valid_transition(self.status, new_status):
            raise ValueError(f"Invalid state transition: {self.status} -> {new_status}")

        self.status = new_status

        if new_status == TaskStatus.IN_PROGRESS and self.started_at is None:
            self.started_at = datetime.now()
        elif new_status == TaskStatus.COMPLETED:
            self.completed_at = datetime.now()

    def add_dependency(self, task_id: str) -> None:
        """添加依赖任务"""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)

    def is_blocked_by(self, all_tasks: List['Task']) -> bool:
        """检查是否被依赖任务阻塞"""
        for dep_id in self.dependencies:
            for task in all_tasks:
                if task.task_id == dep_id:
                    if task.status != TaskStatus.COMPLETED:
                        return True
        return False

    @staticmethod
    def _is_valid_transition(old_status: TaskStatus, new_status: TaskStatus) -> bool:
        """验证状态转换是否有效"""
        valid_transitions = {
            TaskStatus.PENDING: [TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED],
            TaskStatus.IN_PROGRESS: [TaskStatus.COMPLETED, TaskStatus.FAILED],
            TaskStatus.BLOCKED: [TaskStatus.PENDING, TaskStatus.IN_PROGRESS],
            TaskStatus.FAILED: [TaskStatus.PENDING, TaskStatus.IN_PROGRESS],
            TaskStatus.COMPLETED: []  # 终态
        }
        return new_status in valid_transitions.get(old_status, [])
