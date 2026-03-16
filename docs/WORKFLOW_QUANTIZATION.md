# 模型量化工作流详解

## 概述

本文档详细说明 NE301 Model Converter 的模型量化流程，包括推荐方法和备用方法。

## 量化方法对比

| 方法 | 推荐度 | 优点 | 缺点 | 适用场景 |
|------|--------|------|------|----------|
| YOLOv8 直接导出 | ⭐⭐⭐⭐⭐ | 快速、稳定、无形状错误 | 仅支持 YOLOv8 | 大多数场景 |
| ST 量化脚本 | ⭐⭐⭐ | 通用性强、支持多种模型 | 需要 SavedModel 中间格式 | 非 YOLOv8 模型 |

## 推荐方法：YOLOv8 直接导出

### 流程图

```
PyTorch 模型 (.pt/.pth)
    ↓
加载 YOLOv8 模型
    ↓
配置导出参数
    - format: tflite
    - imgsz: 480/640
    - int8: True
    ↓
处理校准数据集（可选）
    - ZIP 文件自动解压
    - 递归查找图片目录
    ↓
执行 YOLO.export()
    ↓
验证输出形状
    - 检查 TFLite 输出
    - 确保形状正确 (1, 34, 1344)
    ↓
量化 TFLite 模型 (int8)
```

### 详细步骤

#### 步骤 1: 加载模型

```python
from ultralytics import YOLO

model = YOLO("model.pt")
```

#### 步骤 2: 配置导出参数

```python
export_args = {
    "format": "tflite",      # 输出格式
    "imgsz": 640,            # 输入尺寸
    "int8": True,            # int8 量化
    "data": calib_data_path  # 校准数据集路径（可选）
}
```

**参数说明**:

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| format | str | 输出格式 | "tflite" |
| imgsz | int | 输入尺寸 | 640 |
| int8 | bool | 是否进行 int8 量化 | False |
| data | str | 校准数据集路径 | None |

#### 步骤 3: 处理校准数据集

**ZIP 文件要求**:
- 文件格式: `.zip`
- 图片格式: `.jpg`, `.jpeg`, `.png`
- 图片数量: 32-200 张（推荐）
- 目录结构: 任意（系统自动递归查找）

**处理逻辑**:
```python
def _extract_calibration_dataset(calib_dataset_path: str) -> str:
    """解压校准数据集 ZIP 文件"""
    if not calib_dataset_path.endswith('.zip'):
        return calib_dataset_path

    # 解压到临时目录
    extract_dir = tempfile.mkdtemp(prefix="calibration_")
    with zipfile.ZipFile(calib_dataset_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    # 递归查找图片目录
    for root, dirs, files in os.walk(extract_dir):
        image_files = [f for f in files
                      if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if image_files:
            return root

    return extract_dir
```

#### 步骤 4: 执行导出

```python
# 执行导出
tflite_path = model.export(**export_args)

# 验证输出
import tensorflow as tf
interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
output_details = interpreter.get_output_details()[0]
output_shape = output_details['shape']

print(f"输出形状: {output_shape}")
# 预期: [1, 34, 1344] (for 640x640 input)
```

#### 步骤 5: 输出形状验证

**正确的输出形状**:

| 输入尺寸 | 输出形状 | 说明 |
|---------|---------|------|
| 256 | `[1, 34, 1344]` | 检测框数量: 1344 |
| 480 | `[1, 34, 2520]` | 检测框数量: 2520 |
| 640 | `[1, 34, 1344]` | 检测框数量: 1344 |

**错误示例**:
```
❌ 输出形状错误: [1, 34, 8400]
   原因: 使用了废弃的 SavedModel 方法
   解决: 确保使用 _export_to_quantized_tflite() 方法
```

## 备用方法：ST 量化脚本

### 使用场景

- 非 YOLOv8 模型
- 需要自定义量化参数
- 需要更细粒度的控制

### 流程图

