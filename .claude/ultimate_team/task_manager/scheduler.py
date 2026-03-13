# .claude/ultimate_team/task_manager/scheduler.py
import asyncio
from typing import Callable, Awaitable, List
from .task import Task, TaskStatus
from .queue import TaskQueue
from .dependency_resolver import DependencyResolver

class TaskScheduler:
    """异步任务调度器"""

    def __init__(self, max_concurrent: int = 3):
        self.queue = TaskQueue()
        self.resolver = DependencyResolver()
        self.max_concurrent = max_concurrent
        self._running_tasks: set[str] = set()
        self._all_tasks: List[Task] = []
        self._handler: Callable[[Task], Awaitable[None]] | None = None
        self._processing_lock = asyncio.Lock()
        self._pending_tasks = 0

    async def schedule(
        self,
        task: Task,
        handler: Callable[[Task], Awaitable[None]]
    ) -> None:
        """调度任务执行"""
        self._all_tasks.append(task)
        self.queue.enqueue(task)
        self._handler = handler
        self._pending_tasks += 1

        # 尝试启动处理（如果已经有其他协程在处理，会直接返回）
        asyncio.create_task(self._try_process_queue())

    async def _try_process_queue(self) -> None:
        """尝试处理任务队列"""
        # 获取锁，确保同时只有一个协程在处理
        async with self._processing_lock:
            await self._process_queue()

    async def _process_queue(self) -> None:
        """处理任务队列"""
        while not self.queue.is_empty():
            # 检查并发限制
            if len(self._running_tasks) >= self.max_concurrent:
                await asyncio.sleep(0.01)
                continue

            # 查找可执行任务
            executable = self.resolver.find_executable_tasks(self._all_tasks)

            # 从队列中取出可执行任务
            task_to_run = None
            for task in executable:
                if task.task_id in self._running_tasks:
                    continue  # 已在运行

                # 从队列中查找
                if self.queue.peek() and self.queue.peek().task_id == task.task_id:
                    task_to_run = self.queue.dequeue()
                    break

            if task_to_run is None:
                break  # 没有可执行任务

            # 执行任务
            self._running_tasks.add(task_to_run.task_id)

            # 创建任务但不等待
            asyncio.create_task(self._execute_task(task_to_run))

    async def _execute_task(self, task: Task) -> None:
        """执行单个任务"""
        try:
            task.transition_to(TaskStatus.IN_PROGRESS)
            await self._handler(task)
        except Exception as e:
            task.error = str(e)
            task.transition_to(TaskStatus.FAILED)
        finally:
            self._running_tasks.discard(task.task_id)
            self._pending_tasks -= 1

            # 如果还有任务，继续处理
            if not self.queue.is_empty() or self._pending_tasks > 0:
                await self._try_process_queue()

    async def wait_until_complete(self) -> None:
        """等待所有任务完成"""
        while self._running_tasks or not self.queue.is_empty():
            await asyncio.sleep(0.1)

    def get_all_tasks(self) -> List[Task]:
        """获取所有任务"""
        return self._all_tasks.copy()
