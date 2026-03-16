# NE301 固件验证失败 - 深度分析报告

## 执行日期
2026-03-16

## 问题现状

✅ **本地验证脚本**: 通过所有检查（OTA header、CRC32、magic number、分区大小）
❌ **NE301 前端 precheck**: 仍然失败

---

## 一、所有可能的失败原因分析（脑暴）

### 1. 版本验证相关（高概率）

#### 1.1 降级保护检查 ⚠️
- **代码位置**: `ota_service.c:296-304`
- **验证逻辑**:
  ```c
  if (!options->allow_downgrade) {
      if (ota_version_compare(header->version, current_ver) < 0) {
          return OTA_VALIDATION_ERROR_VERSION_INVALID;
      }
  }
  ```
- **问题**: 当前运行版本可能高于 2.0.0.XXXX 或 3.0.0.1
- **Precheck 中的配置**:
  ```c
  .allow_downgrade = AICAM_FALSE,  // ❌ 不允许降级
  ```
- **概率**: **高**

#### 1.2 版本范围限制 ⚠️
- **代码位置**: `ota_service.c:308-316`
- **验证逻辑**:
  ```c
  if (options->min_version > 0 && header->version[0] < options->min_version) {
      return OTA_VALIDATION_ERROR_VERSION_INVALID;
  }
  if (options->max_version > 0 && header->version[0] > options->max_version) {
      return OTA_VALIDATION_ERROR_VERSION_INVALID;
  }
  ```
- **Precheck 中的配置**:
  ```c
  .min_version = 1,   // MAJOR version >= 1
  .max_version = 10,  // MAJOR version <= 10
  ```
- **问题**: 如果设备要求特定版本范围（如 2.x.x.x），2.0.0.XXXX 可能不满足
- **概率**: **中**

#### 1.3 版本比较逻辑问题
- **版本格式**: `[major, minor, patch, build_low, build_high, 0, 0, 0]`
- **比较逻辑**: 字典序比较，先比较 major，再比较 minor...
- **潜在问题**:
  - 如果设备版本是 2.1.0.0，而我们上传 2.0.0.3753，会被判定为降级
  - 如果设备版本是 3.0.0.0，而我们上传 2.0.0.XXXX，也会被判定为降级
- **概率**: **高**

---

### 2. 硬件兼容性检查（高概率）

#### 2.1 硬件版本验证 ⚠️
- **Precheck 配置**:
  ```c
  .validate_hardware = AICAM_TRUE,  // ✅ 启用硬件验证
  ```
- **代码位置**: `ota_service.c:232`（调用入口）
- **验证逻辑**: 目前的 `ota_validate_firmware_header` 函数**没有实现**具体的硬件验证逻辑
- **潜在问题**:
  - 函数可能只是返回 `OTA_VALIDATION_OK`，但实际设备上可能有额外的硬件检查
  - 设备可能检查 `ota_header_t` 中的 `Target Information` (0xE0-0x11F, 64 bytes)
  - 当前所有字节都是 0，可能不满足硬件要求
- **概率**: **高**

#### 2.2 目标设备信息缺失
- **OTA header 结构**: `Target Information Section` (64 bytes at 0xE0-0x11F)
- **当前状态**: 全部填充 0
- **可能的问题**:
  - 设备期望有特定的硬件 ID、序列号、或设备类型
  - 例如: `"NE301-HW-v1.0"` 或类似的设备标识
- **概率**: **中**

---

### 3. 分区大小验证（低概率）

#### 3.1 分区大小限制
- **Precheck 配置**:
  ```c
  .validate_partition_size = AICAM_TRUE,  // ✅ 启用分区验证
  ```
- **AI 模型分区大小**: 16MB (0x1000000)
- **我们的固件大小**: 6.16MB ✅
- **概率**: **极低**（已验证）

---

### 4. 网络传输问题（低概率）

