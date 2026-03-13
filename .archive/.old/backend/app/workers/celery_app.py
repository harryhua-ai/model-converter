"""
Celery Worker 配置
"""
from celery import Celery

from app.core.config import settings

# 创建 Celery 应用
celery_app = Celery(
    "ne301_model_converter",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery 配置
celery_app.conf.update(
    # 任务相关
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,

    # 任务超时
    task_time_limit=settings.CELERY_TASK_TIMEOUT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIMEOUT,

    # 任务结果
    result_expires=3600,  # 1 小时
    result_extended=True,

    # 任务路由
    task_routes={
        "app.services.conversion.convert_model": {"queue": "conversion"},
    },

    # Worker 配置
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,

    # 任务重试
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)
