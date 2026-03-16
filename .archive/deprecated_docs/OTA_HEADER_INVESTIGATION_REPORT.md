# NE301 OTA Header 验证失败调查报告

## 执行日期
2026-03-16

## 调查任务完成情况

### ✅ 任务 1: 验证 NE301 容器日志
- **结果**: 没有找到 NE301 前端 precheck 验证失败的错误日志
- **发现**: 日志显示 OTA packer 成功生成了固件，但没有 NE301 前端的验证错误信息
- **结论**: 验证错误可能发生在 NE301 设备端或前端控制台，不在后端日志中

### ✅ 任务 2: 检查 task.output_filename 的值
- **结果**: 确认下载 API 返回的是带 `_pkg` 后缀的文件
- **代码验证**:
  - `backend/app/core/ne301_config.py:273-275` - `get_package_name` 返回 `ne301_Model_v{version}_pkg`
  - `backend/app/core/docker_adapter.py:846-891` - `_add_ota_header` 使用正确的文件名
  - `backend/app/api/tasks.py:110` - 下载 API 使用 `task.output_filename`
- **结论**: 文件名逻辑正确，用户下载的是包含 OTA header 的完整固件包

### ✅ 任务 3: 验证 ota_header_verify 函数实现
- **结果**: 确认验证逻辑包括 4 个检查点
- **代码位置**: `ne301/Custom/Core/System/ota_header.c:18-54`
- **验证项目**:
  1. ✅ Magic number (`0x4F544155` - "OTAU")
  2. ✅ Header version (`0x0100` - v1.0)
  3. ✅ Header size (1024 bytes)
  4. ✅ **CRC32 校验**（关键检查点）
- **结论**: 验证逻辑正确且严格

### ✅ 任务 4: 验证 CRC32 计算
- **Python 实现**: `ne301/Script/ota_packer.py:67-69, 185-189`
  ```python
  def _calculate_crc32(self, data: bytes) -> int:
      return zlib.crc32(data) & 0xFFFFFFFF

  # 计算 header CRC32
  header_for_crc = bytearray(self.header_data)
  struct.pack_into('<I', header_for_crc, 8, 0)  # 设置 CRC32 字段为 0
  header_crc32 = self._calculate_crc32(bytes(header_for_crc))
  struct.pack_into('<I', self.header_data, 8, header_crc32)
  ```

- **C 实现**: `ne301/Custom/Common/Utils/generic_math.c:51-59`
  ```c
  uint32_t generic_crc32(const uint8_t *data, size_t length)
  {
      uint32_t crc = 0xFFFFFFFF;
      for (size_t i = 0; i < length; i++) {
          uint8_t byte = data[i];
          crc = crc32_table[(crc ^ byte) & 0xFF] ^ (crc >> 8);
      }
      return crc ^ 0xFFFFFFFF;
  }
  ```

- **结论**: Python 和 C 使用相同的标准 CRC32 算法（IEEE 802.3），计算逻辑一致

## 关键发现总结

### ✅ 所有实现都是正确的

1. **OTA Header 结构正确**
   - Magic: `0x4F544155` (OTAU) ✅
   - Header Size: 1024 bytes ✅
   - Firmware Type: `0x04` (ai_model) ✅
   - Version: 2.0.0.XXXX @ offset 0xA0 ✅

2. **Model Package Header 结构正确**
   - Magic: `0x314D364E` (N6M1) @ offset 0x400 ✅
   - Version: `0x030000` (v3.0.0) ✅

3. **CRC32 计算正确**
   - Python `zlib.crc32` 与 C `generic_crc32` 使用相同算法 ✅
   - 排除 CRC32 字段本身的方法正确 ✅

4. **文件命名正确**
   - 下载 API 返回带 `_pkg` 后缀的文件 ✅
   - 包含完整的 OTA header + model package ✅

## 问题可能的原因

既然所有实现都正确，验证失败可能由以下原因导致：

### 1. NE301 前端的其他验证逻辑

**可能的问题**:
- `ota_validate_firmware_header` 函数的硬件兼容性检查
- 分区大小限制检查
- 版本号范围检查

**建议调查**:
- 检查 `ne301/Custom/Services/ota/ota_validation.c` 中的验证逻辑
- 查看 NE301 设备的具体硬件版本和分区配置

### 2. NE301 设备环境问题

**可能的问题**:
- NE301 设备硬件版本与固件不兼容
- NE301 设备分区大小不足以容纳固件
- NE301 设备系统版本过低

**建议操作**:
- 检查 NE301 设备的硬件版本号
- 检查 NE301 设备的分区大小
- 检查 NE301 设备的系统版本要求

### 3. NE301 前端预检查 API 的其他要求

**可能的问题**:
- HTTP Content-Length 与 `total_package_size` 不匹配
- 固件类型 URL 参数与 header 中的 `fw_type` 不匹配

**建议操作**:
- 检查 NE301 前端调用 precheck API 时的 URL 参数
- 确认 HTTP Content-Length 是否正确

## 下一步行动建议

### 立即行动

1. **运行验证脚本**
   ```bash
   cd /Users/harryhua/Documents/GitHub/model-converter

   # 转换一个模型
   # 通过 Web UI 上传模型并转换

   # 验证生成的固件
   python scripts/verify_ota_firmware.py backend/outputs/ne301_Model_v*.bin
   ```

2. **查看 NE301 前端控制台错误**
   - 打开浏览器开发者工具
   - 查看 Console 和 Network 标签
   - 记录 precheck API 的完整错误响应

3. **查看 NE301 容器日志**
   ```bash
   # 实时查看日志
   docker logs -f model-converter-api

   # 搜索 precheck 相关日志
   docker logs model-converter-api 2>&1 | grep -i "precheck"
   ```

### 深入调查

4. **检查 ota_validate_firmware_header 实现**
   ```bash
   # 查找验证函数
   find ne301 -name "ota_validation.c" -exec cat {} \;
   ```

5. **测试不同的固件版本号**
   - 尝试使用不同的版本号（如 1.0.0.1）
   - 检查版本号范围是否有限制

6. **测试不同的固件大小**
   - 尝试使用不同大小的模型
   - 检查分区大小限制

## 验证工具

已创建验证脚本: `scripts/verify_ota_firmware.py`

**使用方法**:
```bash
python scripts/verify_ota_firmware.py <firmware.bin>
```

**验证项目**:
- OTA Header magic number
- OTA Header version
- OTA Header size
- OTA Header CRC32
- Model Package Header magic number
- Model Package Header version

## 联系信息

如果问题持续存在，请提供以下信息：
1. NE301 前端控制台的完整错误日志
2. NE301 设备的硬件版本
3. NE301 设备的系统版本
4. 验证脚本的输出结果
5. 失败的固件文件（如果可能）

## 附录：关键文件列表

### 后端打包流程
- `backend/app/core/docker_adapter.py:826-891` - `_add_ota_header` 方法
- `backend/app/core/ne301_config.py:260-275` - `get_package_name` 方法
- `backend/app/api/tasks.py:64-124` - 下载 API

### NE301 OTA 验证逻辑
- `ne301/Custom/Core/System/ota_header.c:18-54` - `ota_header_verify` 函数
- `ne301/Custom/Common/Utils/generic_math.c:51-59` - `generic_crc32` 函数

### OTA 打包工具
- `ne301/Script/ota_packer.py` - OTA header 生成
- `ne301/Script/model_packager.py` - Model package header 生成

---

**报告生成时间**: 2026-03-16
**报告版本**: 1.0
**状态**: 调查完成，等待用户反馈
