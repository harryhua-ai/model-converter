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
        ["python", ".claude/bin/tasks", "--file", "/tmp/test_cli_tasks.json", "list"],
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
        ["python", ".claude/bin/tasks", "--file", "/tmp/test_cli_show.json", "show", "TASK-001"],
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
        ["python", ".claude/bin/tasks", "--file", "/tmp/test_cli_stats.json", "stats"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "总任务数: 2" in result.stdout
