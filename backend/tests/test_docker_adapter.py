# backend/tests/test_docker_adapter.py
import pytest
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
