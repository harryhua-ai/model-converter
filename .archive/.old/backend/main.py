"""
YOLO 模型转换工具 - FastAPI 主应用（简化版）
提供 PyTorch 模型到 NE301 .bin 格式的转换服务
去除 Docker 和 Celery 依赖，直接使用本地异步任务
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.core.config import settings
from app.core.logging import setup_logging
from app.api import api_router


# 配置日志
setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """应用生命周期管理"""
    logger.info("启动 YOLO 模型转换服务")

    # 初始化任务管理器
    from app.services.task_manager import get_task_manager
    task_manager = get_task_manager()
    logger.info("任务管理器已初始化")

    yield

    logger.info("关闭 YOLO 模型转换服务")
    # 清理资源
    task_manager.close()


# 创建 FastAPI 应用
app = FastAPI(
    title="YOLO 模型转换工具",
    description="将 PyTorch YOLO 模型转换为 NE301 设备可用的 .bin 格式",
    version="2.0.0",
    lifespan=lifespan,
)


# CORS 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册 API 路由
app.include_router(api_router, prefix=settings.API_PREFIX)


# 健康检查端点
@app.get("/health")
async def health_check() -> dict:
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "YOLO 模型转换工具",
        "version": "2.0.0",
        "mode": "local (no Docker)",
    }


# 根路径
@app.get("/")
async def root() -> dict:
    """根路径信息"""
    return {
        "message": "YOLO 模型转换工具 API",
        "version": "2.0.0",
        "docs": "/docs",
        "mode": "本地运行模式（无 Docker）",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
