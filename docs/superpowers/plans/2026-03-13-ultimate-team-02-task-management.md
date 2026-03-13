# Ultimate Team - Part 2: 任务管理系统实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建完整的任务管理系统，支持优先级队列、依赖跟踪、并行执行和状态持久化

**Architecture:** 基于队列的任务调度器，使用优先级堆管理任务执行顺序，通过 JSON 文件持久化任务状态，支持依赖解析和并行执行

**Tech Stack:** Python 3.11+, asyncio (异步), heapq (优先级队列), JSON (持久化), dataclasses (数据模型)

---

## 文件结构

```
.claude/
├── ultimate-team/
│   ├── task_manager/
│   │   ├── __init__.py
│   │   ├── task.py                  # 任务数据模型
│   │   ├── queue.py                 # 优先级队列
│   │   ├── scheduler.py             # 任务调度器
│   │   ├── persistence.py           # JSON 持久化
│   │   └── dependency_resolver.py   # 依赖解析器
│   └── tasks/
│       ├── __init__.py
│       └── summary_generator.py     # Markdown 摘要生成器
└── bin/
    └── tasks                         # CLI 工具
tests/
    ├── test_task.py
    ├── test_queue.py
    ├── test_scheduler.py
    ├── test_persistence.py
    └── test_dependency_resolver.py
```

---

## Chunk 1: 任务数据模型

### Task 1: 创建任务数据模型

**Files:**
- Create: `.claude/ultimate-team/task_manager/task.py`
- Create: `tests/test_task.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_task.py
import pytest
from ultimate_team.task_manager.task import Task, TaskStatus, TaskPriority

def test_task_creation():
    """测试任务创建"""
    task = Task(
        task_id="TASK-001",
        subject="实现用户登录",
        description="使用 JWT 实现用户认证",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING
    )

    assert task.task_id == "TASK-001"
    assert task.subject == "实现用户登录"
    assert task.priority == TaskPriority.HIGH
    assert task.status == TaskStatus.PENDING
    assert task.created_at is not None

def test_task_status_transition():
    """测试状态转换"""
    task = Task(
        task_id="TASK-002",
        subject="修复 Bug",
        priority=TaskPriority.URGENT
    )

    # PENDING -> IN_PROGRESS
    task.transition_to(TaskStatus.IN_PROGRESS)
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.started_at is not None

    # IN_PROGRESS -> COMPLETED
    task.transition_to(TaskStatus.COMPLETED)
    assert task.status == TaskStatus.COMPLETED
    assert task.completed_at is not None

def test_task_add_dependency():
    """测试添加依赖"""
    task1 = Task(
        task_id="TASK-001",
        subject="第一个任务",
        priority=TaskPriority.MEDIUM
    )

    task2 = Task(
        task_id="TASK-002",
        subject="依赖任务",
        priority=TaskPriority.MEDIUM
    )

    task2.add_dependency("TASK-001")
    assert "TASK-001" in task2.dependencies
    assert task2.is_blocked_by([task1])

def test_task_priority_comparison():
    """测试优先级比较"""
    urgent_task = Task(
        task_id="TASK-001",
        subject="紧急任务",
        priority=TaskPriority.URGENT
    )

    high_task = Task(
        task_id="TASK-002",
        subject="高优先级",
        priority=TaskPriority.HIGH
    )

    # URGENT (1) < HIGH (2) - 数值越小优先级越高
    assert urgent_task.priority < high_task.priority
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_task.py -v`
Expected: FAIL with "TaskStatus not defined"

- [ ] **Step 3: Write minimal implementation**

```python
# .claude/ultimate-team/task_manager/task.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_task.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_task.py .claude/ultimate-team/task_manager/task.py
git commit -m "feat: add task data model with status transitions"
```

---

## Chunk 2: 优先级队列

### Task 2: 实现优先级队列

