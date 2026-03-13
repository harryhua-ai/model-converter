import sys
from pathlib import Path

# Add .claude directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / ".claude"))

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
