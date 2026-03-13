"""
数据模型定义
包含请求和响应的 Pydantic 模型
"""
from typing import Literal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ModelType(str, Enum):
    """支持的模型类型"""

    YOLOV8 = "YOLOv8"
    YOLOV11 = "YOLOv11"
    YOLOX = "YOLOX"
    CUSTOM = "Custom"


class InputSize(str, Enum):
    """支持的输入尺寸"""

    SIZE_256 = "256"
    SIZE_480 = "480"
    SIZE_640 = "640"


class QuantizationType(str, Enum):
    """量化类型 (仅支持 INT8)"""

    INT8 = "int8"


class QuantizationMode(str, Enum):
    """量化模式"""

    PER_CHANNEL = "per_channel"
    PER_TENSOR = "per_tensor"


class ColorFormat(str, Enum):
    """颜色格式"""

    RGB888_YUV444_1 = "RGB888_YUV444_1"
    RGB888 = "RGB888"
    BGR888 = "BGR888"


class PostprocessType(str, Enum):
    """后处理类型"""

    PP_OD_YOLO_V8_UF = "pp_od_yolo_v8_uf"
    PP_OD_YOLO_V8_UI = "pp_od_yolo_v8_ui"
    PP_OD_ST_YOLOX_UF = "pp_od_st_yolox_uf"


class ConversionConfig(BaseModel):
    """模型转换配置"""

    # 模型基本信息
    model_name: str = Field(..., description="模型名称", min_length=1, max_length=100)
    model_type: ModelType = Field(default=ModelType.YOLOV8, description="模型类型")
    model_version: str = Field(default="1.0.0", description="模型版本")

    # 输入配置
    input_width: int = Field(default=480, ge=256, le=640, description="输入宽度")
    input_height: int = Field(default=480, ge=256, le=640, description="输入高度")
    input_data_type: Literal["uint8", "float32"] = Field(
        default="uint8", description="输入数据类型"
    )
    color_format: ColorFormat = Field(
        default=ColorFormat.RGB888_YUV444_1, description="颜色格式"
    )

    # 量化配置 (平台仅支持 INT8)
    quantization_type: QuantizationType = Field(
        default=QuantizationType.INT8, description="量化类型 (固定为 int8)"
    )
    quantization_mode: QuantizationMode = Field(
        default=QuantizationMode.PER_CHANNEL, description="量化模式"
    )

    # 后处理配置
    postprocess_type: PostprocessType = Field(
        default=PostprocessType.PP_OD_YOLO_V8_UI, description="后处理类型"
    )
    num_classes: int = Field(default=80, ge=1, le=1000, description="类别数量")
    class_names: list[str] = Field(default_factory=list, description="类别名称列表")
    confidence_threshold: float = Field(
        default=0.25, ge=0.0, le=1.0, description="置信度阈值"
    )
    iou_threshold: float = Field(default=0.45, ge=0.0, le=1.0, description="IOU 阈值")
    max_detections: int = Field(default=100, ge=1, le=1000, description="最大检测数")
    total_boxes: int = Field(default=1344, ge=1, description="总框数")

    # 归一化配置
    mean: list[float] = Field(default=[0.0, 0.0, 0.0], description="归一化均值")
    std: list[float] = Field(default=[255.0, 255.0, 255.0], description="归一化标准差")

    # 校准数据集配置 (INT8 必须提供校准数据集)
    use_custom_calibration: bool = Field(
        default=True, description="始终使用自定义校准数据集 (INT8 必须)"
    )
    calibration_dataset_filename: str | None = Field(
        default=None, description="校准数据集文件名 (zip格式)"
    )

    @field_validator("mean", "std")
    @classmethod
    def validate_normalization(cls, v: list[float]) -> list[float]:
        """验证归一化参数"""
        if len(v) != 3:
            raise ValueError("归一化参数必须有 3 个值 (RGB)")
        return v

    @field_validator("input_width", "input_height")
    @classmethod
    def validate_input_size(cls, v: int) -> int:
        """验证输入尺寸"""
        if v not in [256, 320, 480, 640]:
            raise ValueError("输入尺寸必须是 256、320、480 或 640")
        return v

    @field_validator("calibration_dataset_filename")
    @classmethod
    def validate_calibration_file(cls, v: str | None, info) -> str | None:
        """验证校准数据集文件"""
        if info.data.get("use_custom_calibration") and not v:
            raise ValueError("使用自定义校准数据集时必须上传数据集文件")
        return v


class TaskStatus(str, Enum):
    """任务状态"""

    PENDING = "pending"
    VALIDATING = "validating"
    CONVERTING = "converting"
    PACKAGING = "packaging"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConversionTask(BaseModel):
    """转换任务"""

    task_id: str = Field(..., description="任务 ID")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")
    progress: int = Field(default=0, ge=0, le=100, description="进度百分比")
    current_step: str = Field(default="", description="当前步骤")
    config: ConversionConfig = Field(..., description="转换配置")
    error_message: str | None = Field(default=None, description="错误消息")
    output_filename: str | None = Field(default=None, description="输出文件名")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class ConversionProgress(BaseModel):
    """转换进度更新"""

    task_id: str
    status: TaskStatus
    progress: int  # 0-100
    current_step: str
    message: str | None = None
    error: str | None = None


class ModelUploadResponse(BaseModel):
    """模型上传响应"""

    task_id: str
    filename: str
    file_size: int
    config: ConversionConfig


class TaskListResponse(BaseModel):
    """任务列表响应"""

    tasks: list[ConversionTask]
    total: int


class ConfigPreset(BaseModel):
    """配置预设"""

    id: str = Field(..., description="预设 ID")
    name: str = Field(..., description="预设名称")
    description: str = Field(..., description="预设描述")
    config: ConversionConfig = Field(..., description="配置")
