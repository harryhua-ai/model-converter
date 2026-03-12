# backend/app/core/docker_adapter.py
import docker
import json
import logging
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

class DockerToolChainAdapter:
    """Docker 工具链适配器（混合架构核心）"""

    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None

        self.image_name = "camthink/ne301-dev:latest"

    def check_docker(self) -> tuple[bool, str]:
        """检查 Docker 是否可用

        Returns:
            (是否可用, 错误信息)
        """
        if not self.client:
            return False, "Docker client not initialized"

        try:
            self.client.ping()
            return True, ""
        except docker.errors.DockerException as e:
            return False, f"Docker not available: {str(e)}"

    def check_image(self) -> bool:
        """检查镜像是否存在"""
        if not self.client:
            return False

        try:
            self.client.images.get(self.image_name)
            return True
        except docker.errors.ImageNotFound:
            return False

    def pull_image(
        self,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> bool:
        """拉取 Docker 镜像

        Args:
            progress_callback: 进度回调函数(progress: int)

        Returns:
            是否成功
        """
        if not self.client:
            logger.error("Docker client not available")
            return False

        try:
            logger.info(f"Pulling image {self.image_name}...")

            for layer in self.client.images.pull(
                self.image_name,
                stream=True,
                decode=True
            ):
                if progress_callback and "progressDetail" in layer:
                    progress = layer["progressDetail"].get("current", 0)
                    total = layer["progressDetail"].get("total", 100)
                    progress_callback(int(progress / total * 100))

            logger.info("Image pulled successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to pull image: {e}")
            return False

    def convert_model(
        self,
        task_id: str,
        model_path: str,
        config: dict
    ) -> str:
        """在 Docker 容器中执行转换

        Args:
            task_id: 任务 ID
            model_path: 模型文件路径（本地）
            config: 转换配置

        Returns:
            输出文件路径（本地）

        Raises:
            RuntimeError: Docker client not available
            FileNotFoundError: 模型文件不存在
            ValueError: 配置无效
        """
        if not self.client:
            raise RuntimeError("Docker client not available")

        # Validate model file exists
        model_path_obj = Path(model_path)
        if not model_path_obj.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # Ensure output directory exists
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)

        # 准备卷映射
        model_dir = model_path_obj.parent.resolve()
        output_dir_abs = output_dir.absolute()

        volumes = {
            str(model_dir): {"bind": "/input", "mode": "ro"},
            str(output_dir_abs): {"bind": "/output", "mode": "rw"}
        }

        # 构建命令
        model_filename = Path(model_path).name
        command = [
            "python",
            "/workspace/ne301/Script/model_packager.py",
            "create",
            "--model", f"/input/{model_filename}",
            "--config", json.dumps(config),
            "--output", f"/output/ne301_model_{task_id}.bin"
        ]

        try:
            logger.info(f"Starting conversion for task {task_id}")

            # 运行容器（同步等待）
            # 容器会在完成后自动删除（remove=True）
            self.client.containers.run(
                self.image_name,
                command=command,
                volumes=volumes,
                remove=True,
                detach=False
            )

            logger.info(f"Conversion completed for task {task_id}")
            return f"outputs/ne301_model_{task_id}.bin"

        except Exception as e:
            logger.error(f"Conversion failed for task {task_id}: {e}")
            raise
