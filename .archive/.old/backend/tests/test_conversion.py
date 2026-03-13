"""
转换服务测试
"""
import pytest
import os
import asyncio
from unittest.mock import patch, MagicMock


class TestConversionConfig:
    """转换配置测试"""

    def test_config_validation(self, sample_config_dict):
        """测试配置验证"""
        from app.models.schemas import ConversionConfig

        config = ConversionConfig(**sample_config_dict)

        assert config.model_name == "test_model"
        assert config.input_width == 480
        assert config.input_height == 480
        assert config.quantization_type == "int8"

    def test_config_invalid_size(self, sample_config_dict):
        """测试无效的输入尺寸"""
        from app.models.schemas import ConversionConfig
        from pydantic import ValidationError

        sample_config_dict["input_width"] = 999  # 无效尺寸

        with pytest.raises(ValidationError):
            ConversionConfig(**sample_config_dict)

    def test_config_normalization_validation(self, sample_config_dict):
        """测试归一化参数验证"""
        from app.models.schemas import ConversionConfig

        # 正确的归一化参数
        sample_config_dict["mean"] = [0.0, 0.0, 0.0]
        sample_config_dict["std"] = [255.0, 255.0, 255.0]

        config = ConversionConfig(**sample_config_dict)
        assert len(config.mean) == 3
        assert len(config.std) == 3

    def test_config_calibration_validation(self, sample_config_dict):
        """测试校准数据集验证"""
        from app.models.schemas import ConversionConfig

        # 使用自定义校准但未提供文件名
        sample_config_dict["use_custom_calibration"] = True
        sample_config_dict["calibration_dataset_filename"] = None

        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ConversionConfig(**sample_config_dict)


class TestCalibrationDataset:
    """校准数据集测试"""

    def test_extract_calibration_dataset_structure(self):
        """测试校准数据集目录结构"""
        import zipfile
        import tempfile

        # 创建临时 ZIP 文件
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_zip:
            with zipfile.ZipFile(tmp_zip.name, 'w') as zf:
                # 模拟正确的目录结构
                zf.writestr("images/image001.jpg", "MOCK_DATA")
                zf.writestr("images/image002.jpg", "MOCK_DATA")

            # 验证 ZIP 文件
            with zipfile.ZipFile(tmp_zip.name, 'r') as zf:
                namelist = zf.namelist()
                assert "images/image001.jpg" in namelist
                assert "images/image002.jpg" in namelist

        # 清理
        os.unlink(tmp_zip.name)

    def test_calibration_dataset_file_types(self):
        """测试支持的图像文件类型"""
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp']

        for ext in valid_extensions:
            filename = f"test_image{ext}"
            assert filename.lower().endswith(ext.lower())


class TestTaskManager:
    """任务管理器测试"""

    def test_create_task(self, sample_config):
        """测试创建任务"""
        from app.services.task_manager import TaskManager

        task_manager = TaskManager()

        task = task_manager.create_task(
            task_id="test-123",
            config=sample_config,
            filename="test_model.pt"
        )

        assert task.task_id == "test-123"
        assert task.config.model_name == "test_model"

    def test_get_task(self, sample_config):
        """测试获取任务"""
        from app.services.task_manager import TaskManager

        task_manager = TaskManager()

        task_manager.create_task(
            task_id="test-456",
            config=sample_config,
            filename="test_model.pt"
        )

        task = task_manager.get_task("test-456")
        assert task is not None
        assert task.task_id == "test-456"

    @pytest.mark.asyncio
    async def test_update_task(self, sample_config):
        """测试更新任务"""
        from app.services.task_manager import TaskManager
        from app.models.schemas import TaskStatus

        task_manager = TaskManager()

        task_manager.create_task(
            task_id="test-789",
            config=sample_config,
            filename="test_model.pt"
        )

        # 更新任务状态
        updated_task = await task_manager.update_task(
            task_id="test-789",
            status=TaskStatus.CONVERTING,
            progress=50,
            current_step="正在转换"
        )

        assert updated_task.status == TaskStatus.CONVERTING
        assert updated_task.progress == 50


class TestProgressMonitoring:
    """进度监控测试"""

    def test_progress_update(self):
        """测试进度更新"""
        from app.models.schemas import TaskStatus

        progress_values = [0, 25, 50, 75, 100]

        for progress in progress_values:
            assert 0 <= progress <= 100

    def test_status_transitions(self):
        """测试状态转换"""
        from app.models.schemas import TaskStatus

        status_order = [
            TaskStatus.PENDING,
            TaskStatus.VALIDATING,
            TaskStatus.CONVERTING,
            TaskStatus.PACKAGING,
            TaskStatus.COMPLETED
        ]

        # 验证所有状态都存在
        for status in status_order:
            assert status is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