#### 4.1 Content-Length 不匹配
- **代码位置**: `api_ota_module.c:336-343`
- **验证逻辑**:
  ```c
  if (expected_content_length > 0) {
      if (header->total_package_size != expected_content_length) {
          return AICAM_ERROR_INVALID_PARAM;
      }
  }
  ```
- **前端上传流程**:
  1. 先读取前 2KB 进行 precheck
  2. 然后上传完整文件
  3. 需要确保两次大小一致
- **概率**: **低**

#### 4.2 数据截断
- **前端读取代码**: `import-firmware.tsx:94`
  ```typescript
  const contentPreview = await sliceFile(file, 2048);
  ```
- **问题**: 如果文件小于 2KB，读取的数据会不足
- **我们的固件**: 6.16MB ✅
- **概率**: **极低**

---

### 5. 时序和并发问题（中概率）

#### 5.1 OTA 服务状态检查
- **代码位置**: `api_ota_module.c:94-97`
- **验证逻辑**:
  ```c
  static aicam_bool_t is_ota_service_running(void) {
      service_state_t state = ota_service_get_state();
      return (state == SERVICE_STATE_RUNNING);
  }
  ```
- **潜在问题**:
  - 如果 OTA 服务正在运行中，precheck 可能被拒绝
  - 可能有其他 OTA 任务正在进行
- **概率**: **中**

#### 5.2 Flash 写入冲突
- **问题**: 如果正在写入其他固件，precheck 可能失败
- **概率**: **低**

---

### 6. Model Package Header 问题（低概率）

#### 6.1 Model Package Magic Number
- **期望值**: `0x314D364E` ("N6M1")
- **当前值**: 已验证正确 ✅
- **概率**: **极低**

#### 6.2 Model Package Version
- **期望值**: `0x030000` (v3.0.0)
- **当前值**: 已验证正确 ✅
- **概率**: **极低**

---

### 7. 签名验证（未知概率）

#### 7.1 数字签名检查
- **Precheck 配置**:
  ```c
  .validate_signature = AICAM_FALSE,  // ❌ Precheck 中未启用
  ```
- **完整上传时**:
  ```typescript
  validate_signature: true  // ✅ 完整上传时启用
  ```
- **潜在问题**:
  - Precheck 通过，但完整上传时签名验证失败
  - OTA header 中 `Security Information Section` (416 bytes at 0x160-0x2FF) 当前全部为 0
  - 设备可能期望有 RSA/PKCS#1 签名
- **概率**: **未知**（取决于设备是否强制签名）

---

### 8. 其他隐藏验证逻辑（中概率）

#### 8.1 CRC32 完整性验证
- **Precheck 配置**:
  ```c
  .validate_crc32 = AICAM_FALSE,  // ❌ Precheck 中未启用
  ```
- **完整上传时**:
  ```typescript
  validate_crc32: true  // ✅ 完整上传时启用
  ```
- **潜在问题**:
  - `header->fw_crc32` 可能不正确
  - 需要验证整个固件数据（跳过 OTA header）的 CRC32
- **概率**: **中**

#### 8.2 文件名验证
- **前端文件名**: `ne301_Model_v3.0.0.1_pkg.bin`
- **潜在要求**:
  - 设备可能对文件名格式有特殊要求
  - 例如: 必须包含特定前缀、版本号格式等
- **概率**: **低**

#### 8.3 时间戳验证
- **OTA header**: `timestamp` 字段 (0x10, Unix timestamp)
- **当前值**: 打包时的时间戳
- **潜在问题**:
  - 设备可能拒绝过期或未来时间的固件
  - 时间戳可能需要与服务器时间同步
- **概率**: **低**

#### 8.4 序列号验证
- **OTA header**: `sequence` 字段 (0x14)
- **当前值**: 1
- **潜在问题**:
  - 设备可能要求序列号严格递增
  - 如果之前上传过序列号 >= 1 的固件，可能会被拒绝
- **概率**: **中**

---

## 二、概率评估与优先级

