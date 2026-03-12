"""
FastAPI 主应用程序

提供 Web API 和 WebSocket 服务
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("=" * 60)
    logger.info("Model Converter API 启动中...")
    logger.info("=" * 60)

    # 检查环境状态
    from app.core.environment import EnvironmentDetector
    detector = EnvironmentDetector()
    status = detector.check()

    logger.info(f"环境状态: {status.status}")
    logger.info(f"运行模式: {status.mode}")
    logger.info(f"详细信息: {status.message}")

    logger.info("=" * 60)
    logger.info("Model Converter API 已就绪")
    logger.info("=" * 60)

    yield

    # 关闭时执行
    logger.info("Model Converter API 正在关闭...")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    app = FastAPI(
        title="Model Converter API",
        description="PyTorch 模型转换为 ONNX 格式的 Web 服务",
        version="1.0.0",
        lifespan=lifespan
    )

    # 配置 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应限制具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    _register_routes(app)

    # 配置静态文件服务
    _configure_static_files(app)

    return app


def _register_routes(app: FastAPI):
    """注册所有路由"""
    from app.api import convert, setup, tasks, websocket

    app.include_router(convert.router, prefix="/api", tags=["转换"])
    app.include_router(setup.router, prefix="/api", tags=["设置"])
    app.include_router(tasks.router, prefix="/api", tags=["任务"])
    app.include_router(websocket.router, tags=["WebSocket"])

    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """健康检查端点"""
        return {"status": "healthy", "service": "model-converter"}


def _configure_static_files(app: FastAPI):
    """配置静态文件服务"""
    import os
    frontend_path = os.path.join(os.path.dirname(__file__), "../../frontend/dist")

    if os.path.exists(frontend_path):
        app.mount("/static", StaticFiles(directory=frontend_path), name="static")
        logger.info(f"静态文件服务已启用: {frontend_path}")
    else:
        logger.warning(f"前端构建目录不存在: {frontend_path}")


# 创建应用实例
app = create_app()
