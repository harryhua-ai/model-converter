# NE301 OTA 验证失败 - 完整调查报告

## 执行日期
2026-03-16

## 执行摘要

✅ **验证脚本测试结果**: 所有固件都通过了模拟验证
❓ **问题根源**: NE301 设备端有额外的验证逻辑

---

## 验证脚本测试结果

### 测试固件 1: ne301_Model_v2.0.0.3753_pkg.bin

```
============================================================
OTA Header 验证
============================================================

1. Magic Number: ✅ 通过 (0x4F544155)
2. Header Version: ✅ 通过 (0x0100)
3. Header Size: ✅ 通过 (1024 bytes)
4. Header CRC32: ✅ 通过 (0xA7E4FEDE)
5. Firmware Type: ✅ 通过 (ai_model - 0x04)
6. Version: ✅ 通过 (2.0.0.3753)
7. Total Package Size: ✅ 通过 (6166264 bytes)

============================================================
Model Package Header 验证
============================================================

1. Magic Number: ✅ 通过 (0x314D364E - N6M1)
2. Version: ✅ 通过 (0x030000)

✅ 所有验证通过！
```

### 测试固件 2: ne301_Model_v2.0.0.3327_pkg.bin

```
✅ 所有验证通过！
```

---

## 代码调查结果

### ✅ 任务 1: NE301 容器日志
- **结果**: 没有找到前端 precheck 验证失败的错误日志
- **位置**: `docker logs model-converter-api`
- **结论**: 错误发生在 NE301 设备端，不在后端日志中

### ✅ 任务 2: output_filename 验证
- **代码路径**:
  - `backend/app/core/ne301_config.py:273-275` - 返回 `ne301_Model_v{version}_pkg`
  - `backend/app/core/docker_adapter.py:846-891` - 使用正确的文件名
  - `backend/app/api/tasks.py:110` - 下载 API 使用 `task.output_filename`
- **结论**: ✅ 下载的文件包含完整的 OTA header

### ✅ 任务 3: ota_header_verify 函数
- **代码位置**: `ne301/Custom/Core/System/ota_header.c:18-54`
- **验证项目**:
  1. Magic number (`0x4F544155` - "OTAU")
  2. Header version (`0x0100` - v1.0)
  3. Header size (1024 bytes)
  4. **CRC32 校验**
- **结论**: ✅ 验证逻辑正确且严格

### ✅ 任务 4: CRC32 算法验证
- **Python 实现**: `ne301/Script/ota_packer.py:67-69`
  - 使用 `zlib.crc32()` - 标准 CRC32 算法
- **C 实现**: `ne301/Custom/Common/Utils/generic_math.c:51-59`
  - 使用标准 CRC32 查找表
  - 初始值: `0xFFFFFFFF`
  - 最终 XOR: `0xFFFFFFFF`
- **结论**: ✅ 两个实现完全一致

---

## 额外发现：ota_validate_firmware_header 函数

### 代码位置
`ne301/Custom/Services/OTA/ota_service.c:276-329`

### 验证逻辑

该函数执行以下额外的验证：

1. **文件大小验证**
   ```c
   if (header->file_size == 0 || header->file_size > 0x10000000) {
       return OTA_VALIDATION_ERROR_FILE_SIZE;
   }
   ```
   - 文件大小必须 > 0 且 < 256MB

2. **版本验证**（如果 `options->validate_version` 为 true）
   - **降级检查**: 不允许降级到当前运行版本以下
   - **最小版本检查**: MAJOR 版本必须 >= `options->min_version`
   - **最大版本检查**: MAJOR 版本必须 <= `options->max_version`

3. **分区大小验证**（如果 `options->validate_partition_size` 为 true）
   - 调用 `ota_validate_partition_availability(fw_type, header->file_size)`
   - AI 模型分区大小限制: **10MB** (`0xA00000`)

### 关键发现

**AI 模型分区大小限制**: 10MB
```c
case FIRMWARE_AI_1:
    partition_size = 0xA00000;  // 10MB
    break;
```

**我们的固件大小**: 6166264 bytes ≈ **5.88 MB** ✅

---

## 问题定位

### ✅ 已验证通过的部分

1. OTA header 结构正确
2. CRC32 计算正确
3. Magic number、version、size 都正确
4. 文件名逻辑正确
5. 分区大小符合要求（5.88 MB < 10 MB）

### ❓ 可能的问题原因

由于验证脚本模拟了 `ota_header_verify` 函数并通过了验证，但 NE301 前端仍然报错，问题可能在于：

#### 1. 版本验证失败
- **降级检查**: NE301 设备的当前版本可能比固件版本高
- **MAJOR 版本限制**: 设备可能要求特定的 MAJOR 版本范围

