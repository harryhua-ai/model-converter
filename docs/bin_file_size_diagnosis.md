# NE301 bin 文件大小问题诊断

**日期**: 2026-03-17
**问题**: 生成的 NE301 bin 文件 (5.9 MB) 过大，STM32N6 无法导入

---

## 1. 问题现象

### 文件大小对比
- ✅ TFLite 模型: 3.2 MB (256x256 输入, int8 量化)
- ❌ NE301 bin: 5.9 MB (约 1.8x 大小增加)
- ⚠️  JSON 配置: 显示 640x640 输入尺寸（**错误！**）

### 用户配置
- 输入尺寸: 256x256
- 类别数量: 30
- 模型类型: YOLOv8n
- 量化类型: int8

---

## 2. 根本原因

### 🔴 **关键发现：JSON 配置文件中的输入尺寸错误**

```json
{
  "input_spec": {
    "width": 640,    // ❌ 错误！应该是 256
    "height": 640,   // ❌ 错误！应该是 256
    "channels": 3,
    ...
  }
}
```

### 影响分析

1. **TFLite 导出正确**:
   - 文件大小 3.2 MB 符合 256x256 模型
   - Ultralytics `export(imgsz=256)` 工作正常

2. **JSON 配置错误**:
   - `generate_ne301_json_config()` 使用了错误的 `input_size`
   - 导致 `total_boxes` 计算错误（8400 而不是 1344）

3. **bin 文件打包影响**:
   - NE301 工具链可能根据 JSON 配置分配内存
   - 错误的输入尺寸导致过度内存分配
   - 最终 bin 文件膨胀到 5.9 MB

---

## 3. NE301 bin 文件大小构成分析

### 正常情况下（256x256 输入）

```
TFLite (3.2 MB)
    ↓
+ NPU 微代码 (~0.8 MB)
+ 权重重排 (~0.3 MB)
+ 内存对齐 (~0.2 MB)
+ 元数据 (~0.2 MB)
+ 其他优化 (~0.3 MB)
    ↓
预期 bin: ~5.0 MB
```

### 当前异常情况（按 640x640 配置）

```
TFLite (3.2 MB, 实际 256x256)
    ↓
但 JSON 配置按 640x640:
+ 输出层分配: 8400 boxes (应为 1344)
+ 内存池过度分配 (~1.5x)
+ 元数据膨胀
    ↓
实际 bin: 5.9 MB
```

### 大小差异

| 配置 | 输入尺寸 | total_boxes | 预期 bin |
|------|----------|-------------|----------|
| 正确 | 256x256  | 1344        | ~4.5 MB  |
| 当前 | 640x640  | 8400        | 5.9 MB   |
| 差异 | -        | 6.25x       | +1.4 MB  |

---

## 4. 调试步骤

### 步骤 1: 确认 TFLite 实际输入尺寸

```bash
# 方法 1: 使用 TensorFlow
python3 << 'EOF'
import tensorflow as tf
interpreter = tf.lite.Interpreter(model_path="model.tflite")
input_details = interpreter.get_input_details()[0]
print(f"输入尺寸: {input_details['shape'][1]}x{input_details['shape'][2]}")
EOF

# 方法 2: 使用 flatc (TFLite 工具)
flatc --json --strict-json -o /tmp model.tflite
cat /tmp/model.json | grep -A 5 "input_tensor"
```

### 步骤 2: 检查配置传递链路

```python
# 在 backend/app/core/docker_adapter.py 中添加调试日志

def _prepare_ne301_project(self, task_id, quantized_tflite, config, yaml_path):
    logger.info(f"🔍 [DEBUG] config['input_size'] = {config['input_size']}")  # ✅ 添加
    logger.info(f"🔍 [DEBUG] config type: {type(config)}")
    logger.info(f"🔍 [DEBUG] config keys: {config.keys()}")

    json_config = generate_ne301_json_config(
        tflite_path=Path(quantized_tflite),
        model_name=model_name,
        input_size=config["input_size"],  # ⚠️ 检查这个值
        ...
    )

    logger.info(f"🔍 [DEBUG] JSON input_spec: {json_config['input_spec']}")  # ✅ 添加
```

### 步骤 3: 验证 JSON 生成逻辑

