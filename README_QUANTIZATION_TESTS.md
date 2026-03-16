# 🧪 NE301 量化流程测试 - 快速开始

## 🎯 概述

完整的测试套件,用于测试 NE301 模型转换的量化流程。

**测试数量**: 35 个
**当前状态**: 5/35 通过 (14.3%)
**目标状态**: 35/35 通过 (100%)

---

## 📁 文件结构

```
model-converter/
├── backend/tests/
│   ├── test_quantization_flow.py          # 主测试文件
│   └── QUANTIZATION_TEST_SUMMARY.md       # 测试总结
├── run_quantization_tests.sh              # 测试执行脚本
├── QUANTIZATION_TEST_GUIDE.md             # 快速指南
├── QUANTIZATION_TEST_CHECKLIST.md         # 实现清单
├── QUANTIZATION_TEST_DELIVERY.md          # 交付文档
└── README_QUANTIZATION_TESTS.md           # 本文件
```

---

## 🚀 5 分钟快速开始

### 1. 运行所有测试
```bash
./run_quantization_tests.sh
```

### 2. 查看当前状态
```bash
cd backend
pytest tests/test_quantization_flow.py --collect-only
```

### 3. 查看已通过的测试
```bash
pytest tests/test_quantization_flow.py -v 2>&1 | grep PASSED
```

---

## 📊 测试概览

### 测试类分布

| 测试类 | 测试数 | 状态 | 说明 |
|--------|--------|------|------|
| TestExportToSavedModel | 4 | ⏳ | SavedModel 导出 |
| TestRunSTQuantization | 5 | ⏳ | ST 量化脚本 |
| TestValidateQuantizedModel | 6 | ⏳ | 模型验证 |
| TestConvertModelWithQuantization | 6 | ⏳ | 完整流程 |
| TestHelperMethods | 5 | ✅ 3/5 | 辅助方法 |
| TestQuantizationIntegration | 2 | ⏳ | 集成测试 |
| TestEdgeCases | 5 | ✅ 5/5 | 边界情况 |
| TestPerformance | 2 | ⏳ | 性能测试 |

### 已通过的测试 (5 个)

这些测试已通过,因为它们测试的是已存在的方法:

1. ✅ `test_extract_calibration_dataset` - 校准数据集解压
2. ✅ `test_extract_calibration_dataset_not_zip` - 非 ZIP 格式处理
3. ✅ `test_extract_calibration_dataset_error` - 解压错误处理
4. ✅ `test_empty_calibration_dataset` - 空数据集处理
5. ✅ `test_corrupted_calibration_zip` - 损坏 ZIP 处理

### 待实现的测试 (30 个)

这些测试需要实现新方法后才能通过:

#### 需要实现的方法:
1. `_export_to_saved_model()` - 导出 SavedModel (4 个测试)
2. `_run_st_quantization()` - 运行 ST 量化 (5 个测试)
3. `_validate_quantized_model()` - 验证量化模型 (6 个测试)
4. `_prepare_quant_config()` - 准备量化配置 (2 个测试)
5. 修改 `convert_model()` - 使用新流程 (6 个测试)
6. 集成测试 - 需要完整实现 (2 个测试)
7. 边界测试 - 需要完整实现 (3 个测试)
8. 性能测试 - 需要完整实现 (2 个测试)

---

## 🔧 实现指南

### 步骤 1: 实现核心方法

在 `backend/app/core/docker_adapter.py` 中添加:

```python
def _export_to_saved_model(self, model_path: str, input_size: int) -> str:
    """导出 PyTorch 模型到 SavedModel 格式"""
    from ultralytics import YOLO
    model = YOLO(model_path)
    return model.export(format="saved_model", imgsz=input_size)

def _prepare_quant_config(self, saved_model_path: str, input_size: int, calib_dataset_path: Optional[str]) -> Path:
    """准备 ST 量化脚本配置文件"""
    # 实现配置生成逻辑

def _run_st_quantization(self, saved_model_path: str, input_size: int, calib_dataset_path: Optional[str], output_dir: str) -> str:
    """运行 ST 官方量化脚本"""
    # 实现量化脚本调用

def _validate_quantized_model(self, tflite_path: str, input_size: int) -> bool:
    """验证量化后的模型"""
    # 实现模型验证逻辑
```

