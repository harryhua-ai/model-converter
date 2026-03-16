#!/usr/bin/env python3
"""
OTA 固件验证脚本
模拟 NE301 前端的验证逻辑，测试生成的固件是否能通过验证
"""

import struct
import zlib
import sys
from pathlib import Path

# Constants - 必须与 ota_header.h 一致
OTA_HEADER_SIZE = 1024
OTA_MAGIC_NUMBER = 0x4F544155  # "OTAU"
OTA_HEADER_VERSION = 0x0100    # v1.0

# Model package constants
MODEL_PACKAGE_MAGIC = 0x314D364E  # "N6M1"
MODEL_PACKAGE_VERSION = 0x030000   # v3.0.0


def read_ota_header(firmware_path: str) -> dict:
    """读取并解析 OTA header"""
    with open(firmware_path, 'rb') as f:
        header_data = f.read(OTA_HEADER_SIZE)

    if len(header_data) != OTA_HEADER_SIZE:
        raise ValueError(f"文件太小，无法包含完整的 OTA header: {len(header_data)} bytes")

    # 解析关键字段
    magic = struct.unpack_from('<I', header_data, 0)[0]
    header_version = struct.unpack_from('<H', header_data, 4)[0]
    header_size = struct.unpack_from('<H', header_data, 6)[0]
    header_crc32 = struct.unpack_from('<I', header_data, 8)[0]
    fw_type = struct.unpack_from('<B', header_data, 0x0C)[0]
    total_package_size = struct.unpack_from('<I', header_data, 0x18)[0]

    # 读取版本信息 (offset 0xA0)
    fw_ver = struct.unpack_from('<8B', header_data, 0xA0)

    return {
        'magic': magic,
        'header_version': header_version,
        'header_size': header_size,
        'header_crc32': header_crc32,
        'fw_type': fw_type,
        'total_package_size': total_package_size,
        'fw_ver': fw_ver,
        'raw_header': header_data
    }


def read_model_package_header(firmware_path: str) -> dict:
    """读取并解析 model package header (offset 1024)"""
    with open(firmware_path, 'rb') as f:
        f.seek(1024)  # 跳过 OTA header
        model_header_data = f.read(1024)  # model package header 也是 1KB

    if len(model_header_data) < 8:
        raise ValueError(f"文件太小，无法包含 model package header")

    # 解析关键字段
    magic = struct.unpack_from('<I', model_header_data, 0)[0]
    version = struct.unpack_from('<I', model_header_data, 4)[0]

    return {
        'magic': magic,
        'version': version,
        'raw_header': model_header_data
    }


def verify_ota_header(header: dict) -> tuple[bool, str]:
    """
    验证 OTA header
    返回: (是否通过验证, 错误信息)
    """
    print("\n" + "="*60)
    print("OTA Header 验证")
    print("="*60)

    # 1. 验证 magic number
    print(f"\n1. Magic Number:")
    print(f"   期望值: 0x{OTA_MAGIC_NUMBER:08X} (OTAU)")
    print(f"   实际值: 0x{header['magic']:08X}")
    if header['magic'] != OTA_MAGIC_NUMBER:
        return False, "Magic number 不匹配"
    print("   ✅ 通过")

    # 2. 验证 header version
    print(f"\n2. Header Version:")
    print(f"   期望值: 0x{OTA_HEADER_VERSION:04X}")
    print(f"   实际值: 0x{header['header_version']:04X}")
    if header['header_version'] != OTA_HEADER_VERSION:
        return False, f"Header version 不支持: 0x{header['header_version']:04X}"
    print("   ✅ 通过")

    # 3. 验证 header size
    print(f"\n3. Header Size:")
    print(f"   期望值: {OTA_HEADER_SIZE} bytes")
    print(f"   实际值: {header['header_size']} bytes")
    if header['header_size'] != OTA_HEADER_SIZE:
        return False, f"Header size 不正确: {header['header_size']}"
    print("   ✅ 通过")

    # 4. 验证 CRC32
    print(f"\n4. Header CRC32:")
    print(f"   存储的 CRC32: 0x{header['header_crc32']:08X}")

    # 计算 CRC32 (排除 CRC32 字段本身)
    header_for_crc = bytearray(header['raw_header'])
    struct.pack_into('<I', header_for_crc, 8, 0)  # 设置 CRC32 字段为 0
    calculated_crc = zlib.crc32(bytes(header_for_crc)) & 0xFFFFFFFF
    print(f"   计算的 CRC32: 0x{calculated_crc:08X}")

    if calculated_crc != header['header_crc32']:
        print(f"   ❌ CRC32 不匹配!")
        print(f"   差异: 存储值=0x{header['header_crc32']:08X}, 计算值=0x{calculated_crc:08X}")
        return False, "CRC32 验证失败"
    print("   ✅ 通过")

    # 5. 显示固件类型
    print(f"\n5. Firmware Type:")
    fw_types = {
        0x01: "fsbl",
        0x02: "app",
        0x03: "web",
        0x04: "ai_model",
        0x05: "config",
        0x06: "patch",
        0x07: "full"
    }
    fw_type_name = fw_types.get(header['fw_type'], "unknown")
    print(f"   类型: {fw_type_name} (0x{header['fw_type']:02X})")
    if header['fw_type'] != 0x04:
        print(f"   ⚠️  警告: AI 模型固件应该是 0x04")
    print("   ✅ 通过")

    # 6. 显示版本信息
    print(f"\n6. Version Information:")
    ver = header['fw_ver']
    major = ver[0]
    minor = ver[1]
    patch = ver[2]
    build = ver[3] | (ver[4] << 8)
    print(f"   版本: {major}.{minor}.{patch}.{build}")
    print("   ✅ 通过")

    # 7. 显示总大小
    print(f"\n7. Total Package Size:")
    print(f"   大小: {header['total_package_size']} bytes ({header['total_package_size'] / 1024 / 1024:.2f} MB)")
    print("   ✅ 通过")

    return True, ""


