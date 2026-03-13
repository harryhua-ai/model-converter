"""
模型转换 API 端点
处理模型上传和转换任务（使用 Celery 后台任务）
"""
import os
import uuid
import shutil
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import structlog

from app.models.schemas import (
    ModelUploadResponse,
    ConversionConfig,
    TaskStatus,
)
from app.services.task_manager import get_task_manager
from app.core.config import settings

router = APIRouter()
logger = structlog.get_logger(__name__)

# 初始化任务管理器
task_manager = get_task_manager()


@router.post("/upload", response_model=ModelUploadResponse)
async def upload_model(
    file: Annotated[UploadFile, File(description="PyTorch 模型文件 (.pt, .pth, .onnx)")],
    calibration_dataset: Annotated[
        UploadFile | None,
        File(description="校准数据集 ZIP 文件 (可选, INT8量化推荐)")
    ] = None,
    class_yaml: Annotated[
        UploadFile | None,
        File(description="类别配置 YAML 文件 (data.yaml, 可选)")
    ] = None,
    config: str = Form(...),
) -> ModelUploadResponse:
    """
    上传 PyTorch 模型文件并启动转换任务
    """
    import json as json_module

    # 解析 config JSON
    try:
        config_dict = json_module.loads(config)
        conversion_config = ConversionConfig(**config_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"配置格式错误: {str(e)}")

    # 验证文件扩展名
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    if file_ext not in settings.ALLOWED_MODEL_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式。支持的格式: {', '.join(settings.ALLOWED_MODEL_EXTENSIONS)}",
        )

    # 生成任务 ID
    task_id = str(uuid.uuid4())
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # 保存模型文件 (Streaming)
    upload_path = os.path.join(settings.UPLOAD_DIR, f"{task_id}_{file.filename}")
    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Get file size after writing to disk to avoid reading it into memory
    file_size = os.path.getsize(upload_path)
    if file_size > settings.MAX_UPLOAD_SIZE:
        os.remove(upload_path)
        raise HTTPException(
            status_code=400,
            detail=f"文件过大。最大允许 {settings.MAX_UPLOAD_SIZE // (1024*1024)} MB",
        )

    # 处理校准数据集文件
    calibration_path = None
    if calibration_dataset:
        calib_ext = os.path.splitext(calibration_dataset.filename or "")[1].lower()
        if calib_ext != ".zip":
            raise HTTPException(status_code=400, detail="校准数据集必须是 ZIP 格式")

        calibration_path = os.path.join(
            settings.UPLOAD_DIR, f"{task_id}_{calibration_dataset.filename}"
        )
        with open(calibration_path, "wb") as f:
            shutil.copyfileobj(calibration_dataset.file, f)

        conversion_config.use_custom_calibration = True
        conversion_config.calibration_dataset_filename = calibration_dataset.filename

    # 处理 class_yaml 文件
    class_yaml_path = None
    if class_yaml:
        yaml_ext = os.path.splitext(class_yaml.filename or "")[1].lower()
        if yaml_ext not in [".yaml", ".yml"]:
            raise HTTPException(status_code=400, detail="类别配置文件必须是 YAML 格式")

        # class_yaml usually tiny, ok to read once
        yaml_content = await class_yaml.read()
        class_yaml_path = os.path.join(
            settings.UPLOAD_DIR, f"{task_id}_data.yaml"
        )
        with open(class_yaml_path, "wb") as f:
            f.write(yaml_content)

        # 从 YAML 解析类别数量和类别名
        try:
            import yaml
            yaml_data = yaml.safe_load(yaml_content.decode("utf-8"))
            if "nc" in yaml_data:
                conversion_config.num_classes = yaml_data["nc"]
            if "names" in yaml_data and isinstance(yaml_data["names"], list):
                conversion_config.class_names = yaml_data["names"]
        except Exception as e:
            logger.warning("解析 data.yaml 失败，使用默认配置", error=str(e))

    logger.info(
        "收到模型上传请求",
        task_id=task_id,
        filename=file.filename,
        file_size=file_size,
        has_calibration=calibration_path is not None,
        has_class_yaml=class_yaml_path is not None,
        num_classes=conversion_config.num_classes,
    )

    # 创建任务（使用 await）
    task = await task_manager.create_task(
        task_id=task_id,
        config=conversion_config,
        filename=file.filename or "unknown",
    )

    # 启动 Celery 后台转换任务
    from app.workers.conversion_tasks import convert_model_task

    # 将配置转换为字典（避免序列化问题）
    config_dict = conversion_config.model_dump()

    # 提交任务到 Celery（异步执行，不阻塞 API）
    celery_task = convert_model_task.apply_async(
        args=[
            task_id,
            upload_path,
            config_dict,
        ],
        kwargs={
            "calibration_dataset_path": calibration_path,
            "class_yaml_path": class_yaml_path,
        },
        task_id=task_id,  # 使用我们的 task_id 作为 Celery task_id
    )

    logger.info(
        "Celery 任务已提交",
        task_id=task_id,
        celery_task_id=celery_task.id,
    )

    # 立即返回任务信息（不等待转换完成）
    return ModelUploadResponse(
        task_id=task_id,
        filename=file.filename or "unknown",
        file_size=file_size,
        config=conversion_config,
    )


@router.get("/download/{task_id}")
async def download_model(task_id: str) -> FileResponse:
    """
    下载转换后的模型文件 (ZIP 包)
    """
    task = await task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"任务未完成。当前状态: {task.status.value}",
        )

    if not task.output_filename:
        raise HTTPException(status_code=400, detail="输出文件不存在")

    output_path = os.path.join(settings.OUTPUT_DIR, task.output_filename)
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=output_path,
        filename=task.output_filename,
        media_type="application/zip",
    )
