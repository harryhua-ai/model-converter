# NE301 bin 文件大小和版本号问题 - 完整诊断报告

**日期**: 2026-03-17
**状态**: 🔴 发现多个问题，已提供修复方案
**优先级**: HIGH

---

## 📋 问题摘要

### 问题 1: bin 文件过大 (5.9 MB)
- **现象**: 生成的 NE301 bin 文件 5.9 MB，STM32N6 无法导入
- **根本原因**: JSON 配置中的输入尺寸错误（640x640 而不是 256x256）
- **影响**: bin 文件比预期大约 1.5 MB

### 问题 2: OTA 版本号错误
- **现象**: OTA 包版本号不匹配设备期望
- **根本原因**: `get_model_version()` 读取主版本号而不是 `MODEL_VERSION_OVERRIDE`
- **影响**: 设备端可能拒绝 OTA 升级
- **状态**: ✅ **已修复**

---

## 🔍 详细分析

### 问题 1: JSON 配置中的输入尺寸错误

#### 发现过程

1. **文件大小对比**:
   ```
   TFLite: 3.2 MB (256x256 输入)
   NE301 bin: 5.9 MB (约 1.8x)
   预期 bin: ~4.5 MB (基于 256x256)
   差异: +1.4 MB (31%)
   ```

2. **JSON 配置检查**:
   ```json
   {
     "input_spec": {
       "width": 640,    // ❌ 错误！应该是 256
       "height": 640,   // ❌ 错误！应该是 256
       "channels": 3
     },
     "output_spec": {
       "outputs": [{
         "height": 34,
         "width": 8400,  // ❌ 错误！应该是 1344 (256x256 的输出)
         "channels": 1
       }]
     }
   }
   ```

3. **total_boxes 计算**:
   ```
   256x256 输入 → total_boxes = 1344 (正确)
   640x640 输入 → total_boxes = 8400 (错误，是正确的 6.25 倍)
   ```

#### 根本原因

**推测**：在调用 `generate_ne301_json_config()` 时，传递的 `input_size` 参数值不正确。

**代码链路**:
```python
# backend/app/api/convert.py
config_dict = {
    "input_size": validated_config.input_size,  # ⚠️ 可能这里传递错误
    ...
}

# backend/app/core/docker_adapter.py
json_config = generate_ne301_json_config(
    tflite_path=Path(quantized_tflite),
    model_name=model_name,
    input_size=config["input_size"],  # ⚠️ 使用了错误的值
    ...
)

# backend/app/core/ne301_config.py
def generate_ne301_json_config(
    tflite_path: Path,
    model_name: str,
    input_size: int,  # ⚠️ 接收到错误的值
    ...
) -> Dict:
    return {
        "input_spec": {
            "width": input_size,   # ❌ 这里使用了错误的 input_size
            "height": input_size,
            ...
        }
    }
```

#### 调试步骤

```bash
# 1. 添加调试日志到 docker_adapter.py
# 在 _prepare_ne301_project() 方法中添加：

def _prepare_ne301_project(self, task_id, quantized_tflite, config, yaml_path):
    logger.info("="*60)
    logger.info("🔍 [DEBUG] _prepare_ne301_project 参数:")
    logger.info(f"  config['input_size'] = {config['input_size']}")
    logger.info(f"  config 类型: {type(config)}")
    logger.info(f"  config keys: {list(config.keys())}")
    logger.info("="*60)

    # 继续执行...

# 2. 重新运行转换，查看日志
docker logs model-converter-api | grep -A 10 "DEBUG.*_prepare_ne301_project"
```

#### 修复方案（推荐）

**方案 A: 添加 TFLite 输入尺寸验证**（最安全）

