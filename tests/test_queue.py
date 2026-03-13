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

def test_queue_length():
    """测试队列长度"""
    queue = TaskQueue()

    task1 = Task("TASK-001", "任务1", priority=TaskPriority.HIGH)
    task2 = Task("TASK-002", "任务2", priority=TaskPriority.MEDIUM)

    assert len(queue) == 0

    queue.enqueue(task1)
    assert len(queue) == 1

    queue.enqueue(task2)
    assert len(queue) == 2

    queue.remove("TASK-001")
    assert len(queue) == 1

    queue.dequeue()
    assert len(queue) == 0