### 🔴 高优先级（最可能的失败原因）

1. **版本降级检查** (概率: **80%**)
   - 设备当前版本可能 >= 2.0.0.XXXX
   - `allow_downgrade = FALSE`
   - **验证方法**: 查询设备当前版本

2. **硬件兼容性检查** (概率: **70%**)
   - `validate_hardware = TRUE`
   - Target Information 全为 0 可能不满足要求
   - **验证方法**: 检查设备期望的硬件信息

3. **完整上传时的签名验证** (概率: **60%**)
   - Precheck 不验证签名，但完整上传时验证
   - `validate_signature = TRUE`
   - **验证方法**: 查看完整上传时的错误日志

### 🟡 中优先级

4. **时序/并发问题** (概率: **40%**)
   - OTA 服务可能正在运行中
   - **验证方法**: 重试 precheck

5. **序列号验证** (概率: **30%**)
   - 序列号可能需要递增
   - **验证方法**: 使用更大的序列号

6. **完整上传时的 CRC32 验证** (概率: **30%**)
   - Precheck 不验证 CRC32，但完整上传时验证
   - **验证方法**: 验证整个固件的 CRC32

### 🟢 低优先级（已排除或概率极低）

7. **分区大小限制** (概率: **<1%**)
   - 已验证: 6.16MB < 16MB ✅

8. **Magic Number/Header 结构** (概率: **<1%**)
   - 已验证: OTA header 和 Model package header 都正确 ✅

9. **网络传输问题** (概率: **<5%**)
   - 文件大小充足，传输协议正确 ✅

---

## 三、具体的验证方法

### 1. 获取设备当前版本 ⚠️

**方法 1: 通过设备 API**
```bash
# 查询设备信息
curl http://<NE301_IP>/api/v1/system/device-info

# 或
curl http://<NE301_IP>/api/v1/system/version
```

**方法 2: 通过设备控制台**
```bash
# SSH 登录设备
ssh admin@<NE301_IP>

# 查看版本
cat /etc/version
# 或
fw_version
```

**期望输出**:
```json
{
  "version": {
    "major": 2,
    "minor": 1,
    "patch": 0,
    "build": 1234
  }
}
```

---

### 2. 获取详细的 Precheck 错误信息 ⚠️

**方法 1: 浏览器开发者工具**
```javascript
// 1. 打开 NE301 前端
// 2. 按 F12 打开开发者工具
// 3. 切换到 Network 标签
// 4. 上传固件文件
// 5. 查看 precheck 请求的响应

// Precheck 请求
POST /api/v1/system/ota/precheck?firmwareType=ai

// 响应中应该包含详细的错误信息
{
  "code": -1,
  "message": "具体错误原因",
  "error": "详细错误描述"
}
```

**方法 2: 查看设备日志**
```bash
# SSH 登录设备
ssh admin@<NE301_IP>

# 查看 OTA 服务日志
tail -f /var/log/ota.log
# 或
journalctl -u ota-service -f

# 查看系统日志
dmesg | tail -100
```

**期望日志**:
```
[ERROR] Pre-check failed: Firmware type mismatch (header=4, param=2)
[ERROR] Pre-check failed: Version too old: MAJOR 2 < 3
[ERROR] Pre-check failed: Hardware compatibility check failed
```

---

### 3. 测试不同版本号 ⚠️

**方法 1: 使用更高的版本号**
```python
# 修改 backend/app/core/ne301_config.py:230-234
def get_model_version(self) -> NE301Version:
    """获取模型版本号"""
    # 尝试更高的版本号
    return NE301Version(4, 0, 0, 1)  # 改为 4.0.0.1
```

**方法 2: 使用匹配设备主版本的版本号**
```python
# 如果设备版本是 2.1.0.x
def get_model_version(self) -> NE301Version:
    """获取模型版本号"""
    return NE301Version(2, 1, 0, 9999)  # 匹配主版本，更高的 build
```

