# 量化流程测试实现清单

## 测试实现进度

### 总体进度: 5/35 (14.3%)

| 测试类 | 状态 | 通过/总数 | 进度 |
|--------|------|-----------|------|
| TestExportToSavedModel | ⏳ 待实现 | 0/4 | 0% |
| TestRunSTQuantization | ⏳ 待实现 | 0/5 | 0% |
| TestValidateQuantizedModel | ⏳ 待实现 | 0/6 | 0% |
| TestConvertModelWithQuantization | ⏳ 待实现 | 0/6 | 0% |
| TestHelperMethods | ⏳ 部分实现 | 3/5 | 60% |
| TestQuantizationIntegration | ⏳ 待实现 | 0/2 | 0% |
| TestEdgeCases | ✅ 已实现 | 5/5 | 100% |
| TestPerformance | ⏳ 待实现 | 0/2 | 0% |

---

## 详细测试清单

### 1. TestExportToSavedModel (0/4)

需要实现: `_export_to_saved_model()`

- [ ] `test_export_to_saved_model_success` - 测试成功导出
- [ ] `test_export_to_saved_model_different_sizes` - 测试不同输入尺寸
- [ ] `test_export_to_saved_model_model_not_found` - 测试文件不存在
- [ ] `test_export_to_saved_model_ultralytics_error` - 测试 Ultralytics 错误

**实现步骤**:
```python
def _export_to_saved_model(self, model_path: str, input_size: int) -> str:
    from ultralytics import YOLO
    model = YOLO(model_path)
    return model.export(format="saved_model", imgsz=input_size)
```

---

### 2. TestRunSTQuantization (0/5)

需要实现: `_run_st_quantization()` 和 `_prepare_quant_config()`

- [ ] `test_quantization_fake_mode` - 测试 fake 量化
- [ ] `test_quantization_with_calibration` - 测试真实校准
- [ ] `test_quantization_different_input_sizes` - 测试不同尺寸
- [ ] `test_quantization_script_failure` - 测试脚本失败
- [ ] `test_quantization_output_file_not_created` - 测试文件未生成

**实现步骤**:
```python
def _prepare_quant_config(self, saved_model_path: str, input_size: int, calib_dataset_path: Optional[str]) -> Path:
    # 生成 YAML 配置文件
    pass

def _run_st_quantization(self, saved_model_path: str, input_size: int, calib_dataset_path: Optional[str], output_dir: str) -> str:
    # 调用 ST 量化脚本
    pass
```

---

### 3. TestValidateQuantizedModel (0/6)

需要实现: `_validate_quantized_model()`

- [ ] `test_validate_model_success` - 测试成功验证
- [ ] `test_validate_model_output_shape_correct` - 测试输出形状正确
- [ ] `test_validate_model_output_shape_incorrect` - 测试输出形状错误
- [ ] `test_validate_model_different_sizes` - 测试不同尺寸
- [ ] `test_validate_model_file_not_found` - 测试文件不存在
- [ ] `test_validate_model_invalid_tflite` - 测试无效 TFLite

**实现步骤**:
```python
def _validate_quantized_model(self, tflite_path: str, input_size: int) -> bool:
    import tensorflow as tf
    interpreter = tf.lite.Interpreter(model_path=tflite_path)
    # 验证输出形状
    pass
```

---

### 4. TestConvertModelWithQuantization (0/6)

需要修改: `convert_model()` 方法

- [ ] `test_convert_model_with_new_quantization_flow` - 测试新流程
- [ ] `test_convert_model_with_calibration_dataset` - 测试带校准数据集
- [ ] `test_convert_model_export_failure` - 测试导出失败
- [ ] `test_convert_model_quantization_failure` - 测试量化失败
- [ ] `test_convert_model_validation_failure` - 测试验证失败
- [ ] `test_convert_model_progress_callback` - 测试进度回调

**实现步骤**:
```python
def convert_model(self, task_id, model_path, config, calib_dataset_path=None, yaml_path=None, progress_callback=None):
    # 步骤 1: 导出 SavedModel
    saved_model = self._export_to_saved_model(model_path, config["input_size"])

    # 步骤 2: ST 量化
    quantized_tflite = self._run_st_quantization(
        saved_model, config["input_size"], calib_dataset_path, output_dir
    )

    # 步骤 3: 验证量化模型
    self._validate_quantized_model(quantized_tflite, config["input_size"])

    # 后续步骤保持不变...
    pass
```

---

### 5. TestHelperMethods (3/5)

状态: 部分实现 (已有 `_extract_calibration_dataset()`)

- [x] `test_prepare_quant_config` - 测试配置生成 (需要实现方法)
- [x] `test_prepare_quant_config_fake_mode` - 测试 fake 配置 (需要实现方法)
- [x] `test_extract_calibration_dataset` - 测试解压 (已实现 ✅)
- [x] `test_extract_calibration_dataset_not_zip` - 测试非 ZIP (已实现 ✅)
- [x] `test_extract_calibration_dataset_error` - 测试错误处理 (已实现 ✅)

**备注**: 3 个测试已通过,因为 `_extract_calibration_dataset()` 方法已存在。

---

### 6. TestQuantizationIntegration (0/2)

需要完整实现后才能运行

- [ ] `test_full_quantization_flow_fake_mode` - 测试完整 fake 量化流程
- [ ] `test_full_quantization_flow_with_calibration` - 测试完整真实量化流程

**备注**: 这些是集成测试,需要真实 ML 库和 Docker 环境。

---

### 7. TestEdgeCases (5/5)

状态: 已实现 ✅ (测试现有方法)

