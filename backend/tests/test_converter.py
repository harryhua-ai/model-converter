"""
ModelConverter 单元测试
"""
import pytest
from app.core.converter import ModelConverter
from pathlib import Path


@pytest.fixture
def converter():
    """创建转换器实例"""
    return ModelConverter()


@pytest.fixture
def sample_config():
    """示例配置"""
    return {
        "task_id": "test_001",
        "model_type": "YOLOv8",
        "input_size": 480,
        "num_classes": 80,
        "confidence_threshold": 0.25,
        "quantization": "int8"
    }


def test_converter_initialization(converter):
    """测试转换器初始化"""
    assert converter is not None
    assert converter.work_dir.exists()
    assert converter.tools_dir.exists()
    assert converter.quant_script.exists()
    assert converter.quant_config_template.exists()


def test_dependency_check(converter):
    """测试依赖检测"""
    # 应该能检测到依赖是否可用
    assert hasattr(converter, '_ultralytics_available')
    assert hasattr(converter, '_tensorflow_available')
    assert isinstance(converter._ultralytics_available, bool)
    assert isinstance(converter._tensorflow_available, bool)


def test_check_import(converter):
    """测试模块导入检测"""
    # 测试一个肯定存在的模块
    assert converter._check_import("os") is True
    assert converter._check_import("sys") is True

    # 测试一个不存在的模块
    assert converter._check_import("nonexistent_module_xyz") is False


def test_work_dir_creation(tmp_path):
    """测试工作目录创建"""
    work_dir = tmp_path / "custom_converter"
    converter = ModelConverter(work_dir=work_dir)

    assert converter.work_dir == work_dir
    assert work_dir.exists()


def test_prepare_quant_config_without_ml_library(converter, sample_config, tmp_path):
    """测试配置文件准备（不依赖 ML 库）"""
    # 创建临时校准数据集目录
    calib_dir = tmp_path / "calibration_dataset"
    calib_dir.mkdir()

    # 创建测试用的 saved_model 目录
    saved_model_path = tmp_path / "saved_model"
    saved_model_path.mkdir()

    import yaml

    # 读取模板
    with open(converter.quant_config_template) as f:
        expected_config = yaml.safe_load(f)

    # 更新期望的配置
    expected_config["model"]["model_path"] = str(saved_model_path)
    expected_config["model"]["input_shape"] = [480, 480, 3]
    expected_config["quantization"]["calib_dataset_path"] = str(calib_dir)

    # 调用方法
    config_path = converter._prepare_quant_config(
        saved_model_path,
        480,
        str(calib_dir)
    )

    # 验证
    assert config_path.exists()
    assert config_path == converter.work_dir / "user_config_quant.yaml"

    # 验证配置内容
    with open(config_path) as f:
        actual_config = yaml.safe_load(f)

    assert actual_config["model"]["model_path"] == str(saved_model_path)
    assert actual_config["model"]["input_shape"] == [480, 480, 3]
    assert actual_config["quantization"]["calib_dataset_path"] == str(calib_dir)


@pytest.mark.integration
def test_pytorch_to_tflite_conversion(converter, sample_config):
    """测试 PyTorch 到 TFLite 的转换（需要 ML 库）"""
    if not converter._ultralytics_available:
        pytest.skip("Ultralytics 不可用")

    # 这个测试需要真实的模型文件，标记为 integration
    # TODO: 添加真实模型文件的集成测试
    pass


@pytest.mark.integration
def test_full_conversion_pipeline(converter, sample_config):
    """测试完整转换流程（需要 ML 库和 Docker）"""
    if not converter._ultralytics_available or not converter._tensorflow_available:
        pytest.skip("ML 库不可用")

    # 标记为 integration，需要真实环境和 Docker
    # TODO: 添加端到端集成测试
    pass


def test_convert_raises_error_without_ml_library(converter, sample_config):
    """测试在没有 ML 库时调用 convert 会抛出错误"""
    # 强制设置为不可用
    converter._ultralytics_available = False
    converter._tensorflow_available = False

    with pytest.raises(RuntimeError) as exc_info:
        converter.convert("model.pt", sample_config)

    assert "ML 库不可用" in str(exc_info.value)
    assert "ultralytics tensorflow" in str(exc_info.value)