**方法 3: 使用时间戳生成递增版本号**
```python
def get_model_version(self) -> NE301Version:
    """获取模型版本号 - 基于时间戳"""
    import time
    timestamp = int(time.time())
    major = 3
    minor = 0
    patch = 0
    build = timestamp % 10000
    return NE301Version(major, minor, patch, build)
```

---

### 4. 填充 Target Information ⚠️

**方法: 修改 OTA header 生成逻辑**

```python
# 在 backend/app/core/docker_adapter.py 中的 create_ota_header 函数
# 找到 Target Information Section (0xE0-0x11F)

# 当前代码（全部填充 0）
offset += 64  # All zeros for now

# 修改为填充设备信息
target_info = {
    'hardware_version': b'NE301-HW-v1.0',  # 硬件版本
    'device_id': b'NE301-DEFAULT',         # 设备 ID
    'serial_number': b'12345678',          # 序列号
}

# 填充到 header (需要在 ota_packer.py 中实现)
```

**参考代码**: 修改 `ne301/Script/ota_packer.py:170-171`

```python
# ========== Target Information Section (64 bytes): 0xE0-0x11F ==========
# 填充硬件信息（如果已知设备要求）
hardware_id = "NE301-HW-v1.0"  # 根据实际设备调整
hw_id_bytes = self._pack_string(hardware_id, 32)
self.header_data[offset:offset+32] = hw_id_bytes
offset += 32

# 设备序列号（可选）
serial_number = "DEFAULT"
serial_bytes = self._pack_string(serial_number, 32)
self.header_data[offset:offset+32] = serial_bytes
offset += 32
```

---

### 5. 逐步增加序列号 ⚠️

**方法: 修改序列号生成逻辑**

```python
# 在 backend/app/core/docker_adapter.py 中
# 找到序列号设置（0x14）

# 当前代码
struct.pack_into('<I', self.header_data, offset, 1)  # 0x14: sequence

# 修改为递增序列号
import time
sequence = int(time.time()) % 1000000  # 基于时间戳的序列号
struct.pack_into('<I', self.header_data, offset, sequence)
```

---

### 6. 验证 CRC32 完整性 ⚠️

**方法: 重新计算固件 CRC32**

```python
# 验证脚本: scripts/verify_firmware_crc32.py

import struct
import zlib

def verify_firmware_crc32(firmware_path: str):
    """验证整个固件的 CRC32"""
    with open(firmware_path, 'rb') as f:
        # 跳过 OTA header (1KB)
        f.seek(1024)

        # 读取固件数据
        firmware_data = f.read()

        # 计算 CRC32
        calculated_crc = zlib.crc32(firmware_data) & 0xFFFFFFFF

    # 读取 header 中的 CRC32
    with open(firmware_path, 'rb') as f:
        f.seek(0xB8)  # fw_crc32 offset
        stored_crc = struct.unpack('<I', f.read(4))[0]

    print(f"存储的 CRC32: 0x{stored_crc:08X}")
    print(f"计算的 CRC32: 0x{calculated_crc:08X}")

    if calculated_crc == stored_crc:
        print("✅ CRC32 验证通过")
        return True
    else:
        print("❌ CRC32 不匹配!")
        return False

if __name__ == '__main__':
    import sys
    verify_firmware_crc32(sys.argv[1])
```

**使用方法**:
```bash
python3 scripts/verify_firmware_crc32.py ne301/build/ne301_Model_v3.0.0.1_pkg.bin
```

---

### 7. 测试签名验证（如果需要）⚠️

**方法: 检查是否需要签名**

```bash
# 查看设备固件签名配置
ssh admin@<NE301_IP>
cat /etc/ota/config.json
# 或
grep -r "signature" /etc/ota/
```

**如果需要签名**:
- 需要获取设备的私钥/公钥对
- 使用 RSA/PKCS#1 签名算法对固件进行签名
- 将签名填充到 OTA header 的 `Security Information Section` (0x160-0x2FF)

---