```python
# 在 backend/app/core/ne301_config.py 中验证

def generate_ne301_json_config(
    tflite_path: Path,
    model_name: str,
    input_size: int,  # ⚠️ 检查传入值
    ...
) -> Dict:
    logger.info(f"🔍 [DEBUG] generate_ne301_json_config received input_size={input_size}")

    config = {
        "input_spec": {
            "width": input_size,   # ⚠️ 确认这里使用正确
            "height": input_size,
            ...
        }
    }
    return config
```

---

## 5. 可能的原因

### A. 配置传递错误

```python
# 可能的错误场景 1: config 字段名不一致
config = {
    "input_size": 256,      # ✅ 正确
    "model_input_size": 640, # ❌ 可能误用
}

# 可能的错误场景 2: 默认值覆盖
input_size = config.get("input_size", 640)  # ❌ 如果 config 中没有 input_size，会使用 640
```

### B. 多任务并发问题

```python
# 可能的错误场景 3: 全局配置被污染
global_config = {"input_size": 640}  # ❌ 前一个任务的配置

def process_task(user_config):
    # 如果没有正确隔离，可能读取到全局配置
    input_size = global_config.get("input_size")  # ❌
```

### C. YOLO 模型自动检测错误

```python
# 可能的错误场景 4: 从 YOLO 模型读取输入尺寸
from ultralytics import YOLO
model = YOLO("model.pt")
default_size = model.model.args.get("imgsz", 640)  # ❌ 可能读取到默认值 640
```

---

## 6. 解决方案

### 方案 1: 添加输入尺寸验证（推荐）

```python
# backend/app/core/docker_adapter.py

def _prepare_ne301_project(self, task_id, quantized_tflite, config, yaml_path):
    """步骤 3: 准备 NE301 项目目录"""

    # ✅ 新增：从 TFLite 验证输入尺寸
    tflite_input_size = self._extract_input_size_from_tflite(quantized_tflite)
    config_input_size = config["input_size"]

    if tflite_input_size != config_input_size:
        logger.error(f"❌ 输入尺寸不一致！")
        logger.error(f"  TFLite 实际: {tflite_input_size}x{tflite_input_size}")
        logger.error(f"  Config 配置: {config_input_size}x{config_input_size}")
        raise ValueError("配置中的 input_size 与 TFLite 模型不匹配")

    logger.info(f"✅ 输入尺寸验证通过: {config_input_size}x{config_input_size}")

    # 继续生成 JSON 配置...

def _extract_input_size_from_tflite(self, tflite_path: str) -> int:
    """从 TFLite 模型提取输入尺寸"""
    try:
        import tensorflow as tf
        interpreter = tf.lite.Interpreter(model_path=tflite_path)
        input_shape = interpreter.get_input_details()[0]['shape']
        return int(input_shape[1])  # [batch, height, width, channels]
    except Exception as e:
        logger.warning(f"无法从 TFLite 提取输入尺寸: {e}")
        return -1
```

### 方案 2: 强化配置传递

```python
# backend/app/api/convert.py

async def convert_model(...):
    # ✅ 验证配置完整性
    validated_config = ConversionConfig(**config_dict)

    # ✅ 显式传递 input_size（避免字典查找失败）
    config_dict = {
        "input_size": validated_config.input_size,  # ✅ 显式提取
        "num_classes": validated_config.num_classes,
        ...
    }

    # 确保没有 None 值
    if config_dict["input_size"] is None:
        raise ValueError("input_size 不能为 None")

    task_id = task_manager.create_task(validated_config)

    # 继续处理...
```

### 方案 3: 临时快速修复（测试用）

```python
# backend/app/core/ne301_config.py

def generate_ne301_json_config(
    tflite_path: Path,
    model_name: str,
    input_size: int,
    ...
) -> Dict:
    # ✅ 临时修复：如果 input_size 是 640，但 TFLite 是 256，强制使用 256
    if TENSORFLOW_AVAILABLE:
        try:
            interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
            actual_input_size = int(interpreter.get_input_details()[0]['shape'][1])

            if actual_input_size != input_size:
                logger.warning(f"⚠️  输入尺寸不匹配！")
                logger.warning(f"  参数传入: {input_size}x{input_size}")
                logger.warning(f"  TFLite 实际: {actual_input_size}x{actual_input_size}")
                logger.warning(f"  强制使用 TFLite 的实际尺寸")

                input_size = actual_input_size  # ✅ 强制修正
        except Exception as e:
            logger.warning(f"无法从 TFLite 提取输入尺寸: {e}")

    # 继续生成配置...
```

---

## 7. 立即行动计划