### 步骤 2: 修改转换流程

```python
def convert_model(self, task_id, model_path, config, calib_dataset_path=None, yaml_path=None, progress_callback=None):
    # ... 前面的代码 ...

    # ✅ 新流程: SavedModel + ST 量化
    saved_model = self._export_to_saved_model(model_path, config["input_size"])
    quantized_tflite = self._run_st_quantization(
        saved_model, config["input_size"], calib_dataset_path, output_dir
    )
    self._validate_quantized_model(quantized_tflite, config["input_size"])

    # ... 后续代码 ...
```

### 步骤 3: 运行测试

```bash
# 运行所有测试
./run_quantization_tests.sh all

# 运行单元测试
./run_quantization_tests.sh unit

# 生成覆盖率报告
./run_quantization_tests.sh coverage
```

---

## 📚 详细文档

| 文档 | 说明 |
|------|------|
| [QUANTIZATION_TEST_SUMMARY.md](./backend/tests/QUANTIZATION_TEST_SUMMARY.md) | 测试总结和实现步骤 |
| [QUANTIZATION_TEST_GUIDE.md](./QUANTIZATION_TEST_GUIDE.md) | 快速指南和预期结果 |
| [QUANTIZATION_TEST_CHECKLIST.md](./QUANTIZATION_TEST_CHECKLIST.md) | 详细实现清单 |
| [QUANTIZATION_TEST_DELIVERY.md](./QUANTIZATION_TEST_DELIVERY.md) | 交付文档和支持 |

---

## 🎓 测试覆盖

### 测试场景

- ✅ **基本功能**: SavedModel 导出、ST 量化、模型验证
- ✅ **量化模式**: Fake 量化、真实量化
- ✅ **输入尺寸**: 256, 320, 416, 512, 640
- ✅ **错误处理**: 文件不存在、量化失败、输出错误
- ✅ **边界情况**: 空数据集、并发任务、大尺寸
- ✅ **性能场景**: 大量校准图片、内存清理

### 预期覆盖率

| 指标 | 目标 |
|------|------|
| 语句覆盖率 | ≥85% |
| 分支覆盖率 | ≥80% |
| 函数覆盖率 | ≥90% |

---

## ⚠️ 常见问题

### Q: 为什么大部分测试失败?
A: 因为测试的方法尚未实现。这是正常的!实现方法后测试就会通过。

### Q: 如何开始实现?
A: 按照 `QUANTIZATION_TEST_CHECKLIST.md` 中的步骤,依次实现 4 个核心方法。

### Q: 如何运行单个测试?
A: 使用 `./run_quantization_tests.sh specific <test_name>`

### Q: 如何查看详细的错误信息?
A: 运行 `pytest tests/test_quantization_flow.py -v --tb=long`

---

## 📞 获取帮助

1. **查看文档**: 阅读 4 个详细文档
2. **运行示例**: 使用 `run_quantization_tests.sh` 脚本
3. **检查清单**: 参考 `QUANTIZATION_TEST_CHECKLIST.md`
4. **查看代码**: 阅读 `test_quantization_flow.py` 中的测试代码

---

## ✅ 下一步行动

1. ✅ 阅读 `QUANTIZATION_TEST_GUIDE.md`
2. ✅ 查看 `QUANTIZATION_TEST_CHECKLIST.md`
3. ⏳ 实现 4 个核心方法
4. ⏳ 运行测试验证
5. ⏳ 生成覆盖率报告

---

**创建时间**: 2025-03-16
**版本**: 1.0.0
**状态**: ✅ 准备就绪