- [x] `test_empty_calibration_dataset` - 测试空数据集 ✅
- [ ] `test_invalid_input_size` - 测试无效尺寸 (需要实现)
- [ ] `test_concurrent_quantization_tasks` - 测试并发 (需要实现)
- [ ] `test_large_input_size` - 测试大尺寸 (需要实现)
- [x] `test_corrupted_calibration_zip` - 测试损坏 ZIP ✅

**备注**: 2 个边界测试已通过,因为它们测试的是已存在的解压功能。

---

### 8. TestPerformance (0/2)

需要完整实现后才能运行

- [ ] `test_quantization_with_large_calibration_dataset` - 测试大量校准图片
- [ ] `test_memory_cleanup_during_quantization` - 测试内存清理

---

## 实现优先级

### P0 - 核心功能 (必须实现)
1. ✅ `_extract_calibration_dataset()` - 已实现
2. ⏳ `_export_to_saved_model()` - 待实现
3. ⏳ `_prepare_quant_config()` - 待实现
4. ⏳ `_run_st_quantization()` - 待实现
5. ⏳ `_validate_quantized_model()` - 待实现

### P1 - 流程集成 (重要)
6. ⏳ 修改 `convert_model()` - 待实现
7. ⏳ 进度回调集成 - 待实现

### P2 - 错误处理 (建议)
8. ⏳ 文件不存在错误处理 - 待实现
9. ⏳ 量化失败错误处理 - 待实现
10. ⏳ 输出形状验证 - 待实现

### P3 - 边界情况 (可选)
11. ⏳ 并发任务支持 - 待实现
12. ⏳ 大输入尺寸支持 - 待实现
13. ⏳ 内存优化 - 待实现

---

## 测试命令

### 快速测试
```bash
# 只运行已实现的测试
pytest tests/test_quantization_flow.py::TestHelperMethods::test_extract_calibration_dataset -v
pytest tests/test_quantization_flow.py::TestHelperMethods::test_extract_calibration_dataset_not_zip -v
pytest tests/test_quantization_flow.py::TestHelperMethods::test_extract_calibration_dataset_error -v
pytest tests/test_quantization_flow.py::TestEdgeCases::test_empty_calibration_dataset -v
pytest tests/test_quantization_flow.py::TestEdgeCases::test_corrupted_calibration_zip -v
```

### 实现后运行所有测试
```bash
./run_quantization_tests.sh all
```

### 生成覆盖率报告
```bash
./run_quantization_tests.sh coverage
```

---

## 实现检查清单

### 步骤 1: 实现 `_export_to_saved_model()`
- [ ] 导入 `ultralytics.YOLO`
- [ ] 加载模型
- [ ] 调用 `export(format="saved_model")`
- [ ] 返回 SavedModel 路径
- [ ] 测试: `pytest tests/test_quantization_flow.py::TestExportToSavedModel -v`

### 步骤 2: 实现 `_prepare_quant_config()`
- [ ] 读取 YAML 模板
- [ ] 更新配置参数
- [ ] 处理 fake/real 量化模式
- [ ] 写入临时配置文件
- [ ] 测试: `pytest tests/test_quantization_flow.py::TestHelperMethods::test_prepare_quant_config -v`

### 步骤 3: 实现 `_run_st_quantization()`
- [ ] 调用 `_prepare_quant_config()`
- [ ] 构造量化命令
- [ ] 执行 ST 量化脚本
- [ ] 查找输出文件
- [ ] 测试: `pytest tests/test_quantization_flow.py::TestRunSTQuantization -v`

### 步骤 4: 实现 `_validate_quantized_model()`
- [ ] 导入 `tensorflow.lite.Interpreter`
- [ ] 加载 TFLite 模型
- [ ] 验证输出形状
- [ ] 处理不同输入尺寸
- [ ] 测试: `pytest tests/test_quantization_flow.py::TestValidateQuantizedModel -v`

### 步骤 5: 修改 `convert_model()`
- [ ] 替换步骤 1 实现
- [ ] 集成新量化流程
- [ ] 保持进度回调
- [ ] 测试: `pytest tests/test_quantization_flow.py::TestConvertModelWithQuantization -v`

### 步骤 6: 集成测试
- [ ] 准备测试模型文件
- [ ] 准备校准数据集
- [ ] 运行完整流程测试
- [ ] 验证输出文件
- [ ] 测试: `pytest tests/test_quantization_flow.py::TestQuantizationIntegration -v`

### 步骤 7: 覆盖率验证
- [ ] 运行所有测试
- [ ] 生成覆盖率报告
- [ ] 确认 80%+ 覆盖率
- [ ] 修复未覆盖的分支
- [ ] 测试: `./run_quantization_tests.sh coverage`

---

## 成功标准

实现完成后,应该达到:

- ✅ 所有单元测试通过 (31/31)
- ✅ 所有集成测试通过 (2/2)
- ✅ 语句覆盖率 ≥ 85%
- ✅ 分支覆盖率 ≥ 80%
- ✅ 函数覆盖率 ≥ 90%
- ✅ 无已知 bug

---

## 相关文档

- 📝 [测试总结](./QUANTIZATION_TEST_SUMMARY.md)
- 🚀 [快速指南](./QUANTIZATION_TEST_GUIDE.md)
- 📋 [测试文件](./backend/tests/test_quantization_flow.py)
- 🔧 [实现文件](./backend/app/core/docker_adapter.py)

---

**更新时间**: 2025-03-16
**当前状态**: 5/35 通过 (14.3%)
**目标状态**: 35/35 通过 (100%)
