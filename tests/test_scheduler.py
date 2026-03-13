# tests/test_scheduler.py
import pytest
import asyncio
from ultimate_team.task_manager.task import Task, TaskPriority, TaskStatus
from ultimate_team.task_manager.scheduler import TaskScheduler
from ultimate_team.task_manager.queue import TaskQueue

@pytest.mark.anyio
async def test_schedule_single_task():
    """测试调度单个任务"""
    scheduler = TaskScheduler()

    task = Task("TASK-001", "测试任务", priority=TaskPriority.HIGH)

    executed = []

    async def mock_handler(task):
        executed.append(task.task_id)
        task.transition_to(TaskStatus.COMPLETED)

    await scheduler.schedule(task, mock_handler)
    await scheduler.wait_until_complete()

    assert "TASK-001" in executed
    assert task.status == TaskStatus.COMPLETED

@pytest.mark.anyio
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

    # 先添加所有任务到调度器（不并发）
    await scheduler.schedule(low_task, mock_handler)
    await scheduler.schedule(urgent_task, mock_handler)
    await scheduler.schedule(high_task, mock_handler)

    # 等待所有任务完成
    await scheduler.wait_until_complete()

    # 紧急任务应该先执行
    assert executed_order[0] == "TASK-002"
    assert executed_order[1] == "TASK-003"
    assert executed_order[2] == "TASK-001"

@pytest.mark.anyio
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

    # 等待所有任务完成
    await scheduler.wait_until_complete()

    # task1 应该在 task2 之前执行
    assert executed == ["TASK-001", "TASK-002"]
