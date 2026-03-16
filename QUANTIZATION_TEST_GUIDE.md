# 量化流程测试 - 快速指南

## 快速开始

### 1. 运行所有测试
```bash
./run_quantization_tests.sh
```

### 2. 只运行单元测试
```bash
./run_quantization_tests.sh unit
```

### 3. 只运行集成测试
```bash
./run_quantization_tests.sh integration
```

### 4. 生成覆盖率报告
```bash
./run_quantization_tests.sh coverage
```

### 5. 运行特定测试
```bash
./run_quantization_tests.sh specific TestExportToSavedModel::test_export_to_saved_model_success
```

## 测试状态

### 当前状态: ⏳ 等待实现

测试文件已创建,但需要先实现以下方法才能通过测试:

- ❌ `_export_to_saved_model()` - 导出 SavedModel
- ❌ `_run_st_quantization()` - 运行 ST 量化
- ❌ `_validate_quantized_model()` - 验证量化模型
- ❌ `_prepare_quant_config()` - 准备量化配置
- ✅ `_extract_calibration_dataset()` - 解压校准数据集 (已实现)

### 测试统计

- **总测试数**: 35
- **单元测试**: 31
- **集成测试**: 2
- **当前通过**: 5 (测试已存在的方法)
- **待实现**: 30 (需要新方法)

## 测试覆盖的场景

### 1. 基本功能
- ✅ SavedModel 导出
- ✅ ST 官方量化脚本调用
- ✅ 量化模型验证
- ✅ 完整转换流程

### 2. 不同场景
- ✅ 无校准数据集 (fake 量化)
- ✅ 有校准数据集 (真实量化)
- ✅ 不同输入尺寸 (256/320/416/512/640)

### 3. 错误处理
- ✅ 文件不存在
- ✅ 量化失败
- ✅ 输出形状错误
- ✅ 损坏的校准数据集
- ✅ 无效的输入尺寸

### 4. 边界情况
- ✅ 空校准数据集
- ✅ 并发量化任务
- ✅ 大输入尺寸 (1280)
- ✅ 大量校准图片 (300+)

## 实现优先级

### 高优先级 (核心功能)
1. `_export_to_saved_model()` - 导出 SavedModel
2. `_run_st_quantization()` - 运行 ST 量化
3. `_validate_quantized_model()` - 验证量化模型
4. `_prepare_quant_config()` - 准备量化配置

### 中优先级 (改进)
5. 修改 `convert_model()` 使用新流程
6. 优化校准数据集处理
7. 添加性能监控

### 低优先级 (优化)
8. 并发任务优化
9. 内存使用优化
10. 错误消息改进

## 预期结果

实现所有方法后:

