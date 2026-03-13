"""
Celery Worker 入口文件
启动命令：celery -A app.worker worker --loglevel=info --concurrency=1
"""
from app.celery_app import celery_app

__all__ = ["celery_app"]
