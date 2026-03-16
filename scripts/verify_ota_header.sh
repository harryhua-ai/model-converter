#!/bin/bash

# OTA Header 完整验证工具

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if [ $# -lt 1 ]; then
    echo "用法: $0 <固件文件路径>"
    echo ""
    echo "示例: $0 /app/outputs/ne301_Model_v2.0.0.6803_pkg.bin"
    exit 1
fi

FIRMWARE_FILE="$1"

if [ ! -f "$FIRMWARE_FILE" ]; then
    echo -e "${RED}❌ 文件不存在: $FIRMWARE_FILE${NC}"
    exit 1
fi

python3 << EOF
import struct
import sys
from pathlib import Path

firmware_file = Path("$FIRMWARE_FILE")
file_size = firmware_file.stat().st_size

print(f"\n{'='*70}")
print(f"OTA Header 完整验证")
print(f"{'='*70}\n")

print(f"文件: {firmware_file.name}")
print(f"大小: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)\n")

with open(firmware_file, 'rb') as f:
    header = f.read(1024)
    firmware_data = f.read()

# 解析 OTA Header
errors = []
warnings = []

# 1. Magic Number (offset 0x00)
magic = struct.unpack_from('<I', header, 0)[0]
if magic == 0x4F544155:
    print(f"✅ Magic Number: 0x{magic:08X} (OTAU)")
else:
    errors.append(f"Magic Number 错误: 0x{magic:08X}，期望 0x4F544155")
    print(f"❌ Magic Number: 0x{magic:08X}，期望 0x4F544155")

# 2. Header Version (offset 0x04)
header_version = struct.unpack_from('<H', header, 4)[0]
if header_version == 0x0100:
    print(f"✅ Header Version: {header_version:#06x}")
else:
    warnings.append(f"Header Version 异常: {header_version:#06x}")
    print(f"⚠️  Header Version: {header_version:#06x}")

# 3. Header Size (offset 0x06)
header_size = struct.unpack_from('<H', header, 6)[0]
if header_size == 1024:
    print(f"✅ Header Size: {header_size} bytes")
else:
    errors.append(f"Header Size 错误: {header_size}，期望 1024")
    print(f"❌ Header Size: {header_size}，期望 1024")

# 4. Firmware Type (offset 0x0C)
fw_type = struct.unpack_from('<B', header, 12)[0]
fw_type_map = {
    0x01: 'fsbl',
    0x02: 'app',
    0x03: 'web',
    0x04: 'ai_model',
    0x05: 'config',
    0x06: 'patch',
    0x07: 'full'
}
if fw_type == 0x04:
    print(f"✅ Firmware Type: {fw_type} ({fw_type_map.get(fw_type, 'unknown')})")
else:
    warnings.append(f"Firmware Type 异常: {fw_type}")
    print(f"⚠️  Firmware Type: {fw_type} ({fw_type_map.get(fw_type, 'unknown')})")

# 5. Name (offset 0x40)
name = header[0x40:0x60].rstrip(b'\x00').decode('utf-8', errors='replace')
print(f"✅ Name: {name}")

# 6. Description (offset 0x60)
desc = header[0x60:0xA0].rstrip(b'\x00').decode('utf-8', errors='replace')
print(f"✅ Description: {desc}")

# 7. Version (offset 0xA0)
major = header[0xA0]
minor = header[0xA1]
patch = header[0xA2]
build_low = header[0xA3]
build_high = header[0xA4]
build = build_low | (build_high << 8)
version_str = f"{major}.{minor}.{patch}.{build}"

if major == 0 and minor == 0 and patch == 0 and build == 0:
    errors.append(f"版本号全为 0")
    print(f"❌ Version: {version_str} (版本号错误)")
else:
    print(f"✅ Version: {version_str}")

# 8. Firmware Data 检查
print(f"\n固件数据大小: {len(firmware_data):,} bytes ({len(firmware_data) / 1024 / 1024:.2f} MB)")

if len(firmware_data) > 0:
    # 检查固件数据的前 4 字节（应该是 NE301 magic: N6M1）
    firmware_magic = struct.unpack_from('<I', firmware_data, 0)[0]
    if firmware_magic == 0x314D364E:
        print(f"✅ Firmware Magic: 0x{firmware_magic:08X} (N6M1)")
    else:
        warnings.append(f"Firmware Magic 异常: 0x{firmware_magic:08X}")
        print(f"⚠️  Firmware Magic: 0x{firmware_magic:08X}，期望 0x314D364E (N6M1)")
else:
    errors.append(f"固件数据为空")
    print(f"❌ 固件数据为空")

# 总结
print(f"\n{'='*70}")
if errors:
    print(f"{RED}❌ 发现 {len(errors)} 个错误:{NC}")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
elif warnings:
    print(f"{YELLOW}⚠️  发现 {len(warnings)} 个警告:{NC}")
    for warning in warnings:
        print(f"  - {warning}")
    print(f"\n{GREEN}✅ OTA Header 基本正确（有警告）{NC}")
    sys.exit(0)
else:
    print(f"{GREEN}✅ OTA Header 完全正确{NC}")
    sys.exit(0)

EOF
