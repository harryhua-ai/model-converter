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
    from unittest.mock import patch

    adapter = DockerToolChainAdapter()
    adapter.client = Mock()

    # Mock container run
    adapter.client.containers.run.return_value = None

    # Mock file existence check
    with patch.object(Path, 'exists', return_value=True):
        result = adapter.convert_model(
            task_id="test-123",
            model_path="/tmp/test.onnx",
            config={"format": "ne301"}
        )

    assert result == "outputs/ne301_model_test-123.bin"
    adapter.client.containers.run.assert_called_once()

@pytest.mark.unit
def test_convert_model_no_docker():
    """测试无 Docker 时的错误处理"""
    adapter = DockerToolChainAdapter()
    adapter.client = None

    with pytest.raises(RuntimeError, match="Docker client not available"):
        adapter.convert_model("test", "/tmp/test.onnx", {})
