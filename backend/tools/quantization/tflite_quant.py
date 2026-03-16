#!/usr/bin/env python
"""
ST 官方 TFLite 量化脚本（Mock 版本用于测试）

这是一个 mock 实现，用于测试目的
"""
import sys
import argparse
import os
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-path", required=True)
    parser.add_argument("--config-name", required=True)
    args = parser.parse_args()

    config_path = Path(args.config_path)
    config_file = config_path / f"{args.config_name}.yaml"

    # 读取配置
    import yaml
    with open(config_file) as f:
        config = yaml.safe_load(f)

    # 获取输出路径
    output_path = Path(config["quantization"]["export_path"])
    output_path.mkdir(parents=True, exist_ok=True)

    # 检查环境变量，如果设置为 "no_file"，则不创建文件（用于测试）
    if os.environ.get("MOCK_QUANT_NO_FILE", "false").lower() == "true":
        print("⚠️  Mock: 跳过创建量化文件")
        return 0

    # 创建 mock 量化文件
    model_name = config["model"]["name"]
    quantized_file = output_path / f"{model_name}_quant.tflite"
    quantized_file.write_bytes(b"\x00" * 100)  # Mock TFLite 文件

    print(f"✅ 量化完成: {quantized_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