**Files:**
- Create: `.claude/ultimate-team/task_manager/queue.py`
- Create: `tests/test_queue.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_queue.py
import pytest
from ultimate_team.task_manager.task import Task, TaskPriority, TaskStatus
from ultimate_team.task_manager.queue import TaskQueue

def test_enqueue_dequeue():
    """测试入队和出队"""
    queue = TaskQueue()

    task1 = Task("TASK-001", "低优先级", priority=TaskPriority.LOW)
    task2 = Task("TASK-002", "紧急任务", priority=TaskPriority.URGENT)
    task3 = Task("TASK-003", "高优先级", priority=TaskPriority.HIGH)

    queue.enqueue(task1)
    queue.enqueue(task2)
    queue.enqueue(task3)

    # 应该先出队紧急任务
    first = queue.dequeue()
    assert first.task_id == "TASK-002"

    second = queue.dequeue()
    assert second.task_id == "TASK-003"

    third = queue.dequeue()
    assert third.task_id == "TASK-001"

def test_empty_queue():
    """测试空队列"""
    queue = TaskQueue()
    assert queue.is_empty()
    assert queue.dequeue() is None

def test_peek():
    """测试查看队首"""
    queue = TaskQueue()

    task1 = Task("TASK-001", "第一个", priority=TaskPriority.HIGH)
    task2 = Task("TASK-002", "第二个", priority=TaskPriority.URGENT)

    queue.enqueue(task1)
    queue.enqueue(task2)

    # peek 不移除元素
    assert queue.peek().task_id == "TASK-002"
    assert queue.peek().task_id == "TASK-002"

    # dequeue 移除元素
    assert queue.dequeue().task_id == "TASK-002"
    assert queue.peek().task_id == "TASK-001"

def test_remove_task():
    """测试移除任务"""
    queue = TaskQueue()

    task1 = Task("TASK-001", "任务1", priority=TaskPriority.HIGH)
    task2 = Task("TASK-002", "任务2", priority=TaskPriority.MEDIUM)

    queue.enqueue(task1)
    queue.enqueue(task2)

    queue.remove("TASK-001")

    assert queue.dequeue().task_id == "TASK-002"
    assert queue.is_empty()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_queue.py -v`
Expected: FAIL with "TaskQueue not defined"

- [ ] **Step 3: Write minimal implementation**

```python
# .claude/ultimate-team/task_manager/queue.py
import heapq
from typing import List, Optional
from .task import Task

class TaskQueue:
    """任务优先级队列"""

    def __init__(self):
        # 使用 heapq 实现优先级队列
        # 存储格式: (priority, created_at, task)
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

        priority_key = heapq.heappop(self._heap)
        task_id = priority_key[2]
        return self._task_map.pop(task_id, None)

    def peek(self) -> Optional[Task]:
        """查看队首任务（不移除）"""
        if not self._heap:
            return None

        priority_key = self._heap[0]
        task_id = priority_key[2]
        return self._task_map.get(task_id)

    def remove(self, task_id: str) -> bool:
        """移除指定任务"""
        if task_id not in self._task_map:
            return False

        # 标记为已删除（lazy deletion）
        # 在 dequeue 时检查
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_queue.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_queue.py .claude/ultimate-team/task_manager/queue.py
git commit -m "feat: add priority task queue"
```

---

### Task 3: 实现依赖解析器

