# backend/tests/test_environment.py
import pytest
from unittest.mock import Mock, patch
from app.core.environment import EnvironmentDetector
from app.models.schemas import EnvironmentStatus


class TestEnvironmentDetector:
    """EnvironmentDetector 测试"""

    def test_check_docker_not_installed(self):
        """测试 Docker 未安装的情况"""
        # 创建 mock adapter
        mock_adapter = Mock()
        mock_adapter.check_docker.return_value = (False, "Docker daemon not running")

        # 替换 adapter
        detector = EnvironmentDetector()
        detector.toolchain = mock_adapter

        # 执行检查
        result = detector.check()

        # 验证结果
        assert result.status == "docker_not_installed"
        assert result.mode == "none"
        assert "Docker 未安装或未启动" in result.message
        assert result.error == "Docker daemon not running"
        assert result.guide is not None
        assert "title" in result.guide

    def test_check_image_not_found(self):
        """测试镜像不存在的情况"""
        # 创建 mock adapter
        mock_adapter = Mock()
        mock_adapter.check_docker.return_value = (True, "")
        mock_adapter.check_image.return_value = False

        # 替换 adapter
        detector = EnvironmentDetector()
        detector.toolchain = mock_adapter

        # 执行检查
        result = detector.check()

        # 验证结果
        assert result.status == "image_pull_required"
        assert result.mode == "docker"
        assert "Docker 已就绪" in result.message
        assert result.image_size == "~3GB"
        assert "3-5 分钟" in result.estimated_time

    def test_check_ready(self):
        """测试环境完全就绪的情况"""
        # 创建 mock adapter
        mock_adapter = Mock()
        mock_adapter.check_docker.return_value = (True, "")
        mock_adapter.check_image.return_value = True

        # 替换 adapter
        detector = EnvironmentDetector()
        detector.toolchain = mock_adapter

        # 执行检查
        result = detector.check()

        # 验证结果
        assert result.status == "ready"
        assert result.mode == "docker"
        assert "环境就绪" in result.message
        assert result.error is None
        assert result.guide is None

    @patch("app.core.environment.platform.system")
    def test_get_docker_install_guide_macos(self, mock_system):
        """测试 macOS 安装指南"""
        mock_system.return_value = "Darwin"

        detector = EnvironmentDetector()
        guide = detector._get_docker_install_guide()

        assert guide["title"] == "安装 Docker Desktop for Mac"
        assert "url" in guide
        assert "steps" in guide
        assert len(guide["steps"]) == 4

    @patch("app.core.environment.platform.system")
    def test_get_docker_install_guide_linux(self, mock_system):
        """测试 Linux 安装指南"""
        mock_system.return_value = "Linux"

        detector = EnvironmentDetector()
        guide = detector._get_docker_install_guide()

        assert guide["title"] == "安装 Docker Engine"
        assert "url" in guide
        assert "command" in guide
        assert "curl -fsSL" in guide["command"]

    @patch("app.core.environment.platform.system")
    def test_get_docker_install_guide_windows(self, mock_system):
        """测试 Windows 安装指南"""
        mock_system.return_value = "Windows"

        detector = EnvironmentDetector()
        guide = detector._get_docker_install_guide()

        assert guide["title"] == "安装 Docker Desktop for Windows"
        assert "url" in guide
        assert "steps" in guide
        assert len(guide["steps"]) == 5

    @patch("app.core.environment.platform.system")
    def test_get_docker_install_guide_unknown(self, mock_system):
        """测试未知系统"""
        mock_system.return_value = "FreeBSD"

        detector = EnvironmentDetector()
        guide = detector._get_docker_install_guide()

        assert guide == {}
