"""
转换 API 路由

处理模型转换请求
"""

import json
import logging
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse

from app.models.schemas import ConversionConfig, ClassDefinition
from app.core.task_manager import get_task_manager

router = APIRouter()
logger = logging.getLogger(__name__)

# 允许的文件扩展名
ALLOWED_MODEL_EXTENSIONS = {".pt", ".pth", ".onnx"}
ALLOWED_CONFIG_EXTENSIONS = {".json"}
ALLOWED_YAML_EXTENSIONS = {".yaml", ".yml"}


def _validate_file_extension(filename: str, allowed_extensions: set[str]) -> bool:
    """验证文件扩展名"""
    _, ext = os.path.splitext(filename)
    return ext.lower() in allowed_extensions


@router.post("/convert")
async def convert_model(
    background_tasks: BackgroundTasks,
    model_file: UploadFile = File(...),
    config_file: UploadFile = File(...),
    yaml_file: Optional[UploadFile] = File(None)
):
    """
    启动模型转换任务

    Args:
        model_file: PyTorch 模型文件 (.pt, .pth, .onnx)
        config_file: 转换配置 JSON 文件
        yaml_file: (可选) 类别定义 YAML 文件

    Returns:
        JSONResponse: 包含 task_id 的响应
    """
    # 1. 验证模型文件
    if not _validate_file_extension(model_file.filename, ALLOWED_MODEL_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的模型文件格式。允许的格式: {', '.join(ALLOWED_MODEL_EXTENSIONS)}"
        )

    # 2. 验证配置文件
    if not _validate_file_extension(config_file.filename, ALLOWED_CONFIG_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"配置文件必须是 JSON 格式"
        )

    # 3. 验证 YAML 文件(如果提供)
    if yaml_file and not _validate_file_extension(yaml_file.filename, ALLOWED_YAML_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"YAML 文件格式无效。允许的格式: {', '.join(ALLOWED_YAML_EXTENSIONS)}"
        )

    try:
        # 4. 读取并验证配置文件
        config_content = await config_file.read()
        config_dict = json.loads(config_content)
        
        # Pydantic 验证 - 会抛出 ValidationError
        config = ConversionConfig(**config_dict)

        # 5. 读取 YAML 文件(如果提供)
        class_def = None
        if yaml_file:
            yaml_content = await yaml_file.read()
            import yaml
            yaml_data = yaml.safe_load(yaml_content)
            class_def = ClassDefinition(**yaml_data)

        # 6. 保存上传的文件到临时目录
        temp_dir = tempfile.mkdtemp(prefix="model_converter_")

        model_path = os.path.join(temp_dir, model_file.filename)
        with open(model_path, "wb") as f:
            f.write(await model_file.read())

        yaml_path = None
        if yaml_file:
            yaml_path = os.path.join(temp_dir, yaml_file.filename)
            with open(yaml_path, "wb") as f:
                f.write(yaml_content)

        # 7. 创建任务
        task_manager = get_task_manager()
        task_id = task_manager.create_task(config)

        logger.info(f"创建转换任务: {task_id}")
        logger.info(f"模型文件: {model_file.filename}")
        logger.info(f"配置: {config.model_type}, {config.input_size}x{config.input_size}")

        # 8. 启动后台转换任务
        background_tasks.add_task(
            _run_conversion,
            task_id,
            model_path,
            config,
            yaml_path
        )

        return JSONResponse(
            status_code=202,
            content={
                "task_id": task_id,
                "status": "pending",
                "message": "转换任务已创建"
            }
        )

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="配置文件 JSON 格式无效")
    except Exception as e:
        # 检查是否是 Pydantic 验证错误
        from pydantic import ValidationError
        if isinstance(e, ValidationError):
            raise HTTPException(
                status_code=422,
                detail=f"配置验证失败: {str(e)}"
            )
        logger.error(f"创建转换任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


async def _run_conversion(
    task_id: str,
    model_path: str,
    config: ConversionConfig,
    yaml_path: Optional[str] = None
):
    """
    后台执行转换任务

    TODO: 在后续任务中实现实际的 Docker 容器调用
    """
    task_manager = get_task_manager()

    try:
        # 更新任务状态为运行中
        task_manager.update_progress(task_id, 0, "准备转换环境")

        # 模拟转换过程(后续替换为实际的 Docker 调用)
        import asyncio
        for i in range(0, 101, 10):
            await asyncio.sleep(0.1)
            task_manager.update_progress(task_id, i, f"转换中... {i}%")

        # 标记任务完成
        output_filename = f"converted_{os.path.basename(model_path)}.onnx"
        task_manager.complete_task(task_id, output_filename)

        logger.info(f"任务 {task_id} 转换完成")

    except Exception as e:
        logger.error(f"任务 {task_id} 转换失败: {e}")
        task_manager.fail_task(task_id, str(e))
