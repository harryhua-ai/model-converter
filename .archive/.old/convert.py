#!/usr/bin/env python3
"""
NE301 模型转换工具（命令行版本）
将 .pt 模型转换为可直接烧录的 .bin 固件

使用方法:
    python3 convert.py <model.pt> --preset yolov8n-480
    python3 convert.py <model.pt> -p yolov8n-480 --output ./outputs
"""
import sys
import os
import asyncio
import argparse
from pathlib import Path

# 添加后端路径
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.conversion import ConversionService
from app.services.task_manager import get_task_manager
from app.models.schemas import ConversionConfig, ModelType, QuantizationType, ColorFormat, PostprocessType


# 预设配置
PRESETS = {
    "yolov8n-256": {
        "model_name": "yolov8n_256",
        "model_type": ModelType.YOLO_DETECTION,
        "input_width": 256,
        "input_height": 256,
        "quantization_type": QuantizationType.INT8,
        "postprocess_type": PostprocessType.YOLO_V8,
        "num_classes": 80,
        "total_boxes": 8400,
    },
    "yolov8n-480": {
        "model_name": "yolov8n_480",
        "model_type": ModelType.YOLO_DETECTION,
        "input_width": 480,
        "input_height": 480,
        "quantization_type": QuantizationType.INT8,
        "postprocess_type": PostprocessType.YOLO_V8,
        "num_classes": 80,
        "total_boxes": 8400,
    },
    "yolov8n-640": {
        "model_name": "yolov8n_640",
        "model_type": ModelType.YOLO_DETECTION,
        "input_width": 640,
        "input_height": 640,
        "quantization_type": QuantizationType.INT8,
        "postprocess_type": PostprocessType.YOLO_V8,
        "num_classes": 80,
        "total_boxes": 8400,
    },
}


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="NE301 模型转换工具 - .pt → .bin 固件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s yolov8n.pt --preset yolov8n-480
  %(prog)s model.pt -p yolov8n-480 --output ./outputs
  %(prog)s model.pt --preset yolov8n-256 --num-classes 10

配置预设:
  yolov8n-256  快速检测 (256x256)
  yolov8n-480  平衡精度和性能 (480x480) [推荐]
  yolov8n-640  高精度检测 (640x640)
        """
    )
    parser.add_argument(
        "model",
        help="输入模型文件 (.pt/.pth/.onnx)"
    )
    parser.add_argument(
        "--preset", "-p",
        choices=list(PRESETS.keys()),
        required=True,
        help="配置预设"
    )
    parser.add_argument(
        "--output", "-o",
        default="./outputs",
        help="输出目录 (默认: ./outputs)"
    )
    parser.add_argument(
        "--num-classes", "-n",
        type=int,
        help="类别数量 (覆盖预设值)"
    )
    parser.add_argument(
        "--class-names",
        nargs="+",
        help="类别名称列表 (覆盖预设值)"
    )
    parser.add_argument(
        "--calibration", "-c",
        help="校准数据集 ZIP 文件路径"
    )
    parser.add_argument(
        "--data-yaml", "-d",
        help="data.yaml 类别配置文件路径"
    )

    return parser.parse_args()


async def convert_model(args):
    """执行模型转换"""
    # 检查输入文件
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"❌ 错误: 模型文件不存在: {args.model}", file=sys.stderr)
        sys.exit(1)

    # 加载预设配置
    preset = PRESETS[args.preset]
    config = ConversionConfig(
        model_name=preset["model_name"],
        model_type=preset["model_type"],
        input_width=preset["input_width"],
        input_height=preset["input_height"],
        quantization_type=preset["quantization_type"],
        postprocess_type=preset["postprocess_type"],
        num_classes=args.num_classes or preset["num_classes"],
        class_names=args.class_names,
        total_boxes=preset["total_boxes"],
    )

    # 创建输出目录
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成任务 ID
    import uuid
    task_id = f"cli_{uuid.uuid4().hex[:8]}"

    # 复制模型到上传目录
    from app.core.config import settings
    upload_path = Path(settings.UPLOAD_DIR) / f"{task_id}_{model_path.name}"
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy2(model_path, upload_path)

    # 创建任务
    task_manager = get_task_manager()
    task = await task_manager.create_task(
        task_id=task_id,
        config=config,
        filename=model_path.name
    )

    print(f"🚀 开始转换模型: {model_path.name}")
    print(f"   配置预设: {args.preset}")
    print(f"   输入尺寸: {config.input_width}x{config.input_height}")
    print(f"   量化类型: {config.quantization_type}")
    print(f"   类别数量: {config.num_classes}")
    print(f"   任务 ID: {task_id}")
    print()

    # 执行转换
    service = ConversionService()

    # 使用后台任务执行转换
    async def run_conversion():
        try:
            await service.convert_model(
                task_id=task_id,
                input_path=str(upload_path),
                calibration_dataset_path=args.calibration,
                class_yaml_path=args.data_yaml,
                config=config,
            )
        except Exception as e:
            print(f"❌ 转换失败: {e}", file=sys.stderr)
            await task_manager.update_task(
                task_id=task_id,
                error_message=str(e)
            )

    # 启动转换任务
    conversion_task = asyncio.create_task(run_conversion())

    # 监控进度
    last_progress = -1
    while not conversion_task.done():
        task = await task_manager.get_task(task_id)
        if task and task.progress != last_progress:
            print(f"   [{task.progress:3d}%] {task.current_step}", flush=True)
            last_progress = task.progress

        if task and task.status.value in ["completed", "failed", "cancelled"]:
            break

        await asyncio.sleep(0.5)

    # 等待任务完成
    await conversion_task

    # 获取最终状态
    task = await task_manager.get_task(task_id)

    print()
    if task.status.value == "completed":
        print(f"✅ 转换完成!")
        print(f"   输出文件: {task.output_filename}")
        output_path = Path(settings.OUTPUT_DIR) / task.output_filename
        print(f"   文件路径: {output_path}")
        print()
        print(f"烧录到设备:")
        print(f"  cp {output_path} ../Model/weights/")
        print(f"  cd .. && make flash-model")
        return 0
    else:
        print(f"❌ 转换失败: {task.error_message}")
        return 1


def main():
    """主函数"""
    args = parse_args()

    try:
        # 运行异步转换
        exit_code = asyncio.run(convert_model(args))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  转换已取消")
        sys.exit(130)
    except Exception as e:
        print(f"❌ 发生错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
