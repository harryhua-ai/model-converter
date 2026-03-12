"""
Pydantic schemas 单元测试

测试所有数据模型的验证逻辑:
- ConversionConfig: 转换参数验证
- ClassDefinition: 类别定义验证
- ConversionTask: 任务状态验证
- EnvironmentStatus: 环境状态验证
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.schemas import (
    ConversionConfig,
    ClassDefinition,
    ConversionTask,
    EnvironmentStatus,
)


@pytest.mark.unit
class TestConversionConfig:
    """ConversionConfig 测试套件"""

    def test_default_values(self):
        """测试默认值是否正确应用"""
        config = ConversionConfig()
        assert config.model_type == "YOLOv8"
        assert config.input_size == 480
        assert config.num_classes == 80
        assert config.confidence_threshold == 0.25
        assert config.quantization == "int8"
        assert config.use_calibration is False

    def test_valid_custom_values(self):
        """测试有效的自定义值"""
        config = ConversionConfig(
            model_type="YOLOX",
            input_size=640,
            num_classes=100,
            confidence_threshold=0.5,
            use_calibration=True,
        )
        assert config.model_type == "YOLOX"
        assert config.input_size == 640
        assert config.num_classes == 100
        assert config.confidence_threshold == 0.5
        assert config.use_calibration is True

    def test_num_classes_minimum_boundary(self):
        """测试 num_classes 最小边界值"""
        config = ConversionConfig(num_classes=1)
        assert config.num_classes == 1

    def test_num_classes_maximum_boundary(self):
        """测试 num_classes 最大边界值"""
        config = ConversionConfig(num_classes=1000)
        assert config.num_classes == 1000

    def test_num_classes_below_minimum_raises_error(self):
        """测试 num_classes 小于最小值时抛出 ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            ConversionConfig(num_classes=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_num_classes_above_maximum_raises_error(self):
        """测试 num_classes 大于最大值时抛出 ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            ConversionConfig(num_classes=1001)
        assert "less than or equal to 1000" in str(exc_info.value)

    def test_confidence_threshold_minimum_boundary(self):
        """测试 confidence_threshold 最小边界值"""
        config = ConversionConfig(confidence_threshold=0.01)
        assert config.confidence_threshold == 0.01

    def test_confidence_threshold_maximum_boundary(self):
        """测试 confidence_threshold 最大边界值"""
        config = ConversionConfig(confidence_threshold=0.99)
        assert config.confidence_threshold == 0.99

    def test_confidence_threshold_below_minimum_raises_error(self):
        """测试 confidence_threshold 小于最小值时抛出 ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            ConversionConfig(confidence_threshold=0.0)
        assert "greater than or equal to 0.01" in str(exc_info.value)

    def test_confidence_threshold_above_maximum_raises_error(self):
        """测试 confidence_threshold 大于最大值时抛出 ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            ConversionConfig(confidence_threshold=1.0)
        assert "less than or equal to 0.99" in str(exc_info.value)

    def test_invalid_model_type_raises_error(self):
        """测试无效的 model_type 抛出 ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            ConversionConfig(model_type="InvalidModel")
        assert "YOLOv8" in str(exc_info.value) or "YOLOX" in str(exc_info.value)

    def test_invalid_input_size_raises_error(self):
        """测试无效的 input_size 抛出 ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            ConversionConfig(input_size=512)
        assert "256" in str(exc_info.value) or "480" in str(exc_info.value) or "640" in str(exc_info.value)


@pytest.mark.unit
class TestClassDefinition:
    """ClassDefinition 测试套件"""

    def test_basic_creation(self):
        """测试基本的类别定义创建"""
        class_def = ClassDefinition(
            classes=[
                {"name": "person", "id": 0, "color": [255, 0, 0]},
                {"name": "car", "id": 1, "color": [0, 255, 0]},
            ]
        )
        assert len(class_def.classes) == 2
        assert class_def.classes[0]["name"] == "person"
        assert class_def.classes[1]["id"] == 1

    def test_empty_classes_list(self):
        """测试空的类别列表"""
        class_def = ClassDefinition(classes=[])
        assert class_def.classes == []

    def test_single_class(self):
        """测试单个类别"""
        class_def = ClassDefinition(classes=[{"name": "person", "id": 0}])
        assert len(class_def.classes) == 1
        assert class_def.classes[0]["name"] == "person"


@pytest.mark.unit
class TestConversionTask:
    """ConversionTask 测试套件"""

    def test_required_fields(self):
        """测试必需字段"""
        now = datetime.now()
        config = ConversionConfig()
        task = ConversionTask(
            task_id="test-123",
            status="pending",
            config=config,
            created_at=now,
            updated_at=now,
        )
        assert task.task_id == "test-123"
        assert task.status == "pending"
        assert task.config == config
        assert task.created_at == now
        assert task.updated_at == now

    def test_default_progress(self):
        """测试 progress 默认值"""
        now = datetime.now()
        config = ConversionConfig()
        task = ConversionTask(
            task_id="test-123",
            status="pending",
            config=config,
            created_at=now,
            updated_at=now,
        )
        assert task.progress == 0

    def test_default_current_step(self):
        """测试 current_step 默认值"""
        now = datetime.now()
        config = ConversionConfig()
        task = ConversionTask(
            task_id="test-123",
            status="pending",
            config=config,
            created_at=now,
            updated_at=now,
        )
        assert task.current_step == ""

    def test_optional_fields_none(self):
        """测试可选字段默认为 None"""
        now = datetime.now()
        config = ConversionConfig()
        task = ConversionTask(
            task_id="test-123",
            status="pending",
            config=config,
            created_at=now,
            updated_at=now,
        )
        assert task.completed_at is None
        assert task.error_message is None
        assert task.output_filename is None

    def test_optional_fields_with_values(self):
        """测试可选字段设置值"""
        now = datetime.now()
        completed = datetime.now()
        config = ConversionConfig()
        task = ConversionTask(
            task_id="test-123",
            status="completed",
            config=config,
            created_at=now,
            updated_at=now,
            completed_at=completed,
            error_message=None,
            output_filename="model.tflite",
        )
        assert task.completed_at == completed
        assert task.output_filename == "model.tflite"

    def test_progress_minimum_boundary(self):
        """测试 progress 最小边界值"""
        now = datetime.now()
        config = ConversionConfig()
        task = ConversionTask(
            task_id="test-123",
            status="running",
            config=config,
            created_at=now,
            updated_at=now,
            progress=0,
        )
        assert task.progress == 0

    def test_progress_maximum_boundary(self):
        """测试 progress 最大边界值"""
        now = datetime.now()
        config = ConversionConfig()
        task = ConversionTask(
            task_id="test-123",
            status="completed",
            config=config,
            created_at=now,
            updated_at=now,
            progress=100,
        )
        assert task.progress == 100

    def test_progress_below_minimum_raises_error(self):
        """测试 progress 小于最小值时抛出 ValidationError"""
        now = datetime.now()
        config = ConversionConfig()
        with pytest.raises(ValidationError) as exc_info:
            ConversionTask(
                task_id="test-123",
                status="running",
                config=config,
                created_at=now,
                updated_at=now,
                progress=-1,
            )
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_progress_above_maximum_raises_error(self):
        """测试 progress 大于最大值时抛出 ValidationError"""
        now = datetime.now()
        config = ConversionConfig()
        with pytest.raises(ValidationError) as exc_info:
            ConversionTask(
                task_id="test-123",
                status="running",
                config=config,
                created_at=now,
                updated_at=now,
                progress=101,
            )
        assert "less than or equal to 100" in str(exc_info.value)

    def test_invalid_status_raises_error(self):
        """测试无效的 status 抛出 ValidationError"""
        now = datetime.now()
        config = ConversionConfig()
        with pytest.raises(ValidationError) as exc_info:
            ConversionTask(
                task_id="test-123",
                status="invalid_status",
                config=config,
                created_at=now,
                updated_at=now,
            )
        assert "pending" in str(exc_info.value) or "running" in str(exc_info.value)

    def test_all_valid_status_values(self):
        """测试所有有效的 status 值"""
        now = datetime.now()
        config = ConversionConfig()
        valid_statuses = ["pending", "running", "completed", "failed"]
        for status in valid_statuses:
            task = ConversionTask(
                task_id="test-123",
                status=status,
                config=config,
                created_at=now,
                updated_at=now,
            )
            assert task.status == status


@pytest.mark.unit
class TestEnvironmentStatus:
    """EnvironmentStatus 测试套件"""

    def test_basic_creation(self):
        """测试基本的环境状态创建"""
        status = EnvironmentStatus(
            status="ready", mode="docker", message="Environment is ready"
        )
        assert status.status == "ready"
        assert status.mode == "docker"
        assert status.message == "Environment is ready"

    def test_all_valid_status_literals(self):
        """测试所有有效的 status 字面量值"""
        valid_statuses = ["ready", "docker_not_installed", "image_pull_required", "not_configured"]
        for status_value in valid_statuses:
            status = EnvironmentStatus(
                status=status_value, mode="docker", message="Test message"
            )
            assert status.status == status_value

    def test_all_valid_mode_literals(self):
        """测试所有有效的 mode 字面量值"""
        valid_modes = ["docker", "none"]
        for mode_value in valid_modes:
            status = EnvironmentStatus(
                status="ready", mode=mode_value, message="Test message"
            )
            assert status.mode == mode_value

    def test_optional_fields_default_to_none(self):
        """测试可选字段默认为 None"""
        status = EnvironmentStatus(
            status="ready", mode="docker", message="Test message"
        )
        assert status.image_size is None
        assert status.estimated_time is None
        assert status.error is None
        assert status.guide is None

    def test_optional_fields_with_values(self):
        """测试可选字段设置值"""
        guide = {"step1": "Install Docker", "step2": "Pull image"}
        status = EnvironmentStatus(
            status="ready",
            mode="docker",
            message="Test message",
            image_size="2.5GB",
            estimated_time="5 minutes",
            error=None,
            guide=guide,
        )
        assert status.image_size == "2.5GB"
        assert status.estimated_time == "5 minutes"
        assert status.guide == guide

    def test_invalid_status_raises_error(self):
        """测试无效的 status 抛出 ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            EnvironmentStatus(
                status="invalid", mode="docker", message="Test message"
            )
        assert "ready" in str(exc_info.value) or "docker_not_installed" in str(exc_info.value)

    def test_invalid_mode_raises_error(self):
        """测试无效的 mode 抛出 ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            EnvironmentStatus(
                status="ready", mode="invalid", message="Test message"
            )
        assert "docker" in str(exc_info.value) or "none" in str(exc_info.value)

    def test_docker_not_installed_status(self):
        """测试 docker_not_installed 状态"""
        status = EnvironmentStatus(
            status="docker_not_installed",
            mode="none",
            message="Docker is not installed",
            error="Docker command not found",
        )
        assert status.status == "docker_not_installed"
        assert status.mode == "none"
        assert status.error == "Docker command not found"

    def test_image_pull_required_status(self):
        """测试 image_pull_required 状态"""
        status = EnvironmentStatus(
            status="image_pull_required",
            mode="docker",
            message="Docker image needs to be pulled",
            estimated_time="3 minutes",
        )
        assert status.status == "image_pull_required"
        assert status.estimated_time == "3 minutes"