**Files:**
- Create: `.claude/ultimate-team/task_manager/dependency_resolver.py`
- Create: `tests/test_dependency_resolver.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_dependency_resolver.py
import pytest
from ultimate_team.task_manager.task import Task, TaskPriority, TaskStatus
from ultimate_team.task_manager.dependency_resolver import DependencyResolver

def test_resolve_simple_dependency():
    """测试简单依赖解析"""
    task1 = Task("TASK-001", "基础任务", priority=TaskPriority.HIGH)
    task2 = Task("TASK-002", "依赖任务", priority=TaskPriority.HIGH)
    task2.add_dependency("TASK-001")

    resolver = DependencyResolver()
    resolved = resolver.resolve([task1, task2])

    # task1 应该在 task2 之前
    assert resolved[0].task_id == "TASK-001"
    assert resolved[1].task_id == "TASK-002"

def test_resolve_complex_dependencies():
    """测试复杂依赖"""
    task1 = Task("TASK-001", "基础", priority=TaskPriority.MEDIUM)
    task2 = Task("TASK-002", "中间", priority=TaskPriority.MEDIUM)
    task3 = Task("TASK-003", "顶层", priority=TaskPriority.MEDIUM)

    # task3 依赖 task1 和 task2
    task3.add_dependency("TASK-001")
    task3.add_dependency("TASK-002")

    # task2 依赖 task1
    task2.add_dependency("TASK-001")

    resolver = DependencyResolver()
    resolved = resolver.resolve([task1, task2, task3])

    # 执行顺序: task1 -> task2 -> task3
    assert resolved[0].task_id == "TASK-001"
    assert resolved[1].task_id == "TASK-002"
    assert resolved[2].task_id == "TASK-003"

def test_circular_dependency_detection():
    """测试循环依赖检测"""
    task1 = Task("TASK-001", "任务1", priority=TaskPriority.MEDIUM)
    task2 = Task("TASK-002", "任务2", priority=TaskPriority.MEDIUM)
    task3 = Task("TASK-003", "任务3", priority=TaskPriority.MEDIUM)

    # 创建循环: task1 -> task2 -> task3 -> task1
    task1.add_dependency("TASK-003")
    task2.add_dependency("TASK-001")
    task3.add_dependency("TASK-002")

    resolver = DependencyResolver()

    with pytest.raises(ValueError, match="Circular dependency"):
        resolver.resolve([task1, task2, task3])

def test_find_executable_tasks():
    """测试查找可执行任务"""
    task1 = Task("TASK-001", "已完成", priority=TaskPriority.MEDIUM)
    task1.transition_to(TaskStatus.COMPLETED)

    task2 = Task("TASK-002", "阻塞中", priority=TaskPriority.MEDIUM)
    task2.add_dependency("TASK-003")

    task3 = Task("TASK-003", "可执行", priority=TaskPriority.MEDIUM)

    tasks = [task1, task2, task3]

    resolver = DependencyResolver()
    executable = resolver.find_executable_tasks(tasks)

    # task1 已完成，task2 被阻塞，只有 task3 可执行
    assert len(executable) == 1
    assert executable[0].task_id == "TASK-003"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_dependency_resolver.py -v`
Expected: FAIL with "DependencyResolver not defined"

- [ ] **Step 3: Write minimal implementation**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_dependency_resolver.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_dependency_resolver.py .claude/ultimate-team/task_manager/dependency_resolver.py
git commit -m "feat: add dependency resolver with topological sort"
```

---

## Chunk 3: 任务调度器

### Task 4: 实现任务调度器

**Files:**
- Create: `.claude/ultimate-team/task_manager/scheduler.py`
- Create: `tests/test_scheduler.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scheduler.py
import pytest
import asyncio
from ultimate_team.task_manager.task import Task, TaskPriority, TaskStatus
from ultimate_team.task_manager.scheduler import TaskScheduler
from ultimate_team.task_manager.queue import TaskQueue

@pytest.mark.asyncio
async def test_schedule_single_task():
    """测试调度单个任务"""
    scheduler = TaskScheduler()

    task = Task("TASK-001", "测试任务", priority=TaskPriority.HIGH)

    executed = []

    async def mock_handler(task):
        executed.append(task.task_id)
        task.transition_to(TaskStatus.COMPLETED)

    await scheduler.schedule(task, mock_handler)

    assert "TASK-001" in executed
    assert task.status == TaskStatus.COMPLETED

@pytest.mark.asyncio
async def test_schedule_with_priority():
    """测试按优先级调度"""
    scheduler = TaskScheduler()

    low_task = Task("TASK-001", "低优先级", priority=TaskPriority.LOW)
    urgent_task = Task("TASK-002", "紧急", priority=TaskPriority.URGENT)
    high_task = Task("TASK-003", "高优先级", priority=TaskPriority.HIGH)

    executed_order = []

    async def mock_handler(task):
        executed_order.append(task.task_id)
        await asyncio.sleep(0.01)  # 模拟执行时间
        task.transition_to(TaskStatus.COMPLETED)

    # 并发提交
    await asyncio.gather(
        scheduler.schedule(low_task, mock_handler),
        scheduler.schedule(urgent_task, mock_handler),
        scheduler.schedule(high_task, mock_handler)
    )

    # 紧急任务应该先执行
    assert executed_order[0] == "TASK-002"

