"""
NE301 模型转换核心逻辑

Docker 化架构：
- 所有步骤都在 Docker 容器中执行
- 宿主机只负责文件管理和进度通知
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class ModelConverter:
    """模型转换器 - PyTorch → NE301 .bin (全 Docker 化)"""

    def __init__(self, work_dir: Optional[Path] = None):
        """
        初始化转换器

        Args:
            work_dir: 工作目录，默认为 temp/converter/
        """
        self.work_dir = work_dir or Path("temp/converter")
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def convert(
        self,
        model_path: str,
        config: Dict[str, Any],
        calib_dataset_path: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> str:
        """
        完整转换流程：PyTorch → TFLite → 量化 → NE301 .bin

        所有步骤在 Docker 容器中执行

        Args:
            model_path: PyTorch 模型路径 (.pt/.pth)
            config: 转换配置
            calib_dataset_path: 校准数据集路径（可选）
            progress_callback: 进度回调函数

        Returns:
            NE301 .bin 文件路径
        """
        task_id = config.get("task_id", "unknown")

        # 所有转换步骤在 Docker 容器中执行
        from .docker_adapter import DockerToolChainAdapter

        docker = DockerToolChainAdapter()

        # 检查 Docker 可用性
        available, error = docker.check_docker()
        if not available:
            raise RuntimeError(f"Docker 不可用: {error}")

        # 检查镜像
        if not docker.check_image():
            logger.info("Docker 镜像不存在，开始拉取...")
            if progress_callback:
                progress_callback(5, "正在拉取 Docker 镜像...")

            success = docker.pull_image(
                progress_callback=lambda p: progress_callback(5 + p // 20, "正在拉取 Docker 镜像...") if progress_callback else None
            )

            if not success:
                raise RuntimeError("Docker 镜像拉取失败")

            if progress_callback:
                progress_callback(10, "Docker 镜像准备完成")

        # 执行完整转换流程
        if progress_callback:
            progress_callback(15, "开始模型转换...")

        bin_path = docker.convert_model(
            task_id=task_id,
            model_path=model_path,
            config=config,
            calib_dataset_path=calib_dataset_path,
            yaml_path=config.get("yaml_path"),
            progress_callback=lambda p, msg: progress_callback(15 + p * 0.7, msg) if progress_callback else None
        )

        if progress_callback:
            progress_callback(100, "转换完成!")

        return bin_path
