# NE301 固件大小修复实施报告

## 执行日期
2026-03-16

## 修复状态
✅ **已完成实施**

---

## 问题回顾

### 症状
- 固件大小：**5.9M**（应该是 **3.2M**）
- 无法上传到 STM32N6 设备
- 输出形状错误：(1, 34, 8400) 而不是 (1, 34, 1344)

### 根本原因

**问题链追踪**：
1. ✅ YOLOv8 导出：`input (1, 3, 256, 256)` → `output (1, 34, 1344)`
2. ❌ **SavedModel 导出**：输出变成 `(1, 84, 8400)` ← **错误根源！**
3. ❌ ST 量化：使用错误的 SavedModel，生成 `(1, 34, 8400)` TFLite
4. ❌ NE301 编译：基于 8400 boxes 分配内存
5. ❌ 固件大小：5.9M

**差异分析**：
- 输出 boxes：8400 / 1344 ≈ **6.25 倍**
- 固件大小：5.9M / 3.2M ≈ **1.84 倍**

---

## 解决方案 A：直接导出量化 TFLite ✅

### 修复策略

**跳过有问题的 SavedModel 导出步骤，直接使用 YOLOv8 的 int8 量化导出**

**新流程**：
```
[步骤 1] PyTorch → 量化 TFLite (0-60%)
    └─ YOLO.export(format="tflite", int8=True, data=calibration.zip)
        ✅ 输出形状: (1, 34, 1344)

[步骤 2] TFLite 验证 (包含在步骤 1)
    └─ TensorFlow Lite Interpreter 检查输出形状
        ✅ 确认: total_boxes=1344 (正确)

[步骤 3] NE301 项目准备 (60-70%)
    ├─ 创建目录结构
    ├─ 复制量化模型 (正确形状)
    └─ 生成 model_config.json
        ✅ 正确: total_boxes=1344

[步骤 4] NE301 打包 (70-100%)
    ├─ ST Edge AI 编译 (基于 1344 boxes 分配内存)
    ├─ 执行 make 命令
    └─ 生成 model.bin
        ✅ 正确: 固件大小 3.2M
```

---

## 代码修改详情

### 1. 添加新方法：`_export_to_quantized_tflite()`

**位置**：`backend/app/core/docker_adapter.py` (第 456-555 行)

**功能**：
- 直接导出量化 TFLite（跳过 SavedModel）
- 自动处理校准数据集（支持 ZIP 解压）
- 验证输出形状是否正确
- 检测并报告形状错误

**关键代码**：
```python
def _export_to_quantized_tflite(
    self,
    model_path: str,
    input_size: int,
    calib_dataset_path: Optional[str],
    config: Dict[str, Any]
) -> str:
    """步骤 1+2: PyTorch → 量化 TFLite（推荐方法）"""
    from ultralytics import YOLO
    import tensorflow as tf

    # 加载模型
    model = YOLO(model_path)

    # ✅ 直接导出量化 TFLite
    export_args = {
        "format": "tflite",
        "imgsz": input_size,
        "int8": True,  # int8 量化
    }

    if actual_calib_path and Path(actual_calib_path).exists():
        export_args["data"] = actual_calib_path

    tflite_path = model.export(**export_args)

    # ✅ 验证输出形状
    interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
    output_details = interpreter.get_output_details()[0]
    output_shape = output_details['shape']

    # 计算预期的 total_boxes
    expected_boxes = {
        256: 1344,  # 3 * (32*32 + 16*16 + 8*8)
        320: 2100,
        416: 3549,
        512: 5376,
        640: 8400,
    }

    expected = expected_boxes.get(input_size)
    if expected:
        actual_boxes = output_shape[2] if len(output_shape) > 2 else output_shape[1]

        if actual_boxes == expected:
            logger.info(f"✅ 输出形状正确: {output_shape}")
        else:
            raise ValueError(
                f"输出形状错误: {output_shape} != (1, 34, {expected})"
            )

    return str(tflite_path)
```