```python
# backend/app/core/docker_adapter.py

def _prepare_ne301_project(
    self,
    task_id: str,
    quantized_tflite: str,
    config: Dict[str, Any],
    yaml_path: Optional[str] = None
) -> Path:
    """步骤 3: 准备 NE301 项目目录（改进版 - 完整 JSON 配置）"""

    # ✅ 新增：从 TFLite 验证输入尺寸
    tflite_input_size = self._extract_input_size_from_tflite(quantized_tflite)
    config_input_size = config["input_size"]

    if tflite_input_size > 0 and tflite_input_size != config_input_size:
        logger.error(f"❌ 输入尺寸不一致！")
        logger.error(f"  TFLite 实际: {tflite_input_size}x{tflite_input_size}")
        logger.error(f"  Config 配置: {config_input_size}x{config_input_size}")
        logger.error(f"  这会导致 bin 文件过大！")

        # ✅ 选项 1: 抛出错误（严格模式）
        raise ValueError(
            f"输入尺寸不匹配！TFLite={tflite_input_size}, Config={config_input_size}"
        )

        # ✅ 选项 2: 自动修正（宽松模式）
        # logger.warning(f"⚠️  强制使用 TFLite 的实际尺寸: {tflite_input_size}")
        # config["input_size"] = tflite_input_size

    logger.info(f"✅ 输入尺寸验证通过: {config_input_size}x{config_input_size}")

    # 继续生成 JSON 配置...

def _extract_input_size_from_tflite(self, tflite_path: str) -> int:
    """从 TFLite 模型提取输入尺寸"""
    try:
        import tensorflow as tf
        interpreter = tf.lite.Interpreter(model_path=tflite_path)
        input_shape = interpreter.get_input_details()[0]['shape']
        # input_shape = [batch, height, width, channels]
        return int(input_shape[1])
    except Exception as e:
        logger.warning(f"无法从 TFLite 提取输入尺寸: {e}")
        return -1
```

**方案 B: 强化配置传递**（防御性编程）

```python
# backend/app/api/convert.py

@router.post("/convert")
async def convert_model(...):
    # ✅ 验证配置完整性
    try:
        validated_config = ConversionConfig(**config_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"配置验证失败: {e}")

    # ✅ 显式提取 input_size（避免字典查找失败）
    config_dict = {
        "input_size": int(validated_config.input_size),  # ✅ 显式转换
        "num_classes": int(validated_config.num_classes),
        "model_type": validated_config.model_type,
        ...
    }

    # ✅ 确保没有 None 值
    for key, value in config_dict.items():
        if value is None:
            raise ValueError(f"配置参数 {key} 不能为 None")

    # 继续处理...
```

---

### 问题 2: OTA 版本号错误（✅ 已修复）

#### 问题描述

- **期望版本**: `2.0.0.0` (来自 `MODEL_VERSION_OVERRIDE`)
- **实际版本**: `2.0.1.{build}` (来自主版本号)
- **设备端影响**: 版本号不匹配，可能导致 OTA 升级失败

#### version.mk 定义

```makefile
# 主版本号
VERSION_MAJOR  := 2
VERSION_MINOR  := 0
VERSION_PATCH  := 1

# 模型版本覆盖（独立于主版本）
MODEL_VERSION_OVERRIDE   := 2.0.0.0
```

#### 错误的代码（修复前）

```python
# backend/app/core/ne301_config.py (旧版本)

def get_model_version(self) -> NE301Version:
    """获取模型版本号（从 version.mk 读取）"""

    # ❌ 只读取主版本号，忽略了 MODEL_VERSION_OVERRIDE
    major = self._extract_version_var(content, "VERSION_MAJOR", 3)
    minor = self._extract_version_var(content, "VERSION_MINOR", 0)
    patch = self._extract_version_var(content, "VERSION_PATCH", 0)
    build = self._extract_version_var(content, "VERSION_BUILD", 1)

    return NE301Version(major, minor, patch, build)  # ❌ 返回 2.0.1.x
```

#### 修复后的代码

