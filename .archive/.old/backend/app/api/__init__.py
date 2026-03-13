"""
API 路由模块
整合所有 API 端点
"""
from fastapi import APIRouter

from app.api import models, presets, tasks

api_router = APIRouter()

# 注册各个模块的路由
api_router.include_router(
    models.router, prefix="/models", tags=["模型转换"]
)
api_router.include_router(
    presets.router, prefix="/presets", tags=["配置预设"]
)
api_router.include_router(
    tasks.router, prefix="/tasks", tags=["任务管理"]
)