@pytest.mark.asyncio
async def test_schedule_with_dependencies():
    """测试带依赖的任务调度"""
    scheduler = TaskScheduler()

    task1 = Task("TASK-001", "基础", priority=TaskPriority.MEDIUM)
    task2 = Task("TASK-002", "依赖", priority=TaskPriority.MEDIUM)
    task2.add_dependency("TASK-001")

    executed = []

    async def mock_handler(task):
        executed.append(task.task_id)
        task.transition_to(TaskStatus.COMPLETED)

    # 并发提交
    await asyncio.gather(
        scheduler.schedule(task1, mock_handler),
        scheduler.schedule(task2, mock_handler)
    )

    # task1 应该在 task2 之前执行
    assert executed == ["TASK-001", "TASK-002"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scheduler.py -v`
Expected: FAIL with "TaskScheduler not defined"

- [ ] **Step 3: Write minimal implementation**

```python
# .claude/ultimate-team/task_manager/scheduler.py
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

    async def schedule(
        self,
        task: Task,
        handler: Callable[[Task], Awaitable[None]]
    ) -> None:
        """调度任务执行"""
        self._all_tasks.append(task)
        self.queue.enqueue(task)

        await self._process_queue(handler)

    async def _process_queue(
        self,
        handler: Callable[[Task], Awaitable[None]]
    ) -> None:
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
                if task.task_id in [t.task_id for t in self._running_tasks]:
                    continue  # 已在运行

                # 从队列中查找
                if self.queue.peek() and self.queue.peek().task_id == task.task_id:
                    task_to_run = self.queue.dequeue()
                    break

            if task_to_run is None:
                break  # 没有可执行任务

            # 执行任务
            self._running_tasks.add(task_to_run.task_id)

            try:
                task_to_run.transition_to(TaskStatus.IN_PROGRESS)
                await handler(task_to_run)
            except Exception as e:
                task_to_run.error = str(e)
                task_to_run.transition_to(TaskStatus.FAILED)
            finally:
                self._running_tasks.discard(task_to_run.task_id)

    async def wait_until_complete(self) -> None:
        """等待所有任务完成"""
        while self._running_tasks or not self.queue.is_empty():
            await asyncio.sleep(0.1)

    def get_all_tasks(self) -> List[Task]:
        """获取所有任务"""
        return self._all_tasks.copy()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scheduler.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_scheduler.py .claude/ultimate-team/task_manager/scheduler.py
git commit -m "feat: add async task scheduler with dependency resolution"
```

---

## Chunk 4: 持久化和可视化

### Task 5: 实现 JSON 持久化

**Files:**
- Create: `.claude/ultimate-team/task_manager/persistence.py`
- Create: `tests/test_persistence.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_persistence.py
import pytest
import json
from pathlib import Path
from ultimate_team.task_manager.task import Task, TaskPriority, TaskStatus
from ultimate_team.task_manager.persistence import TaskPersistence

def test_save_and_load_tasks():
    """测试保存和加载任务"""
    tasks = [
        Task("TASK-001", "任务1", priority=TaskPriority.HIGH),
        Task("TASK-002", "任务2", priority=TaskPriority.URGENT)
    ]

    persistence = TaskPersistence("/tmp/test_tasks.json")

    # 保存
    persistence.save(tasks)

    # 加载
    loaded = persistence.load()

    assert len(loaded) == 2
    assert loaded[0].task_id == "TASK-001"
    assert loaded[1].task_id == "TASK-002"
    assert loaded[0].priority == TaskPriority.HIGH

def test_load_empty_file():
    """测试加载空文件"""
    persistence = TaskPersistence("/tmp/empty_tasks.json")

    # 不存在的文件应该返回空列表
    loaded = persistence.load()
    assert loaded == []

def test_save_updates_file():
    """测试保存更新文件"""
    persistence = TaskPersistence("/tmp/update_tasks.json")

    # 第一次保存
    tasks1 = [Task("TASK-001", "原始任务")]
    persistence.save(tasks1)

    # 第二次保存
    tasks2 = [
        Task("TASK-001", "更新任务"),
        Task("TASK-002", "新任务")
    ]
    persistence.save(tasks2)

    # 验证最终状态
    loaded = persistence.load()
    assert len(loaded) == 2
    assert loaded[0].subject == "更新任务"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_persistence.py -v`
Expected: FAIL with "TaskPersistence not defined"

- [ ] **Step 3: Write minimal implementation**

```python
# .claude/ultimate-team/task_manager/persistence.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_persistence.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_persistence.py .claude/ultimate-team/task_manager/persistence.py
git commit -m "feat: add JSON persistence for tasks"
```

---

### Task 6: 创建 Markdown 摘要生成器

**Files:**
- Create: `.claude/ultimate-team/tasks/summary_generator.py`
- Create: `.claude/ultimate-team/tasks/__init__.py`
- Create: `tests/test_summary_generator.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_summary_generator.py
import pytest
from datetime import datetime
from ultimate_team.task_manager.task import Task, TaskPriority, TaskStatus
from ultimate_team.tasks.summary_generator import SummaryGenerator

def test_generate_summary():
    """测试生成摘要"""
    tasks = [
        Task("TASK-001", "已完成", priority=TaskPriority.HIGH, status=TaskStatus.COMPLETED),
        Task("TASK-002", "进行中", priority=TaskPriority.MEDIUM, status=TaskStatus.IN_PROGRESS),
        Task("TASK-003", "待处理", priority=TaskPriority.LOW, status=TaskStatus.PENDING)
    ]

    generator = SummaryGenerator()
    summary = generator.generate(tasks)

    assert "# 任务摘要" in summary
    assert "已完成" in summary
    assert "进行中" in summary
    assert "待处理" in summary
    assert "TASK-001" in summary
    assert "TASK-002" in summary

def test_generate_statistics():
    """测试生成统计信息"""
    tasks = [
        Task("TASK-001", "任务1", status=TaskStatus.COMPLETED),
        Task("TASK-002", "任务2", status=TaskStatus.IN_PROGRESS),
        Task("TASK-003", "任务3", status=TaskStatus.PENDING),
        Task("TASK-004", "任务4", status=TaskStatus.FAILED)
    ]

    generator = SummaryGenerator()
    stats = generator.generate_statistics(tasks)

    assert stats["total"] == 4
    assert stats["completed"] == 1
    assert stats["in_progress"] == 1
    assert stats["pending"] == 1
    assert stats["failed"] == 1

def test_save_summary_to_file():
    """测试保存摘要到文件"""
    import tempfile
    import os

    tasks = [
        Task("TASK-001", "测试任务", priority=TaskPriority.HIGH)
    ]

    generator = SummaryGenerator()

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "summary.md")
        generator.save(tasks, file_path)

        assert os.path.exists(file_path)

        with open(file_path, 'r') as f:
            content = f.read()
            assert "# 任务摘要" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_summary_generator.py -v`
Expected: FAIL with "SummaryGenerator not defined"

- [ ] **Step 3: Write minimal implementation**

```python
# .claude/ultimate-team/tasks/summary_generator.py
from typing import List, Dict
from datetime import datetime
from ..task_manager.task import Task, TaskStatus