## 四、优先排查顺序

### 第 1 步: 获取详细的错误信息 ⚠️⚠️⚠️

**最优先**: 查看浏览器开发者工具和设备日志

1. 打开浏览器开发者工具 (F12)
2. 切换到 Network 标签
3. 上传固件文件
4. 查看 `/api/v1/system/ota/precheck` 请求的完整响应
5. 查看错误代码和错误消息

**同时**:
```bash
# SSH 登录设备
ssh admin@<NE301_IP>

# 实时查看日志
tail -f /var/log/ota.log
journalctl -u ota-service -f
```

**期望**: 错误信息会明确指出失败的具体原因

---

### 第 2 步: 检查设备当前版本 ⚠️⚠️

**目的**: 确认是否是版本降级问题

```bash
# 查询设备版本
curl http://<NE301_IP>/api/v1/system/device-info
```

**如果设备版本 >= 2.0.0.XXXX**:
- 问题: 版本降级保护
- 解决: 使用更高的版本号（如 4.0.0.1）

**如果设备版本 < 2.0.0.XXXX**:
- 不是版本问题，继续其他排查

---

### 第 3 步: 测试不同版本号 ⚠️⚠️

**方法**: 修改 `backend/app/core/ne301_config.py:230-234`

```python
def get_model_version(self) -> NE301Version:
    """获取模型版本号"""
    # 尝试更高的版本号
    return NE301Version(5, 0, 0, 1)  # 改为 5.0.0.1
```

**重新构建并测试**:
```bash
# 重新生成固件
cd backend
python -m app.main

# 或者直接使用测试脚本
python3 scripts/test_version_5.py
```

---

### 第 4 步: 检查硬件兼容性 ⚠️

**方法**: 填充 Target Information

1. 修改 `ne301/Script/ota_packer.py:170-171`
2. 填充设备硬件信息（见上文示例）
3. 重新生成固件
4. 测试 precheck

---

### 第 5 步: 验证 CRC32 ⚠️

**方法**: 运行 CRC32 验证脚本

```bash
python3 scripts/verify_firmware_crc32.py ne301/build/ne301_Model_v3.0.0.1_pkg.bin
```

**如果 CRC32 不匹配**:
- 检查固件生成逻辑
- 确保 CRC32 计算时跳过了 OTA header

---

### 第 6 步: 增加序列号 ⚠️

**方法**: 使用时间戳生成序列号

```python
# 修改 backend/app/core/docker_adapter.py
import time
sequence = int(time.time()) % 1000000
struct.pack_into('<I', self.header_data, offset, sequence)
```

---

### 第 7 步: 检查时序/并发问题 ⚠️

**方法**: 重试 precheck

1. 等待几分钟，确保没有其他 OTA 任务在进行
2. 重新上传固件
3. 观察 precheck 是否通过

---

### 第 8 步: 检查签名验证（最后手段）

**方法**: 查看设备签名配置

```bash
ssh admin@<NE301_IP>
cat /etc/ota/config.json
```

**如果需要签名**:
- 联系设备厂商获取签名密钥
- 实现签名逻辑

---

## 五、快速诊断脚本

创建一个快速诊断脚本 `scripts/diagnose_ota_issue.py`:

