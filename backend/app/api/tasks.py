"""
任务 API 路由

查询任务状态和结果，性能监控统计
"""

import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.task_manager import get_task_manager
from app.core.performance_monitor import get_performance_monitor

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


@router.get("/tasks/{task_id}/download")
async def download_task_output(task_id: str):
    """
    下载任务输出文件

    Args:
        task_id: 任务 ID

    Returns:
        FileResponse: 输出文件（.bin 或 .tflite）

    Raises:
        HTTPException: 任务不存在或文件不存在时返回 404
    """
    task_manager = get_task_manager()
    task = task_manager.get_task(task_id)

    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"任务不存在: {task_id}"
        )

    if task.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"任务尚未完成，当前状态: {task.status}"
        )

    if not task.output_filename:
        raise HTTPException(
            status_code=404,
            detail="任务输出文件不存在"
        )

    # 构造文件路径
    output_path = Path(task.output_filename)

    if not output_path.exists():
        logger.error(f"输出文件不存在: {output_path}")
        raise HTTPException(
            status_code=404,
            detail=f"输出文件不存在: {output_path.name}"
        )

    # 确定文件类型和下载名称
    filename = output_path.name
    media_type = "application/octet-stream"

    if filename.endswith('.tflite'):
        media_type = "application/x-tflite"
    elif filename.endswith('.bin'):
        media_type = "application/x-binary"

    logger.info(f"下载文件: {filename} ({output_path.stat().st_size} bytes)")

    return FileResponse(
        path=str(output_path),
        filename=filename,
        media_type=media_type
    )


@router.get("/stats/performance")
async def get_performance_stats():
    """
    获取性能统计信息

    Returns:
        Dict: 性能统计数据
    """
    performance_monitor = get_performance_monitor()
    stats = performance_monitor.get_aggregate_stats()

    logger.info(f"查询性能统计: {stats['total_tasks']} 个任务")

    return stats


@router.get("/stats/tasks")
async def get_task_stats():
    """
    获取任务统计信息

    Returns:
        Dict: 任务统计数据
    """
    task_manager = get_task_manager()
    stats = task_manager.get_stats()

    logger.info(f"查询任务统计: {stats['total_tasks']} 个任务")

    return stats


@router.get("/stats/overview")
async def get_overview_stats():
    """
    获取综合统计概览

    Returns:
        Dict: 综合统计数据
    """
    task_manager = get_task_manager()
    performance_monitor = get_performance_monitor()

    task_stats = task_manager.get_stats()
    perf_stats = performance_monitor.get_aggregate_stats()

    return {
        "tasks": task_stats,
        "performance": perf_stats,
        "timestamp": datetime.now().isoformat()
    }


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """
    删除任务

    Args:
        task_id: 任务 ID

    Returns:
        Dict: 删除结果

    Raises:
        HTTPException: 任务不存在时返回 404
    """
    task_manager = get_task_manager()

    if task_id not in task_manager.tasks:
        raise HTTPException(
            status_code=404,
            detail=f"任务不存在: {task_id}"
        )

    del task_manager.tasks[task_id]
    logger.info(f"删除任务: {task_id}")

    return {"message": "任务已删除", "task_id": task_id}


@router.post("/tasks/cleanup")
async def cleanup_old_tasks(max_age_hours: int = 24):
    """
    清理过期任务

    Args:
        max_age_hours: 最大任务保留时间（小时）

    Returns:
        Dict: 清理结果
    """
    task_manager = get_task_manager()

    tasks_cleaned = task_manager.cleanup_old_tasks(max_age_hours)

    logger.info(f"清理过期任务: {tasks_cleaned} 个任务")

    return {
        "tasks_cleaned": tasks_cleaned,
        "max_age_hours": max_age_hours
    }


from datetime import datetime
