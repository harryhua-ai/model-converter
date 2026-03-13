# .claude/ultimate-team/task_manager/dependency_resolver.py
from typing import List
from collections import defaultdict, deque
from .task import Task, TaskStatus

class DependencyResolver:
    """任务依赖解析器"""

    def resolve(self, tasks: List[Task]) -> List[Task]:
        """
        解析任务依赖，返回拓扑排序后的任务列表

        使用 Kahn 算法进行拓扑排序
        """
        # 构建依赖图
        in_degree = defaultdict(int)  # 任务 ID -> 入度
        adj_list = defaultdict(list)  # 任务 ID -> 依赖它的任务列表

        task_map = {task.task_id: task for task in tasks}

        # 初始化
        for task in tasks:
            in_degree[task.task_id] = len(task.dependencies)

            for dep_id in task.dependencies:
                adj_list[dep_id].append(task.task_id)

        # 找出入度为 0 的节点
        queue = deque([task_id for task_id in in_degree if in_degree[task_id] == 0])
        sorted_tasks = []

        while queue:
            task_id = queue.popleft()
            sorted_tasks.append(task_map[task_id])

            # 减少依赖此任务的其他任务的入度
            for dependent_id in adj_list[task_id]:
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)

        # 检查循环依赖
        if len(sorted_tasks) != len(tasks):
            raise ValueError("Circular dependency detected in tasks")

        return sorted_tasks

    def find_executable_tasks(self, tasks: List[Task]) -> List[Task]:
        """
        查找当前可执行的任务

        可执行条件：
        1. 状态为 PENDING
        2. 所有依赖任务已完成
        """
        executable = []

        for task in tasks:
            if task.status != TaskStatus.PENDING:
                continue

            if task.is_blocked_by(tasks):
                continue

            executable.append(task)

        return executable
