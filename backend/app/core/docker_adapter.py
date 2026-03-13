"""
Docker 工具链适配器（容器化版本）

参考：camthink-ai/AIToolStack/backend/utils/ne301_export.py
"""
import docker
import subprocess
import logging
import threading
import queue
import time
import json
import os
import shutil
from pathlib import Path
from typing import Callable, Dict, Any, Optional

from .config import settings

logger = logging.getLogger(__name__)


class DockerToolChainAdapter:
    """Docker 工具链适配器"""

    def __init__(self):
        self.ne301_image = settings.NE301_DOCKER_IMAGE
        self.ne301_project_path = Path(settings.NE301_PROJECT_PATH)

        try:
            self.client = docker.from_env()
            logger.info(f"Docker 客户端初始化成功，NE301 镜像: {self.ne301_image}")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None

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
        """检查 NE301 镜像是否存在

        Returns:
            镜像是否存在
        """
        if not self.client:
            return False

        try:
            self.client.images.get(self.ne301_image)
            return True
        except docker.errors.ImageNotFound:
            return False
        except Exception as e:
            logger.error(f"检查镜像失败: {e}")
            return False

    def _get_host_path(self, container_path: Path) -> Optional[str]:
        """获取宿主机路径（4级回退机制）

        参考 AIToolStack 的实现，确保 Docker-in-Docker 场景下正确映射路径

        Args:
            container_path: 容器内路径

        Returns:
            宿主机路径，如果获取失败则返回 None
        """
        import subprocess
        import json

        container_path_str = str(container_path)

        # 优先级 1: 使用 docker inspect（最精确）
        container_name = os.environ.get("CONTAINER_NAME", "model-converter-api")
        try:
            inspect_cmd = [
                "docker", "inspect", container_name,
                "--format", "{{json .Mounts}}"
            ]
            result = subprocess.run(
                inspect_cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                all_mounts = json.loads(result.stdout)
                for mount in all_mounts:
                    if mount.get("Destination") == container_path_str:
                        host_path = mount.get("Source")
                        logger.info(f"✓ Got host path from docker inspect: {host_path}")
                        return host_path
        except Exception as e:
            logger.warning(f"docker inspect failed: {e}")

        # 优先级 2: 从其他挂载点推断
        try:
            inspect_cmd = [
                "docker", "inspect", container_name,
                "--format", "{{json .Mounts}}"
            ]
            result = subprocess.run(
                inspect_cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                all_mounts = json.loads(result.stdout)
                for mount in all_mounts:
                    destination = mount.get("Destination")
                    if destination in ["/app/uploads", "/app/outputs"]:
                        # 从 uploads 或 outputs 推断项目根目录
                        source = Path(mount.get("Source"))
                        project_root = source.parent.parent
                        inferred_path = project_root / "ne301"
                        if inferred_path.exists():
                            logger.info(f"✓ Inferred host path: {inferred_path}")
                            return str(inferred_path)
        except Exception as e:
            logger.warning(f"Path inference failed: {e}")

        # 优先级 3: 从 /proc/mounts 读取
        try:
            with open("/proc/mounts", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == container_path_str:
                        host_path = parts[0]
                        logger.info(f"✓ Got host path from /proc/mounts: {host_path}")
                        return host_path
        except Exception as e:
            logger.warning(f"Failed to read /proc/mounts: {e}")

        # 优先级 4: 使用环境变量（最后手段）
        host_path = os.environ.get("NE301_HOST_PATH")
        if host_path:
            logger.info(f"✓ Got host path from env var: {host_path}")
            return host_path

        logger.error(f"✗ Failed to get host path for: {container_path_str}")
        return None

    def convert_model(
        self,
        task_id: str,
        model_path: str,
        config: Dict[str, Any],
        calib_dataset_path: Optional[str] = None,
        yaml_path: Optional[str] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> str:
        """完整转换流程：PyTorch → TFLite → 量化 TFLite → NE301 .bin

        参考 AIToolStack 的实现方式

        Args:
            task_id: 任务 ID
            model_path: PyTorch 模型路径
            config: 转换配置
            calib_dataset_path: 校准数据集路径
            yaml_path: YAML 文件路径
            progress_callback: 进度回调函数

        Returns:
            NE301 .bin 文件路径
        """
        if not self.client:
            raise RuntimeError("Docker client not available")

        logger.info(f"开始任务 {task_id} 的转换流程")

        try:
            # 步骤 1: PyTorch → TFLite (0-30%)
            if progress_callback:
                progress_callback(10, "正在导出 TFLite 模型...")

            tflite_path = self._export_tflite(
                model_path,
                config["input_size"]
            )
            logger.info(f"✅ TFLite 导出成功: {tflite_path}")

            # 步骤 2: TFLite → 量化 TFLite (30-60%)
            if progress_callback:
                progress_callback(35, "正在量化模型...")

            quantized_tflite = self._quantize_tflite(
                tflite_path,
                config["input_size"],
                calib_dataset_path,
                config
            )
            logger.info(f"✅ 量化成功: {quantized_tflite}")

            # 步骤 3: 准备 NE301 项目 (60-70%)
            if progress_callback:
                progress_callback(70, "正在准备 NE301 项目...")

            ne301_project = self._prepare_ne301_project(
                task_id,
                quantized_tflite,
                config
            )

            # 步骤 4: NE301 打包 (70-100%)
            if progress_callback:
                progress_callback(75, "正在生成 NE301 部署包...")

            bin_path = self._build_ne301_model(
                task_id,
                ne301_project,
                quantized_tflite  # ✅ 传递量化文件路径作为备选
            )

            if progress_callback:
                progress_callback(100, "转换完成!")

            logger.info(f"✅ 转换成功: {bin_path}")
            return bin_path

        except Exception as e:
            logger.error(f"转换失败: {e}")
            raise

    def _export_tflite(self, model_path: str, input_size: int) -> str:
        """步骤 1: PyTorch → SavedModel（用于后续量化）"""
        from ultralytics import YOLO

        logger.info(f"步骤 1: 导出 {model_path} 为 SavedModel 格式（用于量化）")

        model = YOLO(model_path)
        # ✅ 修复：导出为 SavedModel 格式（量化脚本需要 SavedModel，不是 TFLite）
        saved_model_path = model.export(format="saved_model", imgsz=input_size, int8=False)

        # ✅ model.export() 返回字符串路径
        if isinstance(saved_model_path, str) and Path(saved_model_path).exists():
            logger.info(f"✅ SavedModel 导出成功: {saved_model_path}")
            return saved_model_path
        else:
            raise FileNotFoundError(f"SavedModel 导出失败：文件未生成或路径无效 ({saved_model_path})")

    def _quantize_tflite(
        self,
        tflite_path: str,
        input_size: int,
        calib_dataset_path: Optional[str],
        config: Dict[str, Any]
    ) -> str:
        """步骤 2: TFLite → 量化 TFLite

        使用 Hydra 配置，参考 AIToolStack 的 tflite_quant.py
        """
        logger.info(f"步骤 2: 量化 {tflite_path}")

        import tempfile
        import yaml
        import zipfile
        from omegaconf import OmegaConf, DictConfig

        # 处理校准数据集：如果是 ZIP 文件，需要解压
        actual_calib_path = calib_dataset_path or ""
        if calib_dataset_path and calib_dataset_path.endswith('.zip'):
            logger.info(f"检测到校准数据集是 ZIP 文件，正在解压...")

            # 创建临时目录
            extract_dir = tempfile.mkdtemp(prefix="calibration_")

            try:
                with zipfile.ZipFile(calib_dataset_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)

                logger.info(f"✅ 校准数据集已解压到: {extract_dir}")

                # 查找解压后的目录（可能包含子目录）
                # 优先使用包含图片文件的直接目录
                for root, dirs, files in os.walk(extract_dir):
                    image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                    if image_files:
                        actual_calib_path = root
                        logger.info(f"✅ 找到校准图片目录: {actual_calib_path} (包含 {len(image_files)} 张图片)")
                        break

                if not actual_calib_path or actual_calib_path == calib_dataset_path:
                    logger.error(f"解压后未找到有效的校准图片")
                    actual_calib_path = extract_dir
            except Exception as e:
                logger.error(f"解压校准数据集失败: {e}")
                raise RuntimeError(f"解压校准数据集失败: {e}")

        # 准备 Hydra 配置
        hydra_config = {
            "model": {
                "model_path": str(Path(tflite_path).resolve()),
                "input_shape": [input_size, input_size, 3]
            },
            "quantization": {
                "calib_dataset_path": actual_calib_path,
                "export_path": "/app/outputs",
                "fake": not bool(actual_calib_path)  # 如果没有校准数据集，使用 fake quantization
            }
        }

        # 写入临时配置文件
        config_file = tempfile.mktemp(suffix=".yaml", prefix="quant_config_")
        with open(config_file, "w") as f:
            yaml.dump(hydra_config, f)

        # 执行量化脚本
        # 修复：当前工作目录是 /app，Python 模块路径从 tools 开始
        cmd = [
            "python", "-m", "tools.quantization.tflite_quant",
            "--config-name", "user_config_quant",
            f"model.model_path={hydra_config['model']['model_path']}",
            f"model.input_shape=[{input_size},{input_size},3]",
            f"quantization.calib_dataset_path={hydra_config['quantization']['calib_dataset_path']}",
            f"quantization.export_path={hydra_config['quantization']['export_path']}"
        ]

        logger.info(f"执行量化命令: {' '.join(cmd)}")

        # 设置环境变量以获取详细错误信息
        env = os.environ.copy()
        env["HYDRA_FULL_ERROR"] = "1"

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            env=env
        )

        if result.returncode != 0:
            logger.error(f"量化失败: {result.stderr}")
            raise RuntimeError(f"TFLite 量化失败: {result.stderr}")

        # 查找量化后的模型
        quantized_files = list(Path("/app/outputs").glob("*.tflite"))
        if not quantized_files:
            raise FileNotFoundError("量化后的模型文件未找到")

        return str(quantized_files[0])

    def _prepare_ne301_project(
        self,
        task_id: str,
        quantized_tflite: str,
        config: Dict[str, Any]
    ) -> Path:
        """步骤 3: 准备 NE301 项目目录

        参考 AIToolStack 的 ne301_export.py
        """
        logger.info("步骤 3: 准备 NE301 项目")

        # 确保 NE301 项目目录存在
        ne301_project = self.ne301_project_path
        ne301_project.mkdir(parents=True, exist_ok=True)

        # 创建 Model 目录结构
        model_dir = ne301_project / "Model" / "weights"
        model_dir.mkdir(parents=True, exist_ok=True)

        # 复制 TFLite 模型
        model_name = f"model_{task_id}"
        tflite_target = model_dir / f"{model_name}.tflite"
        shutil.copy2(quantized_tflite, tflite_target)

        # 生成 JSON 配置
        json_config = {
            "input_size": config["input_size"],
            "num_classes": config["num_classes"],
            "model_type": config["model_type"],
            "quantization": config.get("quantization", "int8")
        }

        json_file = model_dir / f"{model_name}.json"
        with open(json_file, "w") as f:
            json.dump(json_config, f, indent=2)

        logger.info(f"✅ NE301 项目准备完成: {ne301_project}")
        return ne301_project

    def _build_ne301_model(
        self,
        task_id: str,
        ne301_project_path: Path,
        quantized_tflite: str
    ) -> str:
        """步骤 4: 调用 NE301 容器打包（改进版 - 架构感知）

        参考 AIToolStack 的 _build_with_docker() 实现

        Args:
            task_id: 任务 ID
            ne301_project_path: NE301 项目路径
            quantized_tflite: 量化 TFLite 文件路径（备选输出）

        Returns:
            NE301 .bin 文件路径 或 量化 TFLite 文件路径

        Raises:
            RuntimeError: 如果打包失败且备选输出也不可用
        """
        logger.info(f"步骤 4: 调用 NE301 容器打包")

        # 检测主机架构
        import platform
        host_arch = platform.machine()
        is_arm64 = host_arch.lower() in ('arm64', 'aarch64')

        if is_arm64:
            logger.warning("⚠️  检测到 ARM64 架构（Apple Silicon）")
            logger.warning("⚠️  NE301 容器为 amd64 架构，stedgeai 工具需要 AVX 指令集")
            logger.warning("⚠️  将提供量化 TFLite 文件作为备选输出")
            logger.info("💡 提示：NE301 .bin 打包需要在 x86_64 环境中执行")

            # 直接返回量化 TFLite 文件
            return self._provide_quantized_tflite_output(task_id, quantized_tflite)

        # x86_64 环境：尝试 NE301 打包
        try:
            return self._attempt_ne301_build(task_id, ne301_project_path, quantized_tflite)
        except RuntimeError as e:
            logger.error(f"❌ NE301 打包失败: {e}")
            logger.info("📦 提供量化 TFLite 作为备选输出...")
            return self._provide_quantized_tflite_output(task_id, quantized_tflite)

    def _attempt_ne301_build(
        self,
        task_id: str,
        ne301_project_path: Path,
        quantized_tflite: str
    ) -> str:
        """尝试 NE301 打包（仅在 x86_64 环境）

        Args:
            task_id: 任务 ID
            ne301_project_path: NE301 项目路径
            quantized_tflite: 量化 TFLite 文件路径

        Returns:
            NE301 .bin 文件路径

        Raises:
            RuntimeError: 如果打包失败
        """
        model_name = f"model_{task_id}"

        # ✅ 获取宿主机路径（关键改进）
        host_path = self._get_host_path(Path("/workspace/ne301"))

        if not host_path:
            raise RuntimeError(
                "❌ 无法获取宿主机路径！\n"
                "请检查：\n"
                "1. docker-compose.yml 中是否配置了 ./ne301:/workspace/ne301\n"
                f"2. CONTAINER_NAME 环境变量是否正确（当前: {os.environ.get('CONTAINER_NAME', '未设置')}）\n"
                "3. Docker 套接字是否正确挂载\n"
                "调试命令：docker inspect model-converter-api | jq '.[0].Mounts'"
            )

        logger.info(f"✓ 使用宿主机路径: {host_path}")

        # 构造 Docker 命令（使用宿主机路径）
        docker_cmd = [
            "docker", "run", "--rm",
            "-v", f"{host_path}:/workspace/ne301",  # ✅ 宿主机路径
            "-w", "/workspace/ne301",
            self.ne301_image,
            "bash", "-c",
            f"cd /workspace/ne301 && "
            f"if [ ! -f Model/weights/{model_name}.tflite ]; then "
            f"  echo '❌ Model file not found'; exit 1; "
            f"fi && "
            f"echo '✓ Starting NE301 build...' && "
            f"make model && "
            f"make pkg-model && "
            f"echo '✓ Package created'"
        ]

        logger.info(f"执行 NE301 打包命令...")

        # 执行命令并实时输出日志
        process = subprocess.Popen(
            docker_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # 实时输出日志
        output_lines = []
        for line in process.stdout:
            line = line.strip()
            output_lines.append(line)
            logger.info(f"[NE301] {line}")

        process.wait(timeout=600)

        if process.returncode != 0:
            error_output = "\n".join(output_lines[-50:])  # 最后 50 行
            raise RuntimeError(f"❌ NE301 打包失败:\n{error_output}")

        # 查找生成的 .bin 文件
        bin_files = list(ne301_project_path.glob("build/*.bin"))
        if not bin_files:
            # 如果 build 目录中没有，查找整个项目
            bin_files = list(ne301_project_path.rglob("*.bin"))

        if not bin_files:
            raise FileNotFoundError("❌ NE301 .bin 文件未生成")

        # 复制到输出目录
        output_dir = Path("/app/outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        final_bin_path = output_dir / f"ne301_model_{task_id}.bin"
        shutil.copy2(bin_files[0], final_bin_path)

        logger.info(f"✅ NE301 打包成功: {final_bin_path}")
        return str(final_bin_path)

    def _provide_quantized_tflite_output(
        self,
        task_id: str,
        quantized_tflite: str
    ) -> str:
        """提供量化 TFLite 文件作为备选输出

        Args:
            task_id: 任务 ID
            quantized_tflite: 量化 TFLite 文件路径

        Returns:
            量化 TFLite 文件路径（在输出目录中）
        """
        logger.info("📦 准备量化 TFLite 输出...")

        # 检查量化文件是否存在
        tflite_path = Path(quantized_tflite)
        if not tflite_path.exists():
            raise FileNotFoundError(f"量化 TFLite 文件未找到: {quantized_tflite}")

        # 复制到输出目录
        output_dir = Path("/app/outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        final_tflite_path = output_dir / f"quantized_model_{task_id}.tflite"
        shutil.copy2(tflite_path, final_tflite_path)

        logger.info(f"✅ 量化 TFLite 已生成: {final_tflite_path}")
        logger.warning("⚠️  注意：此文件为量化 TFLite 格式，不是 NE301 .bin 格式")
        logger.info("💡 提示：要在 x86_64 环境中完成 NE301 打包，请执行以下步骤：")
        logger.info("   1. 将量化 TFLite 文件传输到 x86_64 服务器")
        logger.info("   2. 在该服务器上运行 NE301 打包命令")
        logger.info("   3. 或使用云服务完成打包（AWS/GCP/Azure x86_64 实例）")

        return str(final_tflite_path)