```python
#!/usr/bin/env python3
"""
NE301 OTA 问题快速诊断脚本
"""

import sys
import requests
import struct

def check_device_version(device_ip: str):
    """检查设备当前版本"""
    try:
        response = requests.get(f"http://{device_ip}/api/v1/system/device-info", timeout=5)
        data = response.json()
        version = data.get("version", {})
        print(f"✅ 设备版本: {version.get('major')}.{version.get('minor')}.{version.get('patch')}.{version.get('build')}")
        return version
    except Exception as e:
        print(f"❌ 无法获取设备版本: {e}")
        return None

def test_precheck(device_ip: str, firmware_path: str):
    """测试 precheck"""
    try:
        # 读取前 2KB
        with open(firmware_path, 'rb') as f:
            header_data = f.read(2048)

        # 发送 precheck 请求
        files = {'file': ('firmware.bin', header_data, 'application/octet-stream')}
        response = requests.post(
            f"http://{device_ip}/api/v1/system/ota/precheck?firmwareType=ai",
            files=files,
            timeout=10
        )

        print(f"Precheck 响应状态: {response.status_code}")
        print(f"Precheck 响应内容: {response.text}")

        if response.status_code == 200:
            print("✅ Precheck 通过")
            return True
        else:
            print("❌ Precheck 失败")
            return False

    except Exception as e:
        print(f"❌ Precheck 请求失败: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("使用方法: python diagnose_ota_issue.py <device_ip> [firmware_path]")
        sys.exit(1)

    device_ip = sys.argv[1]
    firmware_path = sys.argv[2] if len(sys.argv) > 2 else "ne301/build/ne301_Model_v3.0.0.1_pkg.bin"

    print("=" * 60)
    print("NE301 OTA 问题诊断")
    print("=" * 60)

    # 1. 检查设备版本
    print("\n1. 检查设备版本...")
    device_version = check_device_version(device_ip)

    # 2. 测试 precheck
    print("\n2. 测试 Precheck...")
    test_precheck(device_ip, firmware_path)

    # 3. 给出建议
    print("\n" + "=" * 60)
    print("诊断建议:")
    print("=" * 60)

    if device_version:
        major = device_version.get('major', 0)
        minor = device_version.get('minor', 0)
        if major >= 3:
            print("⚠️  设备版本较高，建议使用 4.0.0.1 或更高的版本号")
        elif major == 2 and minor > 0:
            print("⚠️  设备版本是 2.x.x，建议使用 2.1.0.9999 或更高的版本号")
        else:
            print("✅ 版本号应该不是问题")

    print("\n如果 precheck 仍然失败，请查看浏览器开发者工具中的详细错误信息")

if __name__ == '__main__':
    main()
```

**使用方法**:
```bash
python3 scripts/diagnose_ota_issue.py 192.168.1.100 ne301/build/ne301_Model_v3.0.0.1_pkg.bin
```

---

## 六、总结与建议

### 最可能的原因（按概率排序）

1. **版本降级保护** (80%) - 设备版本 >= 2.0.0.XXXX
2. **硬件兼容性检查** (70%) - Target Information 缺失
3. **完整上传时的签名验证** (60%) - 需要 RSA 签名
4. **时序/并发问题** (40%) - OTA 服务正在运行
5. **序列号验证** (30%) - 序列号需要递增

### 推荐的排查顺序

1. **立即**: 查看浏览器开发者工具和设备日志，获取详细错误信息
2. **第一**: 检查设备当前版本，确认是否是版本问题
3. **第二**: 测试更高的版本号（4.0.0.1 或 5.0.0.1）
4. **第三**: 填充 Target Information（硬件信息）
5. **第四**: 验证 CRC32 完整性
6. **第五**: 增加序列号
7. **最后**: 检查是否需要签名验证

### 关键文件列表

- `/Users/harryhua/Documents/GitHub/model-converter/ne301/Custom/Services/Web/api/api_ota_module.c:296-397` - Precheck 实现
- `/Users/harryhua/Documents/GitHub/model-converter/ne301/Custom/Services/OTA/ota_service.c:232-329` - 版本和硬件验证
- `/Users/harryhua/Documents/GitHub/model-converter/ne301/Custom/Core/System/ota_header.c:18-54` - Header 验证
- `/Users/harryhua/Documents/GitHub/model-converter/backend/app/core/ne301_config.py:230-234` - 版本号配置
- `/Users/harryhua/Documents/GitHub/model-converter/ne301/Script/ota_packer.py:170-171` - Target Information 填充

---

**报告生成时间**: 2026-03-16
**报告版本**: 1.0
**下一步**: 获取 NE301 设备的详细错误日志
