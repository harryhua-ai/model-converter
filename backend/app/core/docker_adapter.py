# backend/app/core/docker_adapter.py
import docker
import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional

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
        config: Dict[str, Any],
        yaml_path: Optional[str] = None
    ) -> str:
        """使用 Docker 容器将量化 TFLite 模型转换为 NE301 .bin

        Args:
            task_id: 任务 ID
            model_path: 量化后的 TFLite 模型路径
            config: 转换配置
            yaml_path: YAML 类别定义文件（可选）

        Returns:
            NE301 .bin 文件路径

        Raises:
            RuntimeError: Docker client not available
            FileNotFoundError: 模型文件不存在
            ValueError: 配置无效
        """
        if not self.client:
            raise RuntimeError("Docker client not available")

        logger.info(f"步骤 3: 使用 Docker 转换 {model_path} 为 NE301 .bin")

        # 验证模型文件存在
        model_path_obj = Path(model_path)
        if not model_path_obj.exists():
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

        # 准备输出路径
        output_dir = Path("outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_filename = f"ne301_model_{task_id}.bin"
        output_path = output_dir / output_filename

        # 准备 NE301 JSON 配置
        ne301_config = self._prepare_ne301_config(task_id, config, yaml_path)
        config_path = output_dir / f"{task_id}_config.json"
        with open(config_path, "w") as f:
            json.dump(ne301_config, f, indent=2)

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
            "--config", json.dumps(ne301_config),
            "--output", f"/output/{output_filename}"
        ]

        try:
            logger.info(f"启动 Docker 容器执行转换...")

            # 运行容器（同步等待）
            result = self.client.containers.run(
                self.image_name,
                command=command,
                volumes=volumes,
                remove=True,
                detach=False,
                mem_limit="2g",
                cpu_count=1
            )

            logger.info(f"Docker 容器输出: {result.decode('utf-8')}")

            # 验证输出文件
            if not output_path.exists():
                raise FileNotFoundError(f"NE301 .bin 文件未生成: {output_path}")

            logger.info(f"✅ 转换成功: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"转换失败 for task {task_id}: {e}")
            raise

    def _prepare_ne301_config(
        self,
        task_id: str,
        config: Dict[str, Any],
        yaml_path: Optional[str]
    ) -> Dict[str, Any]:
        """准备 NE301 JSON 配置

        Args:
            task_id: 任务 ID
            config: 转换配置
            yaml_path: YAML 类别定义文件路径（可选）

        Returns:
            NE301 JSON 配置字典
        """
        ne301_config = {
            "model_name": f"ne301_model_{task_id}",
            "input_size": config["input_size"],
            "num_classes": config["num_classes"],
            "confidence_threshold": config.get("confidence_threshold", 0.25),
            "model_type": config["model_type"],
            "quantization": config.get("quantization", "int8")
        }

        # 如果有 YAML 文件，添加类别信息
        if yaml_path and Path(yaml_path).exists():
            try:
                import yaml
                with open(yaml_path) as f:
                    yaml_data = yaml.safe_load(f)
                    # 尝试读取类别名称
                    for key in ["names", "classes", "labels", "categories"]:
                        if key in yaml_data:
                            ne301_config["class_names"] = yaml_data[key]
                            break
            except ImportError:
                logger.warning("PyYAML 未安装，跳过 YAML 文件解析")
            except Exception as e:
                logger.warning(f"解析 YAML 文件失败: {e}")

        return ne301_config