def verify_model_package_header(model_header: dict) -> tuple[bool, str]:
    """
    验证 model package header
    返回: (是否通过验证, 错误信息)
    """
    print("\n" + "="*60)
    print("Model Package Header 验证")
    print("="*60)

    # 1. 验证 magic number
    print(f"\n1. Magic Number:")
    print(f"   期望值: 0x{MODEL_PACKAGE_MAGIC:08X} (N6M1)")
    print(f"   实际值: 0x{model_header['magic']:08X}")
    if model_header['magic'] != MODEL_PACKAGE_MAGIC:
        return False, f"Model package magic 不匹配: 0x{model_header['magic']:08X}"
    print("   ✅ 通过")

    # 2. 验证 version
    print(f"\n2. Version:")
    print(f"   期望值: 0x{MODEL_PACKAGE_VERSION:06X}")
    print(f"   实际值: 0x{model_header['version']:06X}")
    if model_header['version'] != MODEL_PACKAGE_VERSION:
        return False, f"Model package version 不匹配: 0x{model_header['version']:06X}"
    print("   ✅ 通过")

    return True, ""


def main():
    if len(sys.argv) != 2:
        print("使用方法: python verify_ota_firmware.py <firmware.bin>")
        print("\n示例:")
        print("  python verify_ota_firmware.py ne301_Model_v2.0.0.6803_pkg.bin")
        sys.exit(1)

    firmware_path = sys.argv[1]

    if not Path(firmware_path).exists():
        print(f"❌ 错误: 文件不存在: {firmware_path}")
        sys.exit(1)

    print("="*60)
    print(f"验证 OTA 固件: {firmware_path}")
    print("="*60)

    # 获取文件大小
    file_size = Path(firmware_path).stat().st_size
    print(f"\n文件大小: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")

    try:
        # 读取并验证 OTA header
        ota_header = read_ota_header(firmware_path)
        success, error = verify_ota_header(ota_header)
        if not success:
            print(f"\n❌ OTA Header 验证失败: {error}")
            sys.exit(1)

        # 读取并验证 model package header
        model_header = read_model_package_header(firmware_path)
        success, error = verify_model_package_header(model_header)
        if not success:
            print(f"\n❌ Model Package Header 验证失败: {error}")
            sys.exit(1)

        print("\n" + "="*60)
        print("✅ 所有验证通过！")
        print("="*60)
        print("\n该固件应该能够通过 NE301 前端的预检查验证。")
        print("\n如果 NE301 前端仍然报错，请检查：")
        print("1. NE301 设备的硬件版本兼容性")
        print("2. NE301 设备的分区大小限制")
        print("3. NE301 设备的系统版本要求")
        print("4. NE301 容器的日志输出")

    except Exception as e:
        print(f"\n❌ 验证过程中出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