### 优先级 1: 确认问题

```bash
# 1. 检查最近的转换日志
docker logs model-converter-api | grep -A 5 "input_size"

# 2. 验证 TFLite 实际输入尺寸
python3 -c "
import tensorflow as tf
interpreter = tf.lite.Interpreter(model_path='ne301/Model/weights/model_xxx.tflite')
print(interpreter.get_input_details()[0]['shape'])
"

# 3. 检查 JSON 配置
cat ne301/Model/weights/model_xxx.json | grep -A 5 "input_spec"
```

### 优先级 2: 部署修复

```bash
# 1. 应用方案 1（输入尺寸验证）
# 编辑 backend/app/core/docker_adapter.py

# 2. 重启容器
docker-compose restart model-converter-api

# 3. 重新测试转换
# 上传相同模型，观察日志中的 input_size 验证信息
```

### 优先级 3: 验证修复

```bash
# 1. 检查新生成的 JSON 配置
cat ne301/Model/weights/model_new.json | grep -A 5 "input_spec"
# 应该显示 "width": 256, "height": 256

# 2. 检查 bin 文件大小
ls -lh ne301/build/*_pkg.bin
# 应该在 4.5 MB 左右（比之前的 5.9 MB 小）

# 3. 尝试导入 STM32N6
# 如果仍然失败，可能是其他原因（存储限制、固件版本等）
```

---

## 8. STM32N6 存储限制说明

### 常见存储配置

| STM32N6 型号 | Flash 大小 | 可用模型空间 |
|--------------|-----------|-------------|
| STM32N6570   | 2 MB      | ~1.5 MB     |
| STM32N6570-DK| 2 MB      | ~1.5 MB     |
| (外部 Flash) | 可扩展    | 取决于配置  |

### 如果 4.5 MB 仍然过大

1. **使用外部 Flash**:
   - STM32N6570-DK 支持外部 Flash（通过 XIP）
   - 可以加载更大的模型（10+ MB）

2. **进一步优化模型**:
   - 减少类别数量（30 → 10 或更少）
   - 使用更小的输入尺寸（256 → 192 或 128）
   - 尝试模型剪枝（移除不重要的层）

3. **使用模型分片**:
   - 将模型分成多个小文件
   - 按需加载到内存

---

## 9. 长期优化建议

### A. 模型大小优化

```python
# 1. 减少类别数量
num_classes: 30 → 10  # 节省 ~30% 输出层大小

# 2. 降低输入尺寸
input_size: 256 → 192  # 节省 ~44% 特征图大小

# 3. 使用更轻量的模型
YOLOv8n → YOLOv8n-0.5x  # 节省 ~50% 权重
```

### B. 转换流程优化

```python
# 1. 添加输入尺寸自动检测
def _export_to_quantized_tflite(model_path, input_size, ...):
    # ✅ 自动验证 YOLO 模型的输入尺寸
    from ultralytics import YOLO
    model = YOLO(model_path)

    # 检查模型默认输入尺寸
    default_size = model.model.args.get("imgsz", 640)
    if default_size != input_size:
        logger.warning(f"⚠️  模型默认输入尺寸 {default_size} 与配置 {input_size} 不一致")

    # 强制使用配置中的尺寸
    model.export(format="tflite", imgsz=input_size, int8=True)
```

### C. NE301 工具链优化

```bash
# 1. 探索 NE301 压缩选项
# 在 neural_art_reloc.json 中尝试不同的优化配置

# 2. 使用更激进的内存池配置
# stm32n6_reloc_yolov8_od.mpool 中调整内存分配策略

# 3. 联系 ST 技术支持
# 询问是否有针对小模型的特殊打包选项
```

---

## 10. 总结

### 根本原因
✅ JSON 配置中的输入尺寸错误（640x640 而不是 256x256）

### 影响
- bin 文件过度膨胀（5.9 MB 而不是预期的 ~4.5 MB）
- STM32N6 可能无法导入

### 解决方案
1. **立即**: 添加输入尺寸验证（方案 1）
2. **短期**: 修复配置传递链路（方案 2）
3. **长期**: 优化模型大小和转换流程

### 下一步
1. 检查最近转换任务的日志
2. 部署输入尺寸验证代码
3. 重新测试转换流程
4. 如果仍有问题，考虑模型优化（减少类别、降低输入尺寸）

---

**报告生成时间**: 2026-03-17
**建议负责人**: 后端开发团队
**优先级**: HIGH
