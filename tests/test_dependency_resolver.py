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
    task1.transition_to(TaskStatus.IN_PROGRESS)
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