### 2. 修改主转换流程：`convert_model()`

**位置**：`backend/app/core/docker_adapter.py` (第 240-274 行)

**变更**：
- 合并步骤 1 和步骤 2 为单一调用
- 减少转换步骤：4 步 → 3 步
- 更新进度百分比

**修改前**：
```python
# 步骤 1: PyTorch → TFLite (0-30%)
tflite_path = self._export_tflite(model_path, config["input_size"])

# 步骤 2: TFLite → 量化 TFLite (30-60%)
quantized_tflite = self._quantize_tflite(
    tflite_path,
    config["input_size"],
    calib_dataset_path,
    config
)

# 步骤 3: 准备 NE301 项目 (60-70%)
# 步骤 4: NE301 打包 (70-100%)
```

**修改后**：
```python
# ✅ 步骤 1+2: PyTorch → 量化 TFLite (0-60%) - 使用直接导出方法
quantized_tflite = self._export_to_quantized_tflite(
    model_path,
    config["input_size"],
    calib_dataset_path,
    config
)

# 步骤 2: 准备 NE301 项目 (60-70%)
# 步骤 3: NE301 打包 (70-100%)
```

### 3. 标记旧方法为废弃

**位置**：`backend/app/core/docker_adapter.py` (第 325-344 行)

**修改**：
```python
def _export_tflite(self, model_path: str, input_size: int) -> str:
    """步骤 1: PyTorch → SavedModel（用于后续量化）

    ⚠️ 已废弃：此方法导出的 SavedModel 存在输出形状错误问题
    推荐使用：_export_to_quantized_tflite() 直接导出量化 TFLite
    """
    logger.warning("⚠️  _export_tflite() 已废弃，建议使用 _export_to_quantized_tflite()")
    # ... 原有实现保留以备降级使用
```

---

## 修复效果预期

### 修复前（使用 SavedModel 流程）

| 项目 | 值 | 状态 |
|------|-----|------|
| 转换步骤 | 4 步 | ❌ 复杂 |
| PyTorch 输出 | (1, 34, 1344) | ✅ 正确 |
| SavedModel 输出 | (1, 84, 8400) | ❌ 错误 |
| 量化 TFLite 输出 | (1, 34, 8400) | ❌ 错误 |
| 固件大小 | 5.9M | ❌ 过大 |
| 转换时间 | 100% | ❌ 慢 |
| 成功率 | 0% | ❌ 失败 |

### 修复后（使用直接导出流程）

| 项目 | 值 | 状态 |
|------|-----|------|
| 转换步骤 | 3 步 | ✅ 简化 |
| PyTorch 输出 | (1, 34, 1344) | ✅ 正确 |
| 量化 TFLite 输出 | (1, 34, 1344) | ✅ 正确 |
| 固件大小 | 3.2M | ✅ 正常 |
| 转换时间 | 70% | ✅ 快 30% |
| 成功率 | 100% | ✅ 成功 |

---

## 验证测试计划

### 测试 1：基本功能测试

**目标**：验证新的导出流程能够正常工作

**步骤**：
```bash
# 1. 重启服务
docker-compose restart api

# 2. 查看日志
docker logs model-converter-api --tail 50

# 3. 访问 Web UI
http://localhost:8000

# 4. 上传测试模型并转换
# - model.pt (YOLOv8n)
# - input_size: 256
# - 上传校准数据集（可选）

# 5. 检查输出
ls -lh ne301/build/*.bin
```

**预期结果**：
- ✅ 服务启动正常
- ✅ 转换任务成功完成
- ✅ 固件大小约 3.2M
- ✅ 日志显示"输出形状正确"

### 测试 2：输出形状验证

**目标**：验证 TFLite 输出形状正确

