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
