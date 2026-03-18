"""
应用配置管理

使用 pydantic-settings 从环境变量和 .env 文件加载配置

安全修复: HIGH-2026-005 - CORS 配置管理
- 从环境变量读取允许的域名列表
- 开发环境默认允许 localhost
- 生产环境必须显式配置
"""

from typing import List, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    # API 配置
    API_PREFIX: str = "/api"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # Docker 配置
    NE301_DOCKER_IMAGE: str = "camthink/ne301-dev:latest"  # NE301 Docker 镜像名称
    NE301_PROJECT_PATH: str = "/workspace"  # 容器内 NE301 项目路径（命名卷挂载点）
    CONTAINER_NAME: str = "model-converter-api"  # Docker 容器名称

    # 文件路径配置
    UPLOAD_DIR: str = "./uploads"
    TEMP_DIR: str = "./temp"
    OUTPUT_DIR: str = "./outputs"
    MAX_UPLOAD_SIZE: int = 524288000  # 500MB

    # 日志配置
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "DEBUG"

    # 安全修复: HIGH-2026-005 - CORS 配置
    # 允许的跨域来源列表（逗号分隔）
    # 开发环境默认: "http://localhost:3000,http://localhost:8000"
    # 生产环境: 必须显式配置，如 "https://example.com,https://www.example.com"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000,http://localhost:5173"

    def get_cors_origins(self) -> List[str]:
        """获取 CORS 允许的域名列表

        安全修复: HIGH-2026-005

        Returns:
            List[str]: 允许的域名列表

        注意:
            - 开发环境（DEBUG=True）: 允许所有 localhost
            - 生产环境（DEBUG=False）: 必须显式配置
        """
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

        # 开发环境：自动添加常见本地端口
        if self.DEBUG:
            local_origins = [
                "http://localhost",
                "http://localhost:3000",
                "http://localhost:5173",  # Vite 默认端口
                "http://localhost:8000",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:8000",
            ]
            # 合并并去重
            origins = list(set(origins + local_origins))
            logger = __import__("logging").getLogger(__name__)
            logger.warning(f"⚠️ 开发模式: CORS 允许本地来源: {origins}")
        else:
            # 生产环境：使用显式配置
            if not origins or origins == ["*"]:
                raise ValueError(
                    "生产环境必须显式配置 CORS_ORIGINS 环境变量！"
                    "例如: CORS_ORIGINS=https://example.com,https://www.example.com"
                )
            logger = __import__("logging").getLogger(__name__)
            logger.info(f"✅ 生产模式: CORS 允许的来源: {origins}")

        return origins

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


# 全局配置实例
settings = Settings()
