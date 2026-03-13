"""
Celery 应用配置
使用 Redis 作为消息代理和结果后端
"""
from celery import Celery
import os

# Redis 配置
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

# 创建 Celery 应用
celery_app = Celery(
    "model_converter",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.workers.conversion_tasks",
    ]
)

# Celery 配置
celery_app.conf.update(
    # 任务结果过期时间（1小时）
    result_expires=3600,
    # 任务执行时间限制（30分钟）
    task_time_limit=1800,
    # 任务软时间限制（25分钟，留出5分钟清理）
    task_soft_time_limit=1500,
    # 接受的序列化格式
    accept_content=["json"],
    task_serializer="json",
    result_serializer="json",
    # 时区
    timezone="UTC",
    enable_utc=True,
    # 任务结果追踪
    task_track_started=True,
    # Worker 配置
    worker_prefetch_multiplier=1,  # 一次只处理一个任务
    worker_max_tasks_per_child=10,  # 防止内存泄漏，每处理10个任务重启worker
)
