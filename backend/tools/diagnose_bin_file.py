#!/usr/bin/env python3
"""
NE301 bin 文件和 OTA header 诊断工具

用途：
1. 检查 bin 文件大小是否合理
2. 验证 JSON 配置中的输入尺寸
3. 检查 OTA header 版本是否正确
4. 提供优化建议

使用：
python3 diagnose_bin_file.py --bin-path /path/to/model.bin --json-path /path/to/model.json
"""

import argparse
import json
import struct
from pathlib import Path
from typing import Any, Dict, Tuple


# 颜色输出
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")


def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")


def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")


def print_header(msg: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


class NE301Diagnostics:
    """NE301 诊断工具"""

    # OTA 常量
    OTA_MAGIC = 0x4F544155  # "OTAU"
    OTA_HEADER_SIZE = 1024
    OTA_EXPECTED_VERSION = 0x0100  # v1.0

    # 模型包常量
    MODEL_MAGIC = 0x314D364E  # "N6M1"

    def __init__(self, bin_path: Path, json_path: Path = None):
        self.bin_path = bin_path
        self.json_path = json_path
        self.bin_data = None
        self.json_data = None

    def run_diagnostics(self):
        """运行所有诊断"""
        print_header("NE301 Bin 文件诊断")

        # 1. 读取文件
        self._load_files()

        # 2. 识别文件类型
        file_type = self._identify_file_type()

        # 3. 根据文件类型运行诊断
        if file_type == "ota_package":
            self._diagnose_ota_package()
        elif file_type == "model_package":
            self._diagnose_model_package()
        else:
            print_error(f"未知的文件类型: {file_type}")

        # 4. 检查 JSON 配置（如果提供）
        if self.json_path and self.json_path.exists():
            self._diagnose_json_config()

        # 5. 生成优化建议
        self._generate_recommendations()

    def _load_files(self):
        """加载文件"""
        print_info(f"加载 bin 文件: {self.bin_path}")
        with open(self.bin_path, "rb") as f:
            self.bin_data = f.read()

        if self.json_path and self.json_path.exists():
            print_info(f"加载 JSON 文件: {self.json_path}")
            with open(self.json_path, "r") as f:
                self.json_data = json.load(f)

    def _identify_file_type(self) -> str:
        """识别文件类型"""
        if len(self.bin_data) < 4:
            return "unknown"

        magic = struct.unpack("<I", self.bin_data[:4])[0]

        if magic == self.OTA_MAGIC:
            print_success(f"识别为 OTA 包 (magic: 0x{magic:08X})")
            return "ota_package"
        elif magic == self.MODEL_MAGIC:
            print_success(f"识别为模型包 (magic: 0x{magic:08X})")
            return "model_package"
        else:
            print_warning(f"未知 magic: 0x{magic:08X}")
            return "unknown"

    def _diagnose_ota_package(self):
        """诊断 OTA 包"""
        print_header("OTA 包诊断")

        # 解析 header
        if len(self.bin_data) < self.OTA_HEADER_SIZE:
            print_error(f"文件太小: {len(self.bin_data)} < {self.OTA_HEADER_SIZE}")
            return

        # 读取关键字段
        magic = struct.unpack("<I", self.bin_data[0x00:0x04])[0]
        header_version = struct.unpack("<H", self.bin_data[0x04:0x06])[0]
        header_size = struct.unpack("<H", self.bin_data[0x06:0x08])[0]
        fw_type = struct.unpack("<B", self.bin_data[0x0C:0x0D])[0]
        total_size = struct.unpack("<I", self.bin_data[0x18:0x1C])[0]

        print_info(f"Magic: 0x{magic:08X} (期望: 0x{self.OTA_MAGIC:08X})")
        print_info(
            f"Header Version: 0x{header_version:04X} (期望: 0x{self.OTA_EXPECTED_VERSION:04X})"
        )
        print_info(f"Header Size: {header_size} bytes (期望: {self.OTA_HEADER_SIZE})")
        print_info(f"Firmware Type: 0x{fw_type:02X} (0x04 = AI Model)")
        print_info(f"Total Size: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")

        # 验证
        if magic != self.OTA_MAGIC:
            print_error(f"❌ Magic 不匹配！")
        else:
            print_success(f"Magic 正确")

        if header_version != self.OTA_EXPECTED_VERSION:
            print_error(f"❌ Header Version 不匹配！")
            print_error(f"   实际: 0x{header_version:04X}")
            print_error(f"   期望: 0x{self.OTA_EXPECTED_VERSION:04X}")
            print_error(f"   设备端可能无法识别此 OTA 包！")
        else:
            print_success(f"Header Version 正确 (v1.0)")

        if header_size != self.OTA_HEADER_SIZE:
            print_error(f"❌ Header Size 不匹配！")
        else:
            print_success(f"Header Size 正确")

        # 检查固件大小
        fw_size = total_size - header_size
        print_info(f"固件大小: {fw_size:,} bytes ({fw_size/1024/1024:.2f} MB)")

        # 分析大小是否合理
        if fw_size > 6 * 1024 * 1024:  # > 6MB
            print_warning(f"⚠️  固件大小较大 (>6 MB)")
            print_warning(f"   可能无法导入 STM32N6 (2MB Flash)")
        elif fw_size > 4 * 1024 * 1024:  # > 4MB
            print_warning(f"⚠️  固件大小接近限制 (4-6 MB)")
            print_warning(f"   建议优化模型大小")
        else:
            print_success(f"固件大小合理 (<4 MB)")

    def _diagnose_model_package(self):
        """诊断模型包"""
        print_header("模型包诊断")

        # 读取 header (15 x uint32)
        header = struct.unpack("<15I", self.bin_data[:60])
        (
            magic,
            version,
            package_size,
            metadata_offset,
            metadata_size,
            model_config_offset,
            model_config_size,
            model_offset,
            model_size,
            ext_offset,
            ext_size,
            header_checksum,
            model_checksum,
            config_checksum,
            package_checksum,
        ) = header

        print_info(f"Magic: 0x{magic:08X} (期望: 0x{self.MODEL_MAGIC:08X})")
        print_info(f"Version: {version >> 16}.{(version >> 8) & 0xFF}.{version & 0xFF}")
        print_info(f"Package Size: {package_size:,} bytes ({package_size/1024/1024:.2f} MB)")
        print_info(f"Model Size: {model_size:,} bytes ({model_size/1024/1024:.2f} MB)")

        if magic != self.MODEL_MAGIC:
            print_error(f"❌ Magic 不匹配！")
        else:
            print_success(f"Magic 正确")

        # 分析大小
        if model_size > 5 * 1024 * 1024:
            print_warning(f"⚠️  模型大小较大 (>5 MB)")
        else:
            print_success(f"模型大小合理")

    def _diagnose_json_config(self):
        """诊断 JSON 配置"""
        print_header("JSON 配置诊断")

        # 检查输入尺寸
        input_spec = self.json_data.get("input_spec", {})
        width = input_spec.get("width", 0)
        height = input_spec.get("height", 0)

        print_info(f"输入尺寸: {width}x{height}")

        # 检查输出规格
        output_spec = self.json_data.get("output_spec", {})
        outputs = output_spec.get("outputs", [])
        if outputs:
            output = outputs[0]
            output_height = output.get("height", 0)
            output_width = output.get("width", 0)
            print_info(f"输出形状: (1, {output_height}, {output_width})")

            # 计算 total_boxes
            total_boxes = output_width
            print_info(f"Total Boxes: {total_boxes}")

            # 根据输入尺寸验证 total_boxes
            expected_boxes = self._calculate_expected_boxes(width)
            if total_boxes != expected_boxes:
                print_error(f"❌ Total Boxes 不匹配！")
                print_error(f"   实际: {total_boxes}")
                print_error(f"   期望: {expected_boxes} (基于 {width}x{width} 输入)")
                print_error(f"   JSON 配置可能有误！")
            else:
                print_success(f"Total Boxes 正确")

        # 检查类别数量
        num_classes = self.json_data.get("postprocess_params", {}).get("num_classes", 0)
        print_info(f"类别数量: {num_classes}")

    def _calculate_expected_boxes(self, input_size: int) -> int:
        """计算期望的 total_boxes"""
        # YOLOv8 有 3 个检测头，stride 分别为 8, 16, 32
        if input_size == 256:
            return 1344  # 3 * (32*32 + 16*16 + 8*8)
        elif input_size == 320:
            return 2100
        elif input_size == 416:
            return 3549
        elif input_size == 640:
            return 8400
        else:
            # 通用计算
            scale = input_size // 8
            return 3 * (scale * scale + (scale // 2) ** 2 + (scale // 4) ** 2)

    def _generate_recommendations(self):
        """生成优化建议"""
        print_header("优化建议")

        # 基于诊断结果生成建议
        recommendations = []

        # 检查文件大小
        bin_size_mb = len(self.bin_data) / 1024 / 1024
        if bin_size_mb > 5.5:
            recommendations.append(
                {
                    "priority": "HIGH",
                    "issue": f"bin 文件过大 ({bin_size_mb:.2f} MB)",
                    "solutions": [
                        "检查 JSON 配置中的输入尺寸是否正确",
                        "减少类别数量（如果可能）",
                        "降低输入尺寸（256 → 192 或 128）",
                        "使用更小的模型变体",
                    ],
                }
            )

        # 检查 JSON 配置（如果有）
        if self.json_data:
            input_size = self.json_data.get("input_spec", {}).get("width", 0)
            if input_size > 512:
                recommendations.append(
                    {
                        "priority": "MEDIUM",
                        "issue": f"输入尺寸较大 ({input_size}x{input_size})",
                        "solutions": ["考虑降低到 256x256 或更小", "在精度和大小之间权衡"],
                    }
                )

        # 显示建议
        if recommendations:
            for rec in recommendations:
                priority_color = Colors.RED if rec["priority"] == "HIGH" else Colors.YELLOW
                print(f"\n{priority_color}[{rec['priority']}] {rec['issue']}{Colors.END}")
                print("解决方案:")
                for i, solution in enumerate(rec["solutions"], 1):
                    print(f"  {i}. {solution}")
        else:
            print_success("未发现明显问题")


def main():
    parser = argparse.ArgumentParser(description="NE301 bin 文件诊断工具")
    parser.add_argument("--bin-path", required=True, help="bin 文件路径")
    parser.add_argument("--json-path", help="JSON 配置文件路径（可选）")

    args = parser.parse_args()

    bin_path = Path(args.bin_path)
    json_path = Path(args.json_path) if args.json_path else None

    if not bin_path.exists():
        print_error(f"bin 文件不存在: {bin_path}")
        return 1

    diagnostics = NE301Diagnostics(bin_path, json_path)
    diagnostics.run_diagnostics()

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
