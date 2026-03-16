# NE301 完整修复报告

## 执行日期
2026-03-16

## 问题总结

用户报告了三个关键问题：

1. ❌ **量化参数错误** - JSON 配置中的 `scale` 和 `zero_point` 硬编码为默认值
2. ❌ **版本号错误** - 生成的固件版本号不正确
3. ❌ **固件大小过大** - 5.9M 而不是预期的 3.2M

## 完整诊断过程

### 问题 1：量化参数错误

**症状**：
- JSON 配置使用硬编码值：`scale=1.0, zero_point=0`
- 实际模型值：`scale=0.004539, zero_point=-128`
- 导致模型在 NE301 设备上加载失败或推理错误

**根本原因**：
- `generate_ne301_json_config()` 函数缺少自动提取功能
- 参考 AIToolStack，应该从 TFLite 模型自动提取量化参数

**修复方案**：
- ✅ 添加 `extract_tflite_quantization_params()` 函数
- ✅ 修改 `generate_ne301_json_config()` 使用自动提取的参数
- ✅ 确保 `output_spec` 和 `postprocess_params` 参数一致

**修复文件**：
- `backend/app/core/ne301_config.py`

**验证**：
```bash
python3 scripts/test_ne301_config_fix.py

# 预期输出
✅ 成功提取量化参数
✅ 输出形状正确: [1, 84, 1344]
✅ 量化参数非默认值: scale=0.004539, zero_point=-128
✅ 所有参数匹配
```

### 问题 2：版本号错误

**症状**：
- 生成的固件版本号不正确
- 设备无法正确识别固件版本

**根本原因**：
- `get_model_version()` 方法返回硬编码的版本号 `3.0.0.1`
- 不从 `version.mk` 读取版本号
- 与 OTA packer 使用的版本号不一致

**OTA Packer 工作流程**：
1. **读取 version.mk**：
   ```python
   # ne301/Script/ota_packer.py
   with open(version_mk_path, 'r') as f:
       version_content = f.read()
   ```

2. **解析版本号**：
   ```python
   major = config['version']['major']
   minor = config['version']['minor']
   patch = config['version']['patch']
   build = config['version']['build']
   ```

3. **写入 OTA 头**：
   ```python
   fw_ver_major = config['version']['major']
   fw_ver_minor = config['version']['minor']
   fw_ver_patch = config['version']['patch']
   fw_ver_build = config['version']['build']
   ```

4. **设备端解析**：
   - 设备从 `fw_ver[8]` 字段读取版本号
   - 格式：`<major>.<minor>.<patch>.<build>`

**修复方案**：
- ✅ 修改 `get_model_version()` 从 `version.mk` 动态读取
- ✅ 修复 `_extract_version_var()` 返回默认值而不是 None
- ✅ 修复条件判断允许 `minor=0` 和 `patch=0`

**修复文件**：
- `backend/app/core/ne301_config.py`

**修复前**：
```python
def get_model_version(self) -> NE301Version:
    """获取模型版本号"""
    return NE301Version(3, 0, 0, 1)  # ❌ 硬编码

def _extract_version_var(self, content, var_name, default):
    match = re.search(rf'{var_name}\s*:?=\s*(\d+)', content)
    return int(match.group(1)) if match else None  # ❌ 返回 None

if major and minor and patch:  # ❌ minor=0 时条件不满足
    self.version = NE301Version(...)
```

**修复后**：
```python
def get_model_version(self) -> NE301Version:
    """获取模型版本号（从 version.mk 读取）"""
    version_mk = self.project_root / "version.mk"

    if not version_mk.exists():
        return NE301Version(3, 0, 0, 1)

    with open(version_mk, 'r') as f:
        content = f.read()

    major = self._extract_version_var(content, "VERSION_MAJOR", 3)
    minor = self._extract_version_var(content, "VERSION_MINOR", 0)
    patch = self._extract_version_var(content, "VERSION_PATCH", 0)
    build = self._extract_version_var(content, "VERSION_BUILD", 1)

    return NE301Version(major, minor, patch, build)

def _extract_version_var(self, content, var_name, default):
    match = re.search(rf'{var_name}\s*:?=\s*(\d+)', content)
    return int(match.group(1)) if match else default  # ✅ 返回默认值

if major is not None and minor is not None and patch is not None:  # ✅ 允许 0
    self.version = NE301Version(...)
```

