"""
转换 API 路由

处理模型转换请求
"""

import json
import logging
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Form
from fastapi.responses import JSONResponse

from ..models.schemas import ConversionConfig, ClassDefinition
from ..core.task_manager import get_task_manager

router = APIRouter()
logger = logging.getLogger(__name__)

# 允许的文件扩展名
ALLOWED_MODEL_EXTENSIONS = {".pt", ".pth", ".onnx"}
ALLOWED_CONFIG_EXTENSIONS = {".json"}
ALLOWED_YAML_EXTENSIONS = {".yaml", ".yml"}
ALLOWED_CALIBRATION_EXTENSIONS = {".zip"}


def _validate_file_extension(filename: str, allowed_extensions: set[str]) -> bool:
    """验证文件扩展名"""
    _, ext = os.path.splitext(filename)
    return ext.lower() in allowed_extensions


@router.post("/convert")
async def convert_model(
    background_tasks: BackgroundTasks,
    model_file: UploadFile = File(...),
    config: str = Form(...),
    yaml_file: Optional[UploadFile] = File(None),
    calibration_dataset: Optional[UploadFile] = File(None)
):
    """
    启动模型转换任务

    Args:
        model_file: PyTorch 模型文件 (.pt, .pth, .onnx)
        config: 转换配置 JSON 字符串
        yaml_file: (可选) 类别定义 YAML 文件
        calibration_dataset: (可选) 校准数据集 ZIP 文件 (32-100 张图片)

    Returns:
        JSONResponse: 包含 task_id 的响应
    """
    # 1. 验证模型文件
    if not _validate_file_extension(model_file.filename, ALLOWED_MODEL_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的模型文件格式。允许的格式: {', '.join(ALLOWED_MODEL_EXTENSIONS)}"
        )

    # 2. 解析并验证配置 JSON
    try:
        config_dict = json.loads(config)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="配置格式无效，必须是有效的 JSON 字符串"
        )

    # 3. 验证 YAML 文件(如果提供)
    if yaml_file and not _validate_file_extension(yaml_file.filename, ALLOWED_YAML_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"YAML 文件格式无效。允许的格式: {', '.join(ALLOWED_YAML_EXTENSIONS)}"
        )

    # 3.5 验证校准数据集文件(如果提供)
    if calibration_dataset and not _validate_file_extension(
        calibration_dataset.filename, ALLOWED_CALIBRATION_EXTENSIONS
    ):
        raise HTTPException(
            status_code=400,
            detail=f"校准数据集必须是 ZIP 格式"
        )

    # 3.6 验证校准数据集文件大小 (最大 1GB)
    if calibration_dataset:
        MAX_CALIBRATION_SIZE = 1024 * 1024 * 1024  # 1GB
        calibration_dataset.file.seek(0, os.SEEK_END)
        file_size = calibration_dataset.file.tell()
        calibration_dataset.file.seek(0)

        if file_size > MAX_CALIBRATION_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"校准数据集文件过大。最大支持 {MAX_CALIBRATION_SIZE / 1024 / 1024}MB"
            )

    try:
        # 4. Pydantic 验证配置
        logger.info(f"[DEBUG] config_dict 类型: {type(config_dict)}")
        logger.info(f"[DEBUG] config_dict 内容: {config_dict}")
        validated_config = ConversionConfig(**config_dict)
        logger.info(f"[DEBUG] validated_config 创建成功: {type(validated_config)}")

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
            yaml_content = await yaml_file.read()
            yaml_path = os.path.join(temp_dir, yaml_file.filename)
            with open(yaml_path, "wb") as f:
                f.write(yaml_content)

        # 6.5 保存校准数据集文件(如果提供)
        calibration_path = None
        if calibration_dataset:
            import zipfile
            import io

            # 读取 ZIP 文件内容
            zip_content = await calibration_dataset.read()

            # 验证是否是有效的 ZIP 文件
            try:
                with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_ref:
                    # 检查 ZIP 文件中是否有图片文件
                    file_list = zip_ref.namelist()
                    image_count = len([f for f in file_list if f.lower().endswith(('.jpg', '.jpeg', '.png'))])

                    if image_count == 0:
                        raise HTTPException(
                            status_code=400,
                            detail="校准数据集 ZIP 文件中未找到图片文件。支持的格式: .jpg, .jpeg, .png"
                        )

                    logger.info(f"校准数据集包含 {image_count} 张图片，共 {len(file_list)} 个文件")

            except zipfile.BadZipFile:
                raise HTTPException(
                    status_code=400,
                    detail="校准数据集不是有效的 ZIP 文件"
                )

            calibration_path = os.path.join(temp_dir, calibration_dataset.filename)
            with open(calibration_path, "wb") as f:
                f.write(zip_content)

            logger.info(f"校准数据集已保存: {calibration_dataset.filename}")

        # 7. 创建任务
        logger.info(f"[DEBUG] 准备创建任务，validated_config 类型: {type(validated_config)}")
        task_manager = get_task_manager()
        task_id = task_manager.create_task(validated_config)
        logger.info(f"[DEBUG] 任务创建成功: {task_id}")

        logger.info(f"创建转换任务: {task_id}")
        logger.info(f"模型文件: {model_file.filename}")
        logger.info(f"配置: {validated_config.model_type}, {validated_config.input_size}x{validated_config.input_size}")
        if calibration_path:
            logger.info(f"校准数据集: {calibration_dataset.filename}")

        # 8. 启动后台转换任务
        background_tasks.add_task(
            _run_conversion,
            task_id,
            model_path,
            validated_config,
            yaml_path,
            calibration_path
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
            import traceback
            logger.error(f"[ERROR] ValidationError 发生位置:")
            logger.error(traceback.format_exc())
            logger.error(f"[ERROR] ValidationError 详情: {e}")
            raise HTTPException(
                status_code=422,
                detail=f"配置验证失败: {str(e)}"
            )
        logger.error(f"创建转换任务失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


async def _run_conversion(
    task_id: str,
    model_path: str,
    config: ConversionConfig,
    yaml_path: Optional[str] = None,
    calibration_path: Optional[str] = None
):
    """
    后台执行模型转换任务

    现在使用真实的转换流程

    Args:
        task_id: 任务 ID
        model_path: 模型文件路径
        config: 转换配置
        yaml_path: YAML 文件路径（可选）
        calibration_path: 校准数据集路径（可选）
    """
    from ..core.converter import ModelConverter

    task_manager = get_task_manager()

    try:
        logger.info(f"开始任务 {task_id} 的真实转换流程")

        # 初始化转换器
        converter = ModelConverter()

        # 进度回调
        def progress_callback(progress: int, message: str):
            task_manager.update_progress(task_id, progress, message)
            logger.info(f"[{progress}%] {message}")

        # 准备配置字典（从 Pydantic 模型）
        config_dict = config.dict()
        config_dict["task_id"] = task_id

        # 执行转换
        output_path = converter.convert(
            model_path=model_path,
            config=config_dict,
            calib_dataset_path=calibration_path,
            progress_callback=progress_callback
        )

        # 标记任务完成
        task_manager.complete_task(task_id, output_path)
        logger.info(f"✅ 任务 {task_id} 转换成功")

    except Exception as e:
        logger.error(f"❌ 任务 {task_id} 转换失败: {str(e)}")
        task_manager.fail_task(task_id, str(e))
        raise

@router.get("/test")
async def test_endpoint():
    return {"message": "Test works!"}
