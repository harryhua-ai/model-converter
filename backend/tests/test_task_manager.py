"""
TaskManager 单元测试
"""
import pytest
import time
from datetime import datetime
from app.core.task_manager import TaskManager, get_task_manager
from app.models.schemas import ConversionConfig


class TestTaskManagerSingleton:
    """测试单例模式"""

    def test_singleton_pattern(self):
        """验证单例模式 - 多次实例化返回同一对象"""
        # 清理单例以确保测试隔离
        TaskManager._instance = None
        global _task_manager
        import app.core.task_manager as tm_module
        tm_module._task_manager = None

        manager1 = TaskManager()
        manager2 = TaskManager()

        assert manager1 is manager2
        assert id(manager1) == id(manager2)

    def test_get_task_manager_singleton(self):
        """验证 get_task_manager 返回单例"""
        # 清理单例
        TaskManager._instance = None
        global _task_manager
        import app.core.task_manager as tm_module
        tm_module._task_manager = None

        manager1 = get_task_manager()
        manager2 = get_task_manager()

        assert manager1 is manager2


class TestTaskManager:
    """测试 TaskManager 核心功能"""

    def setup_method(self):
        """每个测试前重置单例"""
        TaskManager._instance = None
        global _task_manager
        import app.core.task_manager as tm_module
        tm_module._task_manager = None
        self.task_manager = TaskManager()

    def test_create_task(self):
        """测试创建任务"""
        config = ConversionConfig(
            model_type="YOLOv8",
            input_size=480,
            num_classes=80
        )

        task_id = self.task_manager.create_task(config)

        # 验证任务 ID 格式（UUID）
        assert isinstance(task_id, str)
        assert len(task_id) == 36  # UUID 格式长度

        # 验证任务已创建
        task = self.task_manager.get_task(task_id)
        assert task is not None
        assert task.task_id == task_id
        assert task.status == "pending"
        assert task.progress == 0
        assert task.config == config
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)

    def test_create_task_multiple(self):
        """测试创建多个任务"""
        config1 = ConversionConfig(
            model_type="YOLOv8",
            input_size=480,
            num_classes=80
        )
        config2 = ConversionConfig(
            model_type="YOLOX",
            input_size=640,
            num_classes=100
        )

        task_id1 = self.task_manager.create_task(config1)
        task_id2 = self.task_manager.create_task(config2)

        # 验证任务 ID 不同
        assert task_id1 != task_id2

        # 验证两个任务都存在
        task1 = self.task_manager.get_task(task_id1)
        task2 = self.task_manager.get_task(task_id2)

        assert task1 is not None
        assert task2 is not None
        assert task1.config.model_type == "YOLOv8"
        assert task2.config.model_type == "YOLOX"

    def test_get_task_nonexistent(self):
        """测试获取不存在的任务"""
        task = self.task_manager.get_task("nonexistent_id")
        assert task is None

    def test_update_progress(self):
        """测试更新任务进度"""
        config = ConversionConfig(
            model_type="YOLOv8",
            input_size=480,
            num_classes=80
        )
        task_id = self.task_manager.create_task(config)

        # 更新进度
        self.task_manager.update_progress(task_id, 50, "Converting model...")

        # 验证进度已更新
        task = self.task_manager.get_task(task_id)
        assert task.progress == 50
        assert task.current_step == "Converting model..."
        assert isinstance(task.updated_at, datetime)

        # 再次更新
        self.task_manager.update_progress(task_id, 75, "Optimizing...")
        task = self.task_manager.get_task(task_id)
        assert task.progress == 75
        assert task.current_step == "Optimizing..."

    def test_update_progress_nonexistent_task(self):
        """测试更新不存在的任务进度 - 不应抛出异常"""
        # 应该优雅地处理不存在的任务
        self.task_manager.update_progress("nonexistent_id", 50, "Testing...")
        # 验证不会崩溃

    def test_complete_task(self):
        """测试标记任务完成"""
        config = ConversionConfig(
            model_type="YOLOv8",
            input_size=480,
            num_classes=80
        )
        task_id = self.task_manager.create_task(config)

        # 标记任务完成
        self.task_manager.complete_task(task_id, "output.onnx")

        # 验证任务状态
        task = self.task_manager.get_task(task_id)
        assert task.status == "completed"
        assert task.progress == 100
        assert task.output_filename == "output.onnx"
        assert isinstance(task.completed_at, datetime)
        assert isinstance(task.updated_at, datetime)

    def test_complete_task_nonexistent(self):
        """测试完成不存在的任务 - 不应抛出异常"""
        self.task_manager.complete_task("nonexistent_id", "output.onnx")
        # 验证不会崩溃

    def test_fail_task(self):
        """测试标记任务失败"""
        config = ConversionConfig(
            model_type="YOLOv8",
            input_size=480,
            num_classes=80
        )
        task_id = self.task_manager.create_task(config)

        # 标记任务失败
        self.task_manager.complete_task(task_id, "output.onnx")
        self.task_manager.fail_task(task_id, "Conversion failed: out of memory")

        # 验证任务状态
        task = self.task_manager.get_task(task_id)
        assert task.status == "failed"
        assert task.error_message == "Conversion failed: out of memory"
        assert isinstance(task.updated_at, datetime)

    def test_fail_task_nonexistent(self):
        """测试失败不存在的任务 - 不应抛出异常"""
        self.task_manager.fail_task("nonexistent_id", "Test error")
        # 验证不会崩溃

    def test_task_lifecycle(self):
        """测试完整任务生命周期"""
        config = ConversionConfig(
            model_type="YOLOv8",
            input_size=480,
            num_classes=80
        )

        # 1. 创建任务
        task_id = self.task_manager.create_task(config)
        task = self.task_manager.get_task(task_id)
        assert task.status == "pending"
        assert task.progress == 0

        # 2. 更新进度
        self.task_manager.update_progress(task_id, 25, "Loading model...")
        task = self.task_manager.get_task(task_id)
        assert task.progress == 25
        assert task.current_step == "Loading model..."

        # 3. 继续更新
        self.task_manager.update_progress(task_id, 50, "Converting...")
        task = self.task_manager.get_task(task_id)
        assert task.progress == 50

        # 4. 标记完成
        self.task_manager.complete_task(task_id, "model.onnx")
        task = self.task_manager.get_task(task_id)
        assert task.status == "completed"
        assert task.progress == 100
        assert task.output_filename == "model.onnx"
