"""
Pydantic schemas for data validation

This module defines the data models used throughout the application:
- ConversionConfig: User's conversion parameters
- ClassDefinition: Optional YAML file defining object detection categories
- ConversionTask: Task state tracking
- EnvironmentStatus: Docker environment check results
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class ConversionConfig(BaseModel):
    """转换配置"""
    model_type: Literal["YOLOv8", "YOLOX"] = "YOLOv8"
    input_size: Literal[256, 480, 640] = 480
    num_classes: int = Field(default=80, ge=1, le=1000)
    confidence_threshold: float = Field(default=0.25, ge=0.01, le=0.99)
    quantization: Literal["int8"] = "int8"
    use_calibration: bool = False


class ClassDefinition(BaseModel):
    """类别定义"""
    classes: list[dict]  # [{"name": "person", "id": 0, "color": [255, 0, 0]}]


class ConversionTask(BaseModel):
    """转换任务"""
    task_id: str
    status: Literal["pending", "running", "completed", "failed"]
    progress: int = Field(default=0, ge=0, le=100)
    current_step: str = ""
    config: ConversionConfig
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    output_filename: Optional[str] = None


class EnvironmentStatus(BaseModel):
    """环境状态"""
    status: Literal["ready", "docker_not_installed", "image_pull_required", "not_configured"]
    mode: Literal["docker", "none"]
    message: str
    image_size: Optional[str] = None
    estimated_time: Optional[str] = None
    error: Optional[str] = None
    guide: Optional[dict] = None
