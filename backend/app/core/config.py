"""
应用配置管理

使用 pydantic-settings 从环境变量和 .env 文件加载配置
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    """应用配置"""

    # API 配置
    API_PREFIX: str = "/api"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # Docker 配置
    NE301_DOCKER_IMAGE: str = "camthink/ne301-dev:latest"  # NE301 Docker 镜像名称
    NE301_PROJECT_PATH: str = "/workspace/ne301"  # 容器内 NE301 项目路径
    CONTAINER_NAME: str = "model-converter-api"  # Docker 容器名称

    # 文件路径配置
    UPLOAD_DIR: str = "./uploads"
    TEMP_DIR: str = "./temp"
    OUTPUT_DIR: str = "./outputs"
    MAX_UPLOAD_SIZE: int = 524288000  # 500MB

    # 日志配置
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# 全局配置实例
settings = Settings()