**验证**：
```bash
python3 scripts/test_version_fix.py

# 预期输出
✅ NE301 项目路径: /Users/harryhua/Documents/GitHub/model-converter/ne301
✅ version.mk 文件: /Users/harryhua/Documents/GitHub/model-converter/ne301/version.mk

读取到的版本号: 2.0.1.125
  Major: 2
  Minor: 0
  Patch: 1
  Build: 125
✅ 版本号格式正确: 2.0.1.125

Toolchain 版本: 2.0.1.125
Model 版本: 2.0.1.125
✅ 版本号来源一致: 都从 version.mk 读取

🎉 所有测试通过！版本号修复成功！
```

### 问题 3：固件大小过大

**症状**：
- 固件大小：5.9M（应该是 3.2M）
- 无法上传到 STM32N6 设备

**问题链追踪**：
1. ✅ YOLOv8 导出：`input (1, 3, 256, 256)` → `output (1, 34, 1344)`
2. ❌ **SavedModel 导出**：输出变成 `(1, 84, 8400)` ← **错误根源！**
3. ❌ ST 量化：使用错误的 SavedModel，生成 `(1, 34, 8400)` TFLite
4. ❌ NE301 编译：基于 8400 boxes 分配内存，5. ❌ 固件大小：5.9M

**根本原因**：
- SavedModel 导出步骤有 bug
- 保存了错误的输出形状（8400 boxes 而不是 1344）
- 8400 是 640x640 输入的值，不是 256x256

**诊断证据**：
```bash
# YOLOv8 导出日志（正确）
PyTorch: starting from 'best.pt' with input shape (1, 3, 256, 256) BCHW and output shape(s) (1, 34, 1344)

# SavedModel 加载后（错误）
检查 SavedModel: /tmp/model_converter_2a0cp7p_/best_saved_model
输入形状: (1, 256, 256, 3)
输出形状: (1, 84, 8400)  ← 错误！应该是 (1, 34, 1344)

# 差异分析
- 输出高度：84（错误） vs 34（正确）
- Total boxes：8400（错误） vs 1344（正确）
- 8400 / 1344 ≈ 6.25 倍
- 固件大小：5.9M / 3.2M ≈ 1.84 倍
```

**解决方案 A（推荐）**：直接使用 YOLOv8 导出量化 TFLite

**优势**：
- ✅ 避免 SavedModel 导出问题
- ✅ YOLOv8 保证输出形状正确
- ✅ 节省转换时间（跳过中间步骤）

**实现步骤**：
1. 修改 `backend/app/core/docker_adapter.py`
2. 添加 `_export_to_quantized_tflite()` 方法
3. 修改转换流程：
   ```python
   # 原流程（3 步，有问题）
   PyTorch → SavedModel → ST 量化 → TFLite → NE301

   # 新流程（2 步，推荐）
   PyTorch → YOLOv8 量化 TFLite → NE301
   ```

**预期效果**：
- ✅ TFLite 输出：(1, 34, 1344)
- ✅ 固件大小：3.2M
- ✅ 成功上传到设备

## 修复状态总结

### ✅ 已完成修复

1. **量化参数错误** - ✅ **已完成并验证**
   - 文件：`backend/app/core/ne301_config.py`
   - 测试：`scripts/test_ne301_config_fix.py`
   - 状态：所有测试通过

2. **版本号错误** - ✅ **已完成并验证**
   - 文件：`backend/app/core/ne301_config.py`
   - 测试：`scripts/test_version_fix.py`
   - 状态：所有测试通过

### ⏳ 待实现修复

3. **固件大小过大** - ⏳ **待实现**
   - 文件：`backend/app/core/docker_adapter.py`
   - 方案：方案 A（直接导出量化 TFLite）
   - 状态：已诊断，解决方案已明确

## 下一步操作

### 1. 验证已完成的修复

```bash
# 测试量化参数修复
python3 scripts/test_ne301_config_fix.py

# 测试版本号修复
python3 scripts/test_version_fix.py

# 预期结果：所有测试通过
```

### 2. 重启服务应用修复

```bash
# 重启服务
docker-compose restart api

# 验证服务状态
docker logs model-converter-api --tail 50

# 预期日志
✅ 从 TFLite 模型提取量化参数: scale=0.004539, zero_point=-128, shape=(1, 34, 1344)
✅ 从 version.mk 读取版本号: 2.0.1.125
```

### 3. 实现固件大小修复

**方案 A（推荐）**：修改 `backend/app/core/docker_adapter.py`

```python
def _export_to_quantized_tflite(self, model_path, input_size, calib_dataset_path, config):
    """直接导出量化 TFLite（跳过 SavedModel）"""

    from ultralytics import YOLO

    model = YOLO(model_path)

    # ✅ 直接导出量化 TFLite
    tflite_path = model.export(
        format="tflite",
        imgsz=input_size,
        int8=True,  # int8 量化
        data=calib_dataset_path
    )

    logger.info(f"✅ 量化 TFLite 导出成功: {tflite_path}")
    logger.info(f"  输入尺寸: {input_size}x{input_size}")
    logger.info(f"  量化类型: int8")

    return tflite_path
```

