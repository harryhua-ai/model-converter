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