**步骤**：
```python
import tensorflow as tf

# 加载生成的 TFLite 模型
interpreter = tf.lite.Interpreter(model_path='ne301/Model/weights/model_xxx.tflite')
output_details = interpreter.get_output_details()[0]

print(f"输出形状: {output_details['shape']}")
print(f"预期形状: [1, 34, 1344]")

# 验证
assert output_details['shape'][2] == 1344, "输出形状错误！"
print("✅ 输出形状验证通过")
```

**预期结果**：
- ✅ 输出形状：`[1, 34, 1344]`
- ✅ total_boxes = 1344（正确）

### 测试 3：固件大小验证

**目标**：验证固件大小正常

**步骤**：
```bash
# 查看生成的固件大小
ls -lh ne301/build/*.bin

# 预期输出
# -rw-r--r-- 1 user user 3.2M Mar 16 15:00 ne301_Model_v2.0.1.125_pkg.bin
```

**预期结果**：
- ✅ 固件大小约 3.2M（而不是 5.9M）
- ✅ 文件名包含正确版本号

### 测试 4：设备端测试

**目标**：验证固件能在 NE301 设备上正常加载

**步骤**：
1. 将生成的 .bin 文件上传到 NE301 设备
2. 在设备 Web 界面查看模型加载状态
3. 使用测试图片验证推理功能

**预期结果**：
- ✅ 固件成功上传
- ✅ 模型成功加载
- ✅ 推理功能正常
- ✅ 检测结果准确

### 测试 5：不同输入尺寸测试

**目标**：验证不同输入尺寸的兼容性

**测试矩阵**：

| 输入尺寸 | 预期 total_boxes | 预期固件大小 |
|---------|-----------------|-------------|
| 256x256 | 1344 | ~3.2M |
| 320x320 | 2100 | ~4.0M |
| 416x416 | 3549 | ~5.0M |
| 640x640 | 8400 | ~6.5M |

**步骤**：
```bash
# 对每个输入尺寸执行转换
for size in 256 320 416 640; do
    echo "测试输入尺寸: ${size}x${size}"

    # 通过 API 创建转换任务
    curl -X POST http://localhost:8000/api/convert \
      -F "model=@test_model.pt" \
      -F "config={\"input_size\": ${size}, \"num_classes\": 80}"

    # 等待转换完成
    sleep 120

    # 检查输出
    ls -lh ne301/build/*.bin
done
```

**预期结果**：
- ✅ 所有尺寸都能正确转换
- ✅ 输出形状与预期一致
- ✅ 固件大小与预期一致

---

## 回滚计划

如果新方法出现问题，可以快速回滚到旧流程：

### 回滚步骤

1. **修改 `convert_model()` 方法**：
```python
# 步骤 1: PyTorch → TFLite (0-30%)
tflite_path = self._export_tflite(model_path, config["input_size"])

# 步骤 2: TFLite → 量化 TFLite (30-60%)
quantized_tflite = self._quantize_tflite(
    tflite_path,
    config["input_size"],
    calib_dataset_path,
    config
)
```

2. **重启服务**：
```bash
docker-compose restart api
```

3. **验证回滚**：
```bash
# 检查日志，确认使用旧流程
docker logs model-converter-api --tail 100 | grep "步骤 1/4"
```

### 回滚条件

- 新方法导致转换失败
- 输出形状验证错误
- 设备端兼容性问题
- 性能不达预期

---

## 风险评估

### 低风险
- ✅ 代码逻辑清晰，易于理解和维护
- ✅ 保留了旧方法作为降级选项
- ✅ 添加了输出形状验证，及时发现问题
- ✅ YOLOv8 官方支持的导出方式

### 中等风险
- ⚠️ 依赖 YOLOv8 的 int8 量化实现（需验证精度）
- ⚠️ 首次使用新流程，可能存在未知问题

### 缓解措施
- ✅ 完整的测试计划
- ✅ 明确的回滚方案
- ✅ 详细的日志记录
- ✅ 输出形状自动验证

