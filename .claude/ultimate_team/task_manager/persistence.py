# .claude/ultimate_team/task_manager/persistence.py
import json
from pathlib import Path
from typing import List
from datetime import datetime
from .task import Task, TaskStatus, TaskPriority

class TaskPersistence:
    """任务持久化管理器"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def save(self, tasks: List[Task]) -> None:
        """保存任务到 JSON 文件"""
        data = [self._task_to_dict(task) for task in tasks]

        # 确保目录存在
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self) -> List[Task]:
        """从 JSON 文件加载任务"""
        if not self.file_path.exists():
            return []

        with open(self.file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return [self._dict_to_task(item) for item in data]

    def _task_to_dict(self, task: Task) -> dict:
        """任务转换为字典"""
        return {
            "task_id": task.task_id,
            "subject": task.subject,
            "description": task.description,
            "priority": task.priority.value,
            "status": task.status.value,
            "dependencies": task.dependencies,
            "owner": task.owner,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error": task.error
        }

    def _dict_to_task(self, data: dict) -> Task:
        """字典转换为任务"""
        return Task(
            task_id=data["task_id"],
            subject=data["subject"],
            description=data.get("description", ""),
            priority=TaskPriority(data["priority"]),
            status=TaskStatus(data["status"]),
            dependencies=data.get("dependencies", []),
            owner=data.get("owner"),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            error=data.get("error")
        )
