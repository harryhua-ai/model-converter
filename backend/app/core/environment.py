# backend/app/core/environment.py
import platform
import logging
from app.models.schemas import EnvironmentStatus
from app.core.docker_adapter import DockerToolChainAdapter

logger = logging.getLogger(__name__)


class EnvironmentDetector:
    """环境检测器(混合架构 - 仅 Docker)"""

    def __init__(self):
        self.toolchain = DockerToolChainAdapter()

    def check(self) -> EnvironmentStatus:
        """检查环境状态"""
        # 1. 检查 Docker 是否安装并运行
        docker_available, error = self.toolchain.check_docker()
        if not docker_available:
            return EnvironmentStatus(
                status="docker_not_installed",
                mode="none",
                message="Docker 未安装或未启动",
                error=error,
                guide=self._get_docker_install_guide()
            )

        # 2. 检查镜像是否存在
        if not self.toolchain.check_image():
            return EnvironmentStatus(
                status="image_pull_required",
                mode="docker",
                message="Docker 已就绪,首次转换时会自动拉取工具镜像",
                image_size="~3GB",
                estimated_time="3-5 分钟(取决于网络速度)"
            )

        # 3. 环境完全就绪
        return EnvironmentStatus(
            status="ready",
            mode="docker",
            message="环境就绪,可以开始转换"
        )

    def _get_docker_install_guide(self) -> dict:
        """获取 Docker 安装指南"""
        system = platform.system()

        if system == "Darwin":
            return {
                "title": "安装 Docker Desktop for Mac",
                "url": "https://www.docker.com/products/docker-desktop",
                "steps": [
                    "1. 下载 Docker Desktop for Mac",
                    "2. 打开 .dmg 文件并拖拽到 Applications",
                    "3. 启动 Docker Desktop",
                    "4. 等待 Docker 启动完成(菜单栏图标)"
                ]
            }
        elif system == "Linux":
            return {
                "title": "安装 Docker Engine",
                "url": "https://docs.docker.com/engine/install/",
                "command": "curl -fsSL https://get.docker.com | sh"
            }
        elif system == "Windows":
            return {
                "title": "安装 Docker Desktop for Windows",
                "url": "https://www.docker.com/products/docker-desktop",
                "steps": [
                    "1. 下载 Docker Desktop for Windows",
                    "2. 运行安装程序",
                    "3. 启用 WSL 2 功能(如果需要)",
                    "4. 重启计算机",
                    "5. 启动 Docker Desktop"
                ]
            }

        return {}