class SummaryGenerator:
    """Markdown 摘要生成器"""

    def generate(self, tasks: List[Task]) -> str:
        """生成任务摘要"""
        stats = self.generate_statistics(tasks)

        lines = [
            "# 任务摘要",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 统计概览",
            "",
            f"- **总任务数**: {stats['total']}",
            f"- **已完成**: {stats['completed']}",
            f"- **进行中**: {stats['in_progress']}",
            f"- **待处理**: {stats['pending']}",
            f"- **已失败**: {stats['failed']}",
            "",
            "## 任务列表",
            ""
        ]

        # 按状态分组
        grouped = self._group_by_status(tasks)

        for status, status_tasks in grouped.items():
            lines.append(f"### {self._status_name(status)}")
            lines.append("")

            if not status_tasks:
                lines.append("*无任务*")
                lines.append("")
                continue

            for task in status_tasks:
                lines.append(f"#### {task.task_id}: {task.subject}")
                lines.append("")
                if task.description:
                    lines.append(f"- **描述**: {task.description}")
                if task.owner:
                    lines.append(f"- **负责人**: {task.owner}")
                if task.dependencies:
                    lines.append(f"- **依赖**: {', '.join(task.dependencies)}")
                if task.error:
                    lines.append(f"- **错误**: {task.error}")
                lines.append("")

        return "\n".join(lines)

    def generate_statistics(self, tasks: List[Task]) -> Dict[str, int]:
        """生成统计信息"""
        return {
            "total": len(tasks),
            "completed": len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
            "in_progress": len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS]),
            "pending": len([t for t in tasks if t.status == TaskStatus.PENDING]),
            "failed": len([t for t in tasks if t.status == TaskStatus.FAILED]),
            "blocked": len([t for t in tasks if t.status == TaskStatus.BLOCKED])
        }

    def save(self, tasks: List[Task], file_path: str) -> None:
        """保存摘要到文件"""
        summary = self.generate(tasks)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(summary)

    def _group_by_status(self, tasks: List[Task]) -> Dict[TaskStatus, List[Task]]:
        """按状态分组"""
        grouped = {}
        for task in tasks:
            if task.status not in grouped:
                grouped[task.status] = []
            grouped[task.status].append(task)
        return grouped

    def _status_name(self, status: TaskStatus) -> str:
        """状态名称"""
        names = {
            TaskStatus.PENDING: "待处理",
            TaskStatus.IN_PROGRESS: "进行中",
            TaskStatus.COMPLETED: "已完成",
            TaskStatus.FAILED: "已失败",
            TaskStatus.BLOCKED: "已阻塞"
        }
        return names.get(status, str(status))