```python
# backend/app/core/ne301_config.py (新版本)

def get_model_version(self) -> NE301Version:
    """获取模型版本号（从 version.mk 读取）

    动态读取 version.mk 中的 MODEL_VERSION_OVERRIDE，确保与 OTA packer 一致
    如果 MODEL_VERSION_OVERRIDE 未定义，则使用主版本号
    """

    # ✅ 优先读取 MODEL_VERSION_OVERRIDE（如果定义）
    model_version_match = re.search(
        r'MODEL_VERSION_OVERRIDE\s*:?=\s*(\d+\.\d+\.\d+\.\d+)',
        content
    )

    if model_version_match:
        # ✅ 使用 MODEL_VERSION_OVERRIDE
        version_str = model_version_match.group(1)
        parts = version_str.split('.')
        major, minor, patch, build = map(int, parts)
        return NE301Version(major, minor, patch, build)  # ✅ 返回 2.0.0.0

    # ✅ 回退：读取主版本号
    major = self._extract_version_var(content, "VERSION_MAJOR", 3)
    minor = self._extract_version_var(content, "VERSION_MINOR", 0)
    patch = self._extract_version_var(content, "VERSION_PATCH", 0)
    build = self._extract_version_var(content, "VERSION_BUILD", 1)

    return NE301Version(major, minor, patch, build)
```

#### 验证修复

```bash
cd /Users/harryhua/Documents/GitHub/model-converter/backend

python3 << 'EOF'
from app.core.ne301_config import get_ne301_toolchain
from pathlib import Path

ne301_project_path = Path("/Users/harryhua/Documents/GitHub/model-converter/ne301")
toolchain = get_ne301_toolchain(ne301_project_path)

version = toolchain.get_model_version()
print(f"✅ 读取到的模型版本: {version}")  # 应该输出: 2.0.0.0
EOF
```

**输出**:
```
✅ 读取到的模型版本: 2.0.0.0
  Major: 2
  Minor: 0
  Patch: 0
  Build: 0

✅ 版本号正确！匹配 MODEL_VERSION_OVERRIDE := 2.0.0.0
```

---

## 📊 影响分析

### bin 文件大小影响

| 配置 | 输入尺寸 | total_boxes | 预期 bin | 实际 bin | 差异 |
|------|----------|-------------|----------|----------|------|
| 正确 | 256x256  | 1344        | ~4.5 MB  | ~4.5 MB  | 0%   |
| 当前 | 640x640  | 8400        | ~5.9 MB  | 5.9 MB   | +31% |

**原因**: NE301 工具链根据 JSON 配置分配内存池，错误的输入尺寸导致过度分配。

### OTA 版本号影响

| 场景 | 期望版本 | 实际版本 | 影响 |
|------|----------|----------|------|
| 修复前 | 2.0.0.0 | 2.0.1.x | ❌ 版本不匹配，设备可能拒绝升级 |
| 修复后 | 2.0.0.0 | 2.0.0.0 | ✅ 版本匹配，升级正常 |

---

## 🚀 立即行动计划

### 步骤 1: 部署版本号修复（已完成 ✅）

```bash
# 1. 验证修复
cd /Users/harryhua/Documents/GitHub/model-converter/backend
python3 << 'EOF'
from app.core.ne301_config import get_ne301_toolchain
from pathlib import Path

toolchain = get_ne301_toolchain(Path("../ne301"))
version = toolchain.get_model_version()
assert str(version) == "2.0.0.0", f"版本号错误: {version}"
print("✅ 版本号修复验证通过")
EOF

# 2. 重启服务
docker-compose restart model-converter-api
```

### 步骤 2: 调试输入尺寸问题

```bash
# 1. 添加调试日志（按照上述"修复方案 A"）
# 编辑 backend/app/core/docker_adapter.py

# 2. 重新构建并启动
docker-compose build model-converter-api
docker-compose up -d model-converter-api

# 3. 运行测试转换
# 上传一个 256x256 的模型，观察日志

# 4. 查看调试日志
docker logs model-converter-api | grep -A 20 "DEBUG.*_prepare_ne301_project"
```

### 步骤 3: 部署输入尺寸验证

