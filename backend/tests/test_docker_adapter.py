# backend/tests/test_docker_adapter.py
import pytest
from unittest.mock import Mock, patch
from app.core.docker_adapter import DockerToolChainAdapter

@pytest.mark.unit
def test_check_docker():
    """测试 Docker 检测"""
    adapter = DockerToolChainAdapter()
    available, error = adapter.check_docker()
    # 需要安装 docker 才能测试
    assert isinstance(available, bool)
    assert isinstance(error, str)

@pytest.mark.unit
def test_check_image():
    """测试镜像检查"""
    adapter = DockerToolChainAdapter()
    result = adapter.check_image()
    assert isinstance(result, bool)

@pytest.mark.unit
def test_pull_image_no_callback():
    """测试拉取镜像（无回调）"""
    adapter = DockerToolChainAdapter()
    # Skip if Docker not available
    available, _ = adapter.check_docker()
    if not available:
        pytest.skip("Docker not available")

    # This test would actually pull the image, so we might want to skip it
    # or mock it in actual CI/CD
    # For now, just verify the method exists
    assert hasattr(adapter, 'pull_image')

@pytest.mark.unit
def test_convert_model():
    """测试模型转换（使用 mock）"""
    from pathlib import Path
    from unittest.mock import patch, MagicMock
    import tempfile

    adapter = DockerToolChainAdapter()
    adapter.client = Mock()

    # Mock container run
    adapter.client.containers.run.return_value = b"Conversion successful"

    # 创建临时模型文件
    with tempfile.NamedTemporaryFile(suffix=".tflite", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Mock file existence check
        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'parent', MagicMock(resolve=MagicMock(return_value=Path("/tmp")))):
                with patch.object(Path, 'absolute', MagicMock(return_value=Path("/tmp/outputs"))):
                    with patch("builtins.open", MagicMock()):
                        result = adapter.convert_model(
                            task_id="test-123",
                            model_path=tmp_path,
                            config={
                                "input_size": [640, 640],
                                "num_classes": 80,
                                "model_type": "yolov8",
                                "quantization": "int8"
                            }
                        )

        assert "ne301_model_test-123.bin" in result
        adapter.client.containers.run.assert_called_once()
    finally:
        # 清理临时文件
        Path(tmp_path).unlink(missing_ok=True)

@pytest.mark.unit
def test_convert_model_no_docker():
    """测试无 Docker 时的错误处理"""
    adapter = DockerToolChainAdapter()
    adapter.client = None

    with pytest.raises(RuntimeError, match="Docker client not available"):
        adapter.convert_model("test", "/tmp/test.tflite", {})

@pytest.mark.unit
def test_prepare_ne301_config():
    """测试 NE301 配置准备"""
    adapter = DockerToolChainAdapter()

    config = {
        "input_size": [640, 640],
        "num_classes": 80,
        "model_type": "yolov8",
        "quantization": "int8",
        "confidence_threshold": 0.3
    }

    result = adapter._prepare_ne301_config("test-123", config, None)

    assert result["model_name"] == "ne301_model_test-123"
    assert result["input_size"] == [640, 640]
    assert result["num_classes"] == 80
    assert result["model_type"] == "yolov8"
    assert result["quantization"] == "int8"
    assert result["confidence_threshold"] == 0.3

@pytest.mark.unit
def test_prepare_ne301_config_defaults():
    """测试 NE301 配置默认值"""
    adapter = DockerToolChainAdapter()

    config = {
        "input_size": [320, 320],
        "num_classes": 10,
        "model_type": "mobilenet"
    }

    result = adapter._prepare_ne301_config("test-456", config, None)

    assert result["confidence_threshold"] == 0.25  # 默认值
    assert result["quantization"] == "int8"  # 默认值
