# NE301 固件大小问题 - 完整诊断报告

## 执行日期
2026-03-16

## 问题描述

**用户反馈**：
- 固件 .bin 包太大（5.9M）
- 正常大小应该是 3.2M 左右
- 设备：STM32N6

## 诊断结果

### 完整问题链

1. **YOLOv8 导出**：
   - ✅ 使用 256x256 输入
   - ✅ 输出形状：(1, 34, 1344)
   - 日志：`input shape (1, 3, 256, 256) BCHW and output shape(s) (1, 34, 1344)`

2. **SavedModel 导出**：
   - ❌ 输出形状变成：(1, 84, 8400)
   - ❌ **这是问题的根源！**
   - 可能原因：SavedModel 保存了错误的输入尺寸或使用了默认的 640x640

3. **ST 量化**：
   - ❌ 使用错误的 SavedModel
   - ❌ 生成 TFLite 输出：(1, 34, 8400)
   - 日志：`shape=(1, 34, 8400)`

4. **NE301 编译**：
   - ❌ 基于 8400 boxes 分配内存
   - ❌ 固件大小：5.9M（应该是 3.2M）

### 根本原因

**SavedModel 导出步骤有问题**：
- YOLOv8 的 `export(format="saved_model")` 没有正确保存输入尺寸
- 或者模型本身是 640x640 训练的，SavedModel 使用了训练尺寸

### 关键证据

```bash
# YOLOv8 导出日志（正确）
PyTorch: starting from 'best.pt' with input shape (1, 3, 256, 256) BCHW and output shape(s) (1, 34, 1344)

# SavedModel 加载后（错误）
检查 SavedModel: /tmp/model_converter_2a0cp7p_/best_saved_model
输入形状: (1, 256, 256, 3)
输出形状: (1, 84, 8400)  ← 错误！应该是 (1, 34, 1344)
```

**差异分析**：
- 输出高度：84（错误） vs 34（正确）
- Total boxes：8400（错误）vs 1344（正确）
- 8400 / 1344 ≈ 6.25 倍
- 固件大小：5.9M / 3.2M ≈ 1.84 倍

## 解决方案

### 方案 A：直接使用 YOLOv8 导出量化 TFLite（推荐）✅

**优势**：
- ✅ 避免 SavedModel 导出问题
- ✅ YOLOv8 保证输出形状正确
- ✅ 节省转换时间（跳过中间步骤）

**实现**：

```python
# 修改 backend/app/core/docker_adapter.py

def _export_to_quantized_tflite(self, model_path, input_size, calib_dataset_path, config):
    """直接导出量化 TFLite（跳过 SavedModel）"""

    from ultralytics import YOLO

    model = YOLO(model_path)

    # ✅ 直接导出量化 TFLite
    tflite_path = model.export(
        format="tflite",
        imgsz=input_size,
        int8=True,  # int8 量化
        data=calib_dataset_path  # 校准数据集
    )

    logger.info(f"✅ 量化 TFLite 导出成功: {tflite_path}")
    logger.info(f"  输入尺寸: {input_size}x{input_size}")
    logger.info(f"  量化类型: int8")

    return tflite_path
```

**修改转换流程**：
```python
# 原流程（3 步）
PyTorch → SavedModel → ST 量化 → TFLite → NE301

# 新流程（2 步）
PyTorch → YOLOv8 量化 TFLite → NE301
```

### 方案 B：修复 SavedModel 导出

**实现**：

```python
def _export_to_saved_model(self, model_path, input_size, config):
    """导出 SavedModel 并验证输出形状"""

    from ultralytics import YOLO
    import tensorflow as tf

    model = YOLO(model_path)

    # ✅ 1. 检查模型训练尺寸
    trained_size = model.model.args.get('imgsz', 640)
    if isinstance(trained_size, list):
        trained_size = trained_size[0]

    if trained_size != input_size:
        logger.warning(f"⚠️  模型训练尺寸 ({trained_size}) ≠ 目标尺寸 ({input_size})")
        logger.info("🔧 调整模型输入尺寸...")

        # ✅ 2. 先导出 TFLite（保证输出形状正确）
        tflite_temp = model.export(format="tflite", imgsz=input_size, int8=False)
        logger.info(f"✅ 临时 TFLite: {tflite_temp}")

        # ✅ 3. 使用 TFLite 重新导入并保存为 SavedModel
        # （这里需要使用 TensorFlow 转换工具）
        # ...
    else:
        # 直接导出 SavedModel
        saved_model_path = model.export(format="saved_model", imgsz=input_size, int8=False)

    # ✅ 4. 验证输出形状
    interpreter = tf.lite.Interpreter(model_path=saved_model_path)
    output_shape = interpreter.get_output_details()[0]['shape']
    expected_shape = (1, 4 + config['num_classes'], 1344 if input_size == 256 else 8400)

    if output_shape != expected_shape:
        raise ValueError(f"SavedModel 输出形状错误: {output_shape} != {expected_shape}")

    return saved_model_path
```

## 临时解决方案（用户）

**如果已经转换了模型但固件过大**：

1. **验证问题**：
   ```bash
   python3 scripts/diagnose_firmware_size.sh
   ```

2. **检查 JSON 配置**：
   ```bash
   cat ne301/Model/weights/model_*.json | grep total_boxes
   ```

   如果 `total_boxes=8400` 且 `input_size=256`，说明存在此问题

3. **重新转换**：
   - 使用修复后的代码（方案 A 或 B）
   - 确保 `input_size` 参数正确传递

## 预期效果

**修复前**：
- TFLite 输出：(1, 34, 8400) ❌
- 固件大小：5.9M ❌
- 无法上传到设备 ❌

**修复后**：
- TFLite 输出：(1, 34, 1344) ✅
- 固件大小：3.2M ✅
- 成功上传到设备 ✅

## 下一步操作

1. **实现方案 A**（推荐）：
   - 修改 `backend/app/core/docker_adapter.py`
   - 添加 `_export_to_quantized_tflite()` 方法
   - 修改 `convert_model()` 调用新方法

2. **重启服务**：
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

3. **重新转换模型**：
   - 访问 Web UI：http://localhost:8000
   - 上传模型并转换
   - 确保 `input_size=256`

4. **验证固件大小**：
   ```bash
   ls -lh ne301/build/*.bin
   ```

   预期：3.2M 左右

## 相关文档

- [量化参数修复报告](NE301_QUANTIZATION_FIX_REPORT.md)
- [固件大小诊断脚本](../scripts/diagnose_firmware_size.sh)
- [修复指南脚本](../scripts/fix_firmware_size.py)

---

**修复状态**：⏳ **待实现**

**推荐方案**：方案 A（直接使用 YOLOv8 导出量化 TFLite）

**预计修复时间**：30-60 分钟

**关键文件**：
- `backend/app/core/docker_adapter.py` - 主要修改文件
- `backend/tools/quantization/tflite_quant.py` - ST 量化工具（可选保留）

---

**修复人员**：Claude Code
**创建时间**：2026-03-16
