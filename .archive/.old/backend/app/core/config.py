"""
应用配置模块
使用 Pydantic Settings 进行类型安全的配置管理
"""
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API 配置
    API_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # CORS 配置
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"]
    )

    # 文件存储配置
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB
    TEMP_DIR: str = "./temp"
    OUTPUT_DIR: str = "./outputs"

    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    # Celery 配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_TIMEOUT: int = 1800  # 30 分钟
    CELERY_TASK_SOFT_TIMEOUT: int = 1500  # 25 分钟

    # 任务配置
    MAX_CONCURRENT_TASKS: int = 3
    TASK_CLEANUP_HOURS: int = 24  # 24 小时后清理旧任务文件

    # 模型转换配置
    DEFAULT_CALIBRATION_DATASET: str = "coco8"
    STEDGEAI_PATH: str = "/opt/st/stedgeai"

    # NE301 项目路径（用于调用现有脚本）
    NE301_PROJECT_PATH: str = "/workspace"

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json 或 console

    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALLOWED_MODEL_EXTENSIONS: List[str] = [".pt", ".pth", ".onnx"]


# 全局配置实例
settings = Settings()
