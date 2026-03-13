"""
FastAPI 主应用程序

提供 Web API 和 WebSocket 服务
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import sys

# 🔧 配置日志输出到 stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("=" * 60)
    logger.info("Model Converter API 启动中...")
    logger.info("=" * 60)

    # 验证配置加载
    from .core.config import settings
    logger.info(f"✅ 配置已加载")
    logger.info(f"   - API: {settings.HOST}:{settings.PORT}{settings.API_PREFIX}")
    logger.info(f"   - Docker: {settings.NE301_DOCKER_IMAGE}")
    logger.info(f"   - 日志级别: {settings.LOG_LEVEL}")

    # 检查环境状态
    from .core.environment import EnvironmentDetector
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

    # 先注册路由（避免被静态文件覆盖）
    _register_routes(app)

    # 后配置静态文件（支持 SPA 路由）
    _configure_static_files(app)

    return app


def _register_routes(app: FastAPI):
    """注册所有路由"""
    from .api import convert, setup, tasks, websocket

    app.include_router(convert.router, prefix="/api", tags=["转换"])
    app.include_router(setup.router, prefix="/api", tags=["设置"])
    app.include_router(tasks.router, prefix="/api", tags=["任务"])
    app.include_router(websocket.router, prefix="/api", tags=["WebSocket"])

    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """健康检查端点"""
        return {"status": "healthy", "service": "model-converter"}


def _configure_static_files(app: FastAPI):
    """配置静态文件服务"""
    from pathlib import Path
    import os

    # 获取应用根目录（Docker 容器中为 /app）
    # __file__ = /app/app/main.py -> parent = /app/app -> parent = /app
    app_root = Path(__file__).parent.parent
    frontend_path = app_root / "frontend" / "dist"

    logger.info(f"查找前端路径: {frontend_path}")
    logger.info(f"路径存在? {frontend_path.exists()}")

    if frontend_path.exists():
        # 挂载到根路径，支持 SPA 路由
        app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
        logger.info(f"✅ 静态文件服务已启用: {frontend_path}")
    else:
        logger.warning(f"❌ 前端构建目录不存在: {frontend_path}")


# 创建应用实例
app = create_app()