```
PyTorch 模型 (.pt/.pth)
    ↓
导出 SavedModel 格式
    ↓
配置 Hydra 参数
    - model.model_path
    - model.input_shape
    - quantization.calib_dataset_path
    ↓
运行 ST 量化脚本
    ↓
量化 TFLite 模型 (int8)
```

### 配置文件示例

`backend/tools/quantization/user_config_quant.yaml`:

```yaml
model:
  model_path: "/path/to/saved_model"
  input_shape: [640, 640, 3]

quantization:
  calib_dataset_path: "/path/to/calibration_images"
  export_path: "/app/outputs"
  max_calib_images: 200
  fake: false
```

### 执行命令

```bash
python -m tools.quantization.tflite_quant \
  --config-name user_config_quant \
  model.model_path=/path/to/saved_model \
  model.input_shape=[640,640,3] \
  quantization.calib_dataset_path=/path/to/calibration_images
```

## 校准数据集最佳实践

### 数据准备

**图片数量**:
- 最小: 32 张
- 推荐: 100-200 张
- 最大: 200 张（内存保护）

**图片内容**:
- 代表实际使用场景
- 包含各种光照、角度、背景
- 覆盖目标物体的各种状态

**数据分布**:
- 与训练数据分布相似
- 包含不同难度的样本
- 避免过度重复的场景

### 常见问题

#### Q1: 校准数据集需要标注吗？

**A**: 不需要。校准数据集只需要原始图片，不需要标注文件。

#### Q2: 校准数据集和训练数据集可以相同吗？

**A**: 可以，但建议使用独立的验证集作为校准数据集，以提高泛化能力。

#### Q3: 没有 GPU 可以运行量化吗？

**A**: 可以。量化过程主要在 CPU 上运行，速度较快（通常几分钟）。

#### Q4: fake quantization 和真实量化的区别？

**A**:
- **Fake quantization**: 模拟量化效果，精度损失较大
- **真实量化**: 使用真实校准数据，精度损失较小

#### Q5: 如何评估量化后的模型精度？

**A**:
1. 使用测试集评估 mAP 指标
2. 对比量化前后的精度差异
3. 检查输出形状是否正确

## 性能基准

### 转换时间（参考值）

| 输入尺寸 | YOLOv8 导出 | ST 量化脚本 | 总耗时 |
|---------|------------|-----------|--------|
| 256 | 30-45s | N/A | ~30s |
| 480 | 45-60s | N/A | ~45s |
| 640 | 60-90s | N/A | ~60s |

### 模型大小对比

| 模型类型 | Float32 | Int8 | 压缩比 |
|---------|---------|------|--------|
| YOLOv8n | 6.2 MB | 1.6 MB | 3.9x |
| YOLOv8s | 22 MB | 5.7 MB | 3.9x |
| YOLOv8m | 52 MB | 13.4 MB | 3.9x |

## 故障排查

### 错误：输出形状不匹配

**症状**:
```
ValueError: 输出形状错误: (1, 34, 8400) != (1, 34, 1344)
```

**原因**:
使用了废弃的 SavedModel 方法

**解决**:
确保使用 `_export_to_quantized_tflite()` 方法

### 错误：校准数据集解压失败

**症状**:
```
RuntimeError: 解压校准数据集失败: [Errno 2] No such file or directory
```

**原因**:
- ZIP 文件损坏
- 文件路径错误
- 权限不足

**解决**:
1. 检查 ZIP 文件完整性
2. 确认文件路径正确
3. 检查文件权限

### 错误：内存不足

**症状**:
```
MemoryError: Unable to allocate array
```

**原因**:
校准图片过多或过大

**解决**:
1. 减少校准图片数量（最大 200 张）
2. 降低图片分辨率
3. 使用更小的 batch size

## 参考

- [Ultralytics 文档](https://docs.ultralytics.com/)
- [TensorFlow Lite 量化指南](https://www.tensorflow.org/lite/performance/quantization)
- [ST Edge AI 文档](https://www.st.com/en/embedded-software/stedgeai-core.html)