```bash
$ ./run_quantization_tests.sh

=========================================
  NE301 量化流程测试
=========================================

运行所有测试...

========================================= test session starts ==========================================
platform darwin -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/harryhua/Documents/GitHub/model-converter/backend
configfile: pytest.ini
collected 35 items

tests/test_quantization_flow.py::TestExportToSavedModel::test_export_to_saved_model_success PASSED [  2%]
tests/test_quantization_flow.py::TestExportToSavedModel::test_export_to_saved_model_different_sizes PASSED [  5%]
tests/test_quantization_flow.py::TestExportToSavedModel::test_export_to_saved_model_model_not_found PASSED [  8%]
tests/test_quantization_flow.py::TestExportToSavedModel::test_export_to_saved_model_ultralytics_error PASSED [ 11%]
tests/test_quantization_flow.py::TestRunSTQuantization::test_quantization_fake_mode PASSED [ 14%]
tests/test_quantization_flow.py::TestRunSTQuantization::test_quantization_with_calibration PASSED [ 17%]
tests/test_quantization_flow.py::TestRunSTQuantization::test_quantization_different_input_sizes PASSED [ 20%]
tests/test_quantization_flow.py::TestRunSTQuantization::test_quantization_script_failure PASSED [ 22%]
tests/test_quantization_flow.py::TestRunSTQuantization::test_quantization_output_file_not_created PASSED [ 25%]
tests/test_quantization_flow.py::TestValidateQuantizedModel::test_validate_model_success PASSED [ 28%]
tests/test_quantization_flow.py::TestValidateQuantizedModel::test_validate_model_output_shape_correct PASSED [ 31%]
tests/test_quantization_flow.py::TestValidateQuantized_model::test_validate_model_output_shape_incorrect PASSED [ 34%]
tests/test_quantization_flow.py::TestValidateQuantizedModel::test_validate_model_different_sizes PASSED [ 37%]
tests/test_quantization_flow.py::TestValidateQuantizedModel::test_validate_model_file_not_found PASSED [ 40%]
tests/test_quantization_flow.py::TestValidateQuantizedModel::test_validate_model_invalid_tflite PASSED [ 42%]
tests/test_quantization_flow.py::TestConvertModelWithQuantization::test_convert_model_with_new_quantization_flow PASSED [ 45%]
tests/test_quantization_flow.py::TestConvertModelWithQuantization::test_convert_model_with_calibration_dataset PASSED [ 48%]
tests/test_quantization_flow.py::TestConvertModelWithQuantization::test_convert_model_export_failure PASSED [ 51%]
tests/test_quantization_flow.py::TestConvertModelWithQuantization::test_convert_model_quantization_failure PASSED [ 54%]
tests/test_quantization_flow.py::TestConvertModelWithQuantization::test_convert_model_validation_failure PASSED [ 57%]
tests/test_quantization_flow.py::TestConvertModelWithQuantization::test_convert_model_progress_callback PASSED [ 60%]
tests/test_quantization_flow.py::TestHelperMethods::test_prepare_quant_config PASSED [ 62%]
tests/test_quantization_flow.py::TestHelperMethods::test_prepare_quant_config_fake_mode PASSED [ 65%]
tests/test_quantization_flow.py::TestHelperMethods::test_extract_calibration_dataset PASSED [ 68%]
tests/test_quantization_flow.py::TestHelperMethods::test_extract_calibration_dataset_not_zip PASSED [ 71%]
tests/test_quantization_flow.py::TestHelperMethods::test_extract_calibration_dataset_error PASSED [ 74%]
tests/test_quantization_flow.py::TestQuantizationIntegration::test_full_quantization_flow_fake_mode PASSED [ 77%]
tests/test_quantization_flow.py::TestQuantizationIntegration::test_full_quantization_flow_with_calibration PASSED [ 80%]
tests/test_quantization_flow.py::TestEdgeCases::test_empty_calibration_dataset PASSED [ 82%]
tests/test_quantization_flow.py::TestEdgeCases::test_invalid_input_size PASSED [ 85%]
tests/test_quantization_flow.py::TestEdgeCases::test_concurrent_quantization_tasks PASSED [ 88%]
tests/test_quantization_flow.py::TestEdgeCases::test_large_input_size PASSED [ 91%]
tests/test_quantization_flow.py::TestEdgeCases::test_corrupted_calibration_zip PASSED [ 94%]
tests/test_quantization_flow.py::TestPerformance::test_quantization_with_large_calibration_dataset PASSED [ 97%]
tests/test_quantization_flow.py::TestPerformance::test_memory_cleanup_during_quantization PASSED [100%]

========================================= 35 passed in 15.42s ==========================================

=========================================
  测试完成
=========================================
```

## 覆盖率目标

实现后预期达到:

- **语句覆盖率**: 85%+
- **分支覆盖率**: 80%+
- **函数覆盖率**: 90%+

## 下一步

1. **实现新方法** - 参考测试文件中的实现步骤
2. **运行测试** - 使用 `./run_quantization_tests.sh`
3. **修复失败** - 根据测试输出调整实现
4. **生成覆盖率** - 使用 `./run_quantization_tests.sh coverage`
5. **提交代码** - 确保所有测试通过

## 相关文件

- 📝 测试文件: `backend/tests/test_quantization_flow.py`
- 🔧 实现文件: `backend/app/core/docker_adapter.py`
- 📋 总结文档: `backend/tests/QUANTIZATION_TEST_SUMMARY.md`
- 🚀 测试脚本: `run_quantization_tests.sh`

---

**最后更新**: 2025-03-16
**状态**: ⏳ 等待实现
**版本**: 1.0.0