```

- [ ] **Step 4: Write __init__.py**

```python
# .claude/ultimate-team/tasks/__init__.py
from .summary_generator import SummaryGenerator

__all__ = ['SummaryGenerator']
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_summary_generator.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tests/test_summary_generator.py .claude/ultimate-team/tasks/ .claude/ultimate-team/tasks/__init__.py
git commit -m "feat: add markdown summary generator"
```

---

## Chunk 5: CLI 工具

### Task 7: 创建 CLI 工具

**Files:**
- Create: `.claude/bin/tasks`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cli.py
import pytest
import subprocess
import json
from ultimate_team.task_manager.task import Task, TaskPriority, TaskStatus
from ultimate_team.task_manager.persistence import TaskPersistence

def test_cli_list_command():
    """测试 tasks list 命令"""
    # 创建测试数据
    tasks = [
        Task("TASK-001", "测试任务", priority=TaskPriority.HIGH)
    ]

    persistence = TaskPersistence("/tmp/test_cli_tasks.json")
    persistence.save(tasks)

    # 运行 CLI
    result = subprocess.run(
        ["python", ".claude/bin/tasks", "list", "--file", "/tmp/test_cli_tasks.json"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "TASK-001" in result.stdout

def test_cli_show_command():
    """测试 tasks show 命令"""
    tasks = [
        Task("TASK-001", "详细任务", description="这是详细描述", priority=TaskPriority.URGENT)
    ]

    persistence = TaskPersistence("/tmp/test_cli_show.json")
    persistence.save(tasks)

    result = subprocess.run(
        ["python", ".claude/bin/tasks", "show", "TASK-001", "--file", "/tmp/test_cli_show.json"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "详细任务" in result.stdout
    assert "这是详细描述" in result.stdout

def test_cli_stats_command():
    """测试 tasks stats 命令"""
    tasks = [
        Task("TASK-001", "任务1", status=TaskStatus.COMPLETED),
        Task("TASK-002", "任务2", status=TaskStatus.IN_PROGRESS)
    ]

    persistence = TaskPersistence("/tmp/test_cli_stats.json")
    persistence.save(tasks)

    result = subprocess.run(
        ["python", ".claude/bin/tasks", "stats", "--file", "/tmp/test_cli_stats.json"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "总任务数: 2" in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL with "No such file or directory"

- [ ] **Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
# .claude/bin/tasks
import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from ultimate_team.task_manager.task import Task
from ultimate_team.task_manager.persistence import TaskPersistence
from ultimate_team.tasks.summary_generator import SummaryGenerator

DEFAULT_TASKS_FILE = ".claude/tasks/tasks.json"

def cmd_list(args):
    """列出所有任务"""
    persistence = TaskPersistence(args.file)
    tasks = persistence.load()

    if not tasks:
        print("没有任务")
        return

    print(f"共 {len(tasks)} 个任务:\n")

    for task in tasks:
        status_icon = {
            0: "⏳",  # PENDING
            1: "🔄",  # IN_PROGRESS
            2: "✅",  # COMPLETED
            3: "❌",  # FAILED
            4: "🚫"   # BLOCKED
        }.get(task.status.value, "❓")

        print(f"{status_icon} {task.task_id}: {task.subject}")
        if task.owner:
            print(f"   负责人: {task.owner}")
        print()

def cmd_show(args):
    """显示任务详情"""
    persistence = TaskPersistence(args.file)
    tasks = persistence.load()

    task = next((t for t in tasks if t.task_id == args.task_id), None)

    if not task:
        print(f"错误: 未找到任务 {args.task_id}")
        sys.exit(1)

    print(f"任务 ID: {task.task_id}")
    print(f"主题: {task.subject}")
    print(f"描述: {task.description or '(无)'}")
    print(f"状态: {task.status.name}")
    print(f"优先级: {task.priority.name}")
    print(f"负责人: {task.owner or '(未分配)'}")

    if task.dependencies:
        print(f"依赖: {', '.join(task.dependencies)}")

    if task.error:
        print(f"错误: {task.error}")

    print(f"创建时间: {task.created_at}")
    if task.started_at:
        print(f"开始时间: {task.started_at}")
    if task.completed_at:
        print(f"完成时间: {task.completed_at}")

def cmd_stats(args):
    """显示统计信息"""
    persistence = TaskPersistence(args.file)
    tasks = persistence.load()

    generator = SummaryGenerator()
    stats = generator.generate_statistics(tasks)

    print("任务统计:")
    print(f"  总任务数: {stats['total']}")
    print(f"  已完成: {stats['completed']}")
    print(f"  进行中: {stats['in_progress']}")
    print(f"  待处理: {stats['pending']}")
    print(f"  已失败: {stats['failed']}")
    print(f"  已阻塞: {stats['blocked']}")

def cmd_summary(args):
    """生成 Markdown 摘要"""
    persistence = TaskPersistence(args.file)
    tasks = persistence.load()

    generator = SummaryGenerator()

    if args.output:
        generator.save(tasks, args.output)
        print(f"摘要已保存到: {args.output}")
    else:
        summary = generator.generate(tasks)
        print(summary)

def main():
    parser = argparse.ArgumentParser(description="任务管理 CLI 工具")
    parser.add_argument("--file", default=DEFAULT_TASKS_FILE, help="任务文件路径")

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # list 命令
    list_parser = subparsers.add_parser("list", help="列出所有任务")

    # show 命令
    show_parser = subparsers.add_parser("show", help="显示任务详情")
    show_parser.add_argument("task_id", help="任务 ID")

    # stats 命令
    stats_parser = subparsers.add_parser("stats", help="显示统计信息")

    # summary 命令
    summary_parser = subparsers.add_parser("summary", help="生成摘要")
    summary_parser.add_argument("-o", "--output", help="输出文件路径")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "list": cmd_list,
        "show": cmd_show,
        "stats": cmd_stats,
        "summary": cmd_summary
    }

    command_func = commands.get(args.command)
    if command_func:
        command_func(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Make executable**

Run: `chmod +x .claude/bin/tasks`

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tests/test_cli.py .claude/bin/tasks
git commit -m "feat: add CLI tools for task management"
```

---

## 总结

**完成的组件**:
- ✅ 任务数据模型（状态转换、依赖管理）
- ✅ 优先级队列（基于堆的高效队列）
- ✅ 依赖解析器（拓扑排序、循环检测）
- ✅ 任务调度器（异步执行、并发控制）
- ✅ JSON 持久化（保存和加载）
- ✅ Markdown 摘要生成器（统计和可视化）
- ✅ CLI 工具（list、show、stats、summary）

**下一步**: 实施 Part 3 - 闭环执行器