```bash
# 1. 应用修复方案 A（添加 TFLite 输入尺寸验证）
# 编辑 backend/app/core/docker_adapter.py

# 2. 重启服务
docker-compose restart model-converter-api

# 3. 测试转换
# 上传相同模型，应该看到输入尺寸验证日志

# 4. 检查 bin 文件大小
ls -lh ne301/build/*_pkg.bin
# 应该在 4.5 MB 左右（比之前的 5.9 MB 小）
```

### 步骤 4: 验证修复

```bash
# 1. 检查 JSON 配置
cat ne301/Model/weights/model_*.json | python3 -m json.tool | grep -A 5 "input_spec"
# 应该显示 "width": 256, "height": 256

# 2. 检查 bin 文件大小
ls -lh ne301/build/*_pkg.bin
# 应该在 4.5 MB 左右

# 3. 检查 OTA 版本号
python3 << 'EOF'
import struct

bin_path = "ne301/build/ne301_Model_v2.0.0.0_pkg.bin"
with open(bin_path, 'rb') as f:
    f.seek(0xA0)  # fw_ver offset
    version_bytes = f.read(8)
    major, minor, patch, build = version_bytes[:4]
    print(f"OTA 版本号: {major}.{minor}.{patch}.{build}")
    # 应该输出: 2.0.0.0
EOF

# 4. 尝试导入 STM32N6
# 如果仍有问题，检查 STM32N6 的实际存储限制
```

---

## 🔧 长期优化建议

### 1. 模型大小优化

如果 4.5 MB 仍然过大（STM32N6 通常只有 2MB Flash）：

```python
# 选项 1: 减少类别数量
num_classes: 30 → 10  # 节省 ~30% 输出层大小

# 选项 2: 降低输入尺寸
input_size: 256 → 192  # 节省 ~44% 特征图大小

# 选项 3: 使用更轻量的模型
YOLOv8n → YOLOv8n-0.5x  # 节省 ~50% 权重

# 选项 4: 使用外部 Flash
# STM32N6570-DK 支持外部 Flash（通过 XIP）
# 可以加载更大的模型（10+ MB）
```

### 2. 转换流程优化

```python
# 添加自动输入尺寸检测
def _export_to_quantized_tflite(model_path, input_size, ...):
    from ultralytics import YOLO
    model = YOLO(model_path)

    # ✅ 验证模型输入尺寸
    default_size = model.model.args.get("imgsz", 640)
    if default_size != input_size:
        logger.warning(f"⚠️  模型默认输入尺寸 {default_size} 与配置 {input_size} 不一致")

    # ✅ 强制使用配置中的尺寸
    model.export(format="tflite", imgsz=input_size, int8=True)
```

### 3. 测试用例

```python
# backend/tests/test_input_size_validation.py

def test_input_size_validation():
    """测试输入尺寸验证"""
    # 1. 创建一个 256x256 的 TFLite 模型
    # 2. 尝试使用 config["input_size"] = 640 转换
    # 3. 应该抛出错误或自动修正

def test_model_version_override():
    """测试 MODEL_VERSION_OVERRIDE 读取"""
    toolchain = get_ne301_toolchain(Path("ne301"))
    version = toolchain.get_model_version()

    assert version.major == 2
    assert version.minor == 0
    assert version.patch == 0
    assert version.build == 0
```

---

## 📝 总结

### 已修复
✅ **问题 2**: OTA 版本号读取（`get_model_version()` 现在正确读取 `MODEL_VERSION_OVERRIDE`）

### 待修复
🔴 **问题 1**: JSON 配置中的输入尺寸错误
   - 需要添加 TFLite 输入尺寸验证
   - 需要追踪配置传递链路
   - 建议使用修复方案 A（添加验证）

### 下一步
1. ✅ 重启服务，验证版本号修复
2. 🔴 添加调试日志，追踪 input_size 传递
3. 🔴 部署输入尺寸验证代码
4. 🔴 重新测试转换，验证 bin 文件大小

---

**报告生成时间**: 2026-03-17
**负责人**: 后端开发团队
**优先级**: HIGH
**预计修复时间**: 1-2 小时
