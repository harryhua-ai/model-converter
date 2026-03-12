"""
任务 API 路由

查询任务状态和结果
"""

import logging
from fastapi import APIRouter, HTTPException

from app.core.task_manager import get_task_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    获取任务状态

    Args:
        task_id: 任务 ID

    Returns:
        ConversionTask: 任务详细信息

    Raises:
        HTTPException: 任务不存在时返回 404
    """
    task_manager = get_task_manager()
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"任务不存在: {task_id}"
        )
    
    logger.info(f"查询任务状态: {task_id} - {task.status}")
    
    # FastAPI 会自动序列化 Pydantic 模型
    return task


@router.get("/tasks")
async def list_tasks():
    """
    列出所有任务

    Returns:
        List[ConversionTask]: 所有任务的列表
    """
    task_manager = get_task_manager()
    tasks = list(task_manager.tasks.values())
    
    logger.info(f"列出所有任务: 共 {len(tasks)} 个")
    
    return tasks