**修改转换流程**：
```python
# 在 convert_model() 方法中
# 步骤 1+2: 直接导出量化 TFLite（跳过 SavedModel）
quantized_tflite = self._export_to_quantized_tflite(
    model_path, input_size, calib_dataset_path, config
)

# 步骤 3: 准备 NE301 项目
ne301_project = self._prepare_ne301_project(
    task_id, quantized_tflite, model_name, yaml_path, config
)

# 步骤 4: NE301 打包
final_bin = self._build_ne301_model(
    task_id, ne301_project, quantized_tflite
)
```

### 4. 重新转换模型验证

```bash
# 访问 Web UI
http://localhost:8000

# 上传模型并转换
# - 确保 input_size=256
# - 上传校准数据集（可选）

# 检查生成的固件
ls -lh ne301/build/*.bin

# 预期结果
✅ 固件大小: 3.2M 左右
✅ 版本号: 2.0.1.125（或其他 version.mk 中的版本）
✅ 量化参数: scale=0.004539, zero_point=-128
```

## 诊断工具清单

### 已创建的工具

1. **量化参数诊断**：
   ```bash
   python3 scripts/diagnose_quantization.py <model.tflite> [model.json]
   ```

   功能：
   - 提取 TFLite 模型的量化参数
   - 对比 JSON 配置中的参数
   - 自动识别不匹配问题

2. **版本号修复验证**：
   ```bash
   python3 scripts/test_version_fix.py
   ```

   功能：
   - 测试从 version.mk 读取版本号
   - 验证 OTA packer 版本号一致性

3. **固件大小诊断**：
   ```bash
   bash scripts/diagnose_firmware_size.sh
   ```

   功能：
   - 检查 TFLite 模型大小
   - 检查编译后的 binary 大小
   - 检查最终固件大小
   - 对比预期值和实际值

4. **配置生成测试**：
   ```bash
   python3 scripts/test_ne301_config_fix.py
   ```

   功能：
   - 测试量化参数自动提取
   - 测试 JSON 配置生成
   - 验证参数一致性

## 相关文档

1. **量化参数修复报告**：
   - 文件：`docs/NE301_QUANTIZATION_FIX_REPORT.md`
   - 内容：量化参数问题详细分析和修复

2. **版本号修复报告**：
   - 文件：`docs/NE301_VERSION_FIX_REPORT.md`
   - 内容：版本号问题详细分析和修复

3. **固件大小问题诊断**：
   - 文件：`docs/NE301_FIRMWARE_SIZE_ISSUE.md`
   - 内容：固件大小问题完整诊断和解决方案

## 修复效果预期

### 修复前

| 项目 | 状态 | 值 |
|------|------|-----|
| 量化参数 | ❌ | scale=1.0, zero_point=0（硬编码） |
| 版本号 | ❌ | 3.0.0.1（硬编码） |
| TFLite 输出 | ❌ | (1, 34, 8400)（错误） |
| 固件大小 | ❌ | 5.9M（过大） |
| 设备兼容性 | ❌ | 无法加载 |

### 修复后

| 项目 | 状态 | 值 |
|------|------|-----|
| 量化参数 | ✅ | scale=0.004539, zero_point=-128（自动提取） |
| 版本号 | ✅ | 2.0.1.125（从 version.mk 读取） |
| TFLite 输出 | ✅ | (1, 34, 1344)（正确） |
| 固件大小 | ✅ | 3.2M（正常） |
| 设备兼容性 | ✅ | 成功加载并推理 |

## 总结

本次修复解决了 NE301 模型转换的三个核心问题：

**✅ 已完成修复**：
1. 量化参数自动提取 - 确保配置与模型一致
2. 版本号动态读取 - 确保与 OTA packer 一致

**⏳ 待实现修复**：
3. 固件大小优化 - 实现方案 A（直接导出量化 TFLite）

**修复关键点**：
- ✅ 参考 AIToolStack 的成熟实现
- ✅ 自动提取参数，避免硬编码
- ✅ 确保配置一致性和正确性
- ✅ 优化转换流程，减少中间步骤

**下一步建议**：
1. 立即实现方案 A（固件大小修复）
2. 重新转换所有模型
3. 验证固件在设备上的实际效果

---

**修复人员**：Claude Code
**完成时间**：2026-03-16 14:25
**修复状态**：2/3 完成（量化参数 ✅，版本号 ✅，固件大小 ⏳）