#### 2. 硬件兼容性检查
- NE301 设备的硬件版本可能不兼容
- 需要检查设备的硬件 ID 或序列号

#### 3. 其他系统级验证
- 设备可能执行额外的安全检查
- 签名验证（虽然代码中标记为 reserved）

---

## 推荐的下一步行动

### 🔥 高优先级

#### 1. 获取 NE301 设备的详细错误日志

**操作**:
```bash
# 连接到 NE301 设备控制台
# 查看 OTA precheck API 的详细错误响应

# 关键信息：
# - 具体的验证失败原因
# - 失败的字段名称
# - 期望值 vs 实际值
```

#### 2. 检查版本验证逻辑

**操作**:
- 查看 NE301 设备的当前固件版本
- 确认固件版本 2.0.0.XXXX 是否满足版本要求
- 检查 `options->validate_version` 是否为 true
- 检查 `options->allow_downgrade` 是否为 false

#### 3. 测试不同版本号

**操作**:
```bash
# 尝试使用更高的版本号
# 例如：3.0.0.1 或 2.0.0.9999

# 检查版本号格式是否有特殊要求
```

### 📋 中等优先级

#### 4. 验证硬件兼容性

**操作**:
- 检查 NE301 设备的硬件版本
- 确认 AI 模型固件是否需要特定的硬件版本

#### 5. 检查签名验证

**操作**:
- 查看 OTA header 中的 Security Information Section (416 bytes)
- 确认是否需要数字签名

---

## 临时解决方案

### 方案 1: 调整版本号

如果问题是版本降级检查：

```python
# 在 backend/app/core/ne301_config.py 中
def get_model_version(self) -> Version:
    """获取模型版本号"""
    # 尝试使用更高的版本号
    return Version(3, 0, 0, 1)  # 改为 3.0.0.1
```

### 方案 2: 检查版本生成逻辑

```python
# 检查版本号是否基于时间戳生成
# 确保版本号总是递增的
```

---

## 验证工具使用

### 运行验证脚本

```bash
# 验证任何固件文件
python3 scripts/verify_ota_firmware.py <firmware.bin>

# 示例
python3 scripts/verify_ota_firmware.py ne301/build/ne301_Model_v2.0.0.3753_pkg.bin
```

### 预期输出

如果所有验证通过，输出会显示：
```
✅ 所有验证通过！
该固件应该能够通过 NE301 前端的预检查验证。
```

---

## 关键文件列表

### 后端代码
- `backend/app/core/docker_adapter.py:826-891` - OTA header 生成
- `backend/app/core/ne301_config.py:260-275` - 文件名和版本管理
- `backend/app/api/tasks.py:64-124` - 下载 API

### NE301 验证代码
- `ne301/Custom/Core/System/ota_header.c:18-54` - `ota_header_verify`
- `ne301/Custom/Services/OTA/ota_service.c:276-329` - `ota_validate_firmware_header`
- `ne301/Custom/Common/Utils/generic_math.c:51-59` - `generic_crc32`

### 打包工具
- `ne301/Script/ota_packer.py` - OTA header 生成（Python）
- `ne301/Script/model_packager.py` - Model package header 生成

---

## 附录：OTA Header 结构

```
OTA Header (1024 bytes total):
├── Basic Information (64 bytes): 0x00-0x3F
│   ├── Magic: 0x4F544155 (OTAU)
│   ├── Header Version: 0x0100
│   ├── Header Size: 1024
│   ├── Header CRC32: <calculated>
│   ├── FW Type: 0x04 (ai_model)
│   ├── Timestamp: <unix timestamp>
│   ├── Sequence: 1
│   └── Total Package Size: <firmware + header>
│
├── Firmware Information (160 bytes): 0x40-0xDF
│   ├── FW Name: "NE301_MODEL"
│   ├── FW Description: "NE301 AI Model (version)"
│   ├── FW Version: [major, minor, patch, build_low, build_high, 0, 0, 0]
│   ├── Min Version: [same as FW Version]
│   ├── FW Size: <firmware data size>
│   ├── FW CRC32: <firmware CRC32>
│   └── FW Hash: <SHA256>
│
├── Target Information (64 bytes): 0xE0-0x11F
├── Dependencies (64 bytes): 0x120-0x15F
├── Security (416 bytes): 0x160-0x2FF
└── Extensions (256 bytes): 0x300-0x3FF
```

---

**报告生成时间**: 2026-03-16
**报告版本**: 2.0
**状态**: 调查完成，等待 NE301 设备错误日志
**下一步**: 获取 NE301 前端的详细验证失败信息
