import heapq
from typing import List, Optional
from .task import Task

class TaskQueue:
    """任务优先级队列"""

    def __init__(self):
        # 使用 heapq 实现优先级队列
        # 存储格式: (priority, created_at, task_id)
        self._heap: List[tuple] = []
        self._task_map: dict[str, Task] = {}  # task_id -> task

    def enqueue(self, task: Task) -> None:
        """任务入队"""
        # 使用任务 ID 防止重复
        if task.task_id in self._task_map:
            raise ValueError(f"Task {task.task_id} already in queue")

        # 优先级 + 创建时间作为排序键
        # 数值越小优先级越高
        priority_key = (
            task.priority.value,
            task.created_at.timestamp(),
            task.task_id  # 防止 priority 和 created_at 相同时的比较
        )
        heapq.heappush(self._heap, priority_key)
        self._task_map[task.task_id] = task

    def dequeue(self) -> Optional[Task]:
        """任务出队"""
        if not self._heap:
            return None

        # 清理已删除的任务（lazy deletion）
        while self._heap:
            priority_key = self._heap[0]
            task_id = priority_key[2]
            if task_id in self._task_map:
                break
            heapq.heappop(self._heap)

        if not self._heap:
            return None

        priority_key = heapq.heappop(self._heap)
        task_id = priority_key[2]
        return self._task_map.pop(task_id, None)

    def peek(self) -> Optional[Task]:
        """查看队首任务（不移除）"""
        if not self._heap:
            return None

        # 清理已删除的任务
        while self._heap:
            priority_key = self._heap[0]
            task_id = priority_key[2]
            if task_id in self._task_map:
                return self._task_map.get(task_id)
            heapq.heappop(self._heap)

        return None

    def remove(self, task_id: str) -> bool:
        """移除指定任务"""
        if task_id not in self._task_map:
            return False

        # 标记为已删除（lazy deletion）
        # 在 dequeue 或 peek 时清理
        self._task_map.pop(task_id)
        return True

    def is_empty(self) -> bool:
        """检查队列是否为空"""
        # 清理已删除的任务
        while self._heap:
            priority_key = self._heap[0]
            task_id = priority_key[2]
            if task_id in self._task_map:
                break
            heapq.heappop(self._heap)

        return len(self._heap) == 0

    def __len__(self) -> int:
        """队列长度"""
        return len(self._task_map)