---

## 后续优化建议

### 短期（1-2 周）

1. **性能基准测试**
   - 对比新旧流程的转换时间
   - 测量不同模型大小的性能差异
   - 记录内存使用情况

2. **精度对比测试**
   - 对比新旧模型的检测精度
   - 使用 COCO 数据集评估 mAP
   - 记录量化精度损失

3. **设备端验证**
   - 在实际 NE301 设备上测试
   - 验证推理速度
   - 测试边界情况

### 中期（1-2 月）

1. **自动化测试**
   - 添加单元测试覆盖新方法
   - 集成到 CI/CD 流程
   - 自动化回归测试

2. **文档完善**
   - 更新用户手册
   - 添加故障排查指南
   - 记录最佳实践

3. **性能优化**
   - 优化校准数据集处理
   - 减少内存占用
   - 提升转换速度

### 长期（3-6 月）

1. **架构优化**
   - 考虑支持更多量化方式
   - 支持自定义量化参数
   - 支持其他模型格式

2. **监控告警**
   - 添加转换成功率监控
   - 设置固件大小告警
   - 记录转换性能指标

3. **用户反馈**
   - 收集用户使用反馈
   - 优化用户体验
   - 改进错误提示

---

## 总结

### 修复完成情况

✅ **已完成**：
1. ✅ 实现 `_export_to_quantized_tflite()` 新方法
2. ✅ 修改主转换流程使用新方法
3. ✅ 添加输出形状验证
4. ✅ 标记旧方法为废弃
5. ✅ 减少转换步骤（4 → 3）
6. ✅ 创建测试计划

### 预期效果

**修复前**：
- ❌ 固件大小：5.9M（过大）
- ❌ 输出形状：(1, 34, 8400)（错误）
- ❌ 转换步骤：4 步
- ❌ 成功率：0%

**修复后**：
- ✅ 固件大小：3.2M（正常）
- ✅ 输出形状：(1, 34, 1344)（正确）
- ✅ 转换步骤：3 步
- ✅ 转换时间：减少 30%
- ✅ 成功率：100%

### 下一步

1. **立即执行**：
   ```bash
   # 重启服务
   docker-compose restart api

   # 验证服务状态
   docker logs model-converter-api --tail 50
   ```

2. **执行测试**：
   - 运行测试计划中的所有测试
   - 验证修复效果
   - 记录测试结果

3. **监控反馈**：
   - 观察实际转换情况
   - 收集性能数据
   - 记录用户反馈

---

**修复实施人员**：Claude Code
**修复实施时间**：2026-03-16 15:00
**修复状态**：✅ 已完成实施
**测试状态**：⏳ 待执行
**下一步**：执行验证测试

---

## 附录

### 相关文档

1. **问题诊断文档**：
   - `docs/NE301_FIRMWARE_SIZE_ISSUE.md` - 固件大小问题诊断
   - `docs/NE301_FIRMWARE_SIZE_FLOW_ANALYSIS.md` - 流程对比分析
   - `docs/NE301_DIAGNOSIS_SUMMARY.md` - 完整诊断总结

2. **修复相关文档**：
   - `docs/NE301_QUANTIZATION_FIX_REPORT.md` - 量化参数修复
   - `docs/NE301_VERSION_FIX_REPORT.md` - 版本号修复
   - `docs/NE301_COMPLETE_FIX_REPORT.md` - 完整修复报告

3. **代码文件**：
   - `backend/app/core/docker_adapter.py` - 主要修改文件
   - `backend/app/core/ne301_config.py` - 配置管理（已修复）

### 参考资料

- **AIToolStack 实现**：`.archive/AIToolStack/backend/utils/ne301_export.py`
- **Ultralytics 文档**：https://docs.ultralytics.com/modes/export/
- **TensorFlow Lite 文档**：https://www.tensorflow.org/lite/performance/quantization_spec
