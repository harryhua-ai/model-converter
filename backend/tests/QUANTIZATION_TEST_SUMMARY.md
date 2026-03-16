# 量化流程测试总结

## 测试文件概述

已创建完整的量化流程测试文件: `backend/tests/test_quantization_flow.py`

### 测试覆盖范围

测试文件包含 **8 个主要测试类**,共 **35 个测试用例**:

#### 1. TestExportToSavedModel (4 个测试)
测试 `_export_to_saved_model()` 函数:
- ✅ 成功导出 SavedModel
- ✅ 不同输入尺寸 (256/320/416/512/640)
- ✅ 模型文件不存在的错误处理
- ✅ Ultralytics 导出失败的错误处理

#### 2. TestRunSTQuantization (5 个测试)
测试 `_run_st_quantization()` 函数:
- ✅ Fake 量化模式（无校准数据集）
- ✅ 真实校准数据集量化
- ✅ 不同输入尺寸的量化配置
- ✅ 量化脚本执行失败的错误处理
- ✅ 量化文件未生成的错误处理

#### 3. TestValidateQuantizedModel (6 个测试)
测试 `_validate_quantized_model()` 函数:
- ✅ 成功验证量化模型
- ✅ 输出形状验证（正确）
- ✅ 输出形状验证（错误）
- ✅ 不同输入尺寸的输出形状
- ✅ 模型文件不存在的错误处理
- ✅ 无效 TFLite 文件的错误处理

#### 4. TestConvertModelWithQuantization (6 个测试)
测试修改后的 `convert_model()` 方法:
- ✅ 使用新量化流程的完整转换
- ✅ 带校准数据集的转换
- ✅ SavedModel 导出失败
- ✅ 量化失败
- ✅ 模型验证失败
- ✅ 进度回调功能

#### 5. TestHelperMethods (5 个测试)
测试辅助方法:
- ✅ 量化配置文件生成
- ✅ Fake 量化模式配置
- ✅ 校准数据集解压
- ✅ 非 ZIP 格式的校准数据集
- ✅ 解压失败的错误处理

#### 6. TestQuantizationIntegration (2 个测试)
集成测试（需要真实 ML 库）:
- ✅ 完整的 fake 量化流程
- ✅ 带校准数据集的完整量化流程

#### 7. TestEdgeCases (5 个测试)
边界情况测试:
- ✅ 空校准数据集
- ✅ 无效的输入尺寸
- ✅ 并发量化任务
- ✅ 大输入尺寸 (1280)
- ✅ 损坏的校准数据集 ZIP

#### 8. TestPerformance (2 个测试)
性能测试:
- ✅ 大量校准图片的场景（300+ 张）
- ✅ 量化过程中的内存清理

### 测试类型分布

| 类型 | 数量 | 标记 |
|------|------|------|
| 单元测试 | 31 | `@pytest.mark.unit` |
| 集成测试 | 2 | `@pytest.mark.integration` |
| 边界测试 | 5 | 包含在单元测试中 |
| 性能测试 | 2 | 包含在单元测试中 |

## 当前状态

### ❌ 测试失败原因

所有测试当前**失败**是**正常的**,因为测试的方法尚未在 `docker_adapter.py` 中实现:

```python
# 需要实现的新方法:
DockerToolChainAdapter._export_to_saved_model()      # 不存在
DockerToolChainAdapter._run_st_quantization()        # 不存在
DockerToolChainAdapter._validate_quantized_model()   # 不存在
DockerToolChainAdapter._prepare_quant_config()       # 不存在
```

### ✅ 已通过的测试

以下测试已通过,因为它们测试的是已存在的方法:

1. `test_extract_calibration_dataset` - 校准数据集解压（已实现）
2. `test_extract_calibration_dataset_not_zip` - 非 ZIP 格式处理（已实现）
3. `test_extract_calibration_dataset_error` - 解压错误处理（已实现）
4. `test_empty_calibration_dataset` - 空数据集处理（已实现）
5. `test_corrupted_calibration_zip` - 损坏 ZIP 处理（已实现）

## 实现步骤

### 步骤 1: 实现新方法

在 `backend/app/core/docker_adapter.py` 中添加以下方法:

```python
def _export_to_saved_model(
    self,
    model_path: str,
    input_size: int
) -> str:
    """导出 PyTorch 模型到 SavedModel 格式"""
    from ultralytics import YOLO

    model = YOLO(model_path)
    saved_model_path = model.export(
        format="saved_model",
        imgsz=input_size,
        verbose=False
    )

    return str(saved_model_path)


def _prepare_quant_config(
    self,
    saved_model_path: str,
    input_size: int,
    calib_dataset_path: Optional[str]
) -> Path:
    """准备 ST 量化脚本配置文件"""
    import yaml
    from pathlib import Path

    # 读取模板
    template_path = Path(__file__).parent.parent / "tools" / "quantization" / "user_config_quant.yaml"
    with open(template_path) as f:
        config = yaml.safe_load(f)

    # 更新配置
    config["model"]["model_path"] = saved_model_path
    config["model"]["input_shape"] = [input_size, input_size, 3]

    if calib_dataset_path:
        config["quantization"]["calib_dataset_path"] = calib_dataset_path
        config["quantization"]["fake"] = False
    else:
        config["quantization"]["fake"] = True

    # 写入临时配置文件
    work_dir = Path(tempfile.gettempdir()) / "ne301_quant"
    work_dir.mkdir(exist_ok=True)
    config_path = work_dir / "user_config_quant.yaml"

    with open(config_path, 'w') as f:
        yaml.dump(config, f)

    return config_path


def _run_st_quantization(
    self,
    saved_model_path: str,
    input_size: int,
    calib_dataset_path: Optional[str],
    output_dir: str
) -> str:
    """运行 ST 官方量化脚本"""
    import subprocess

    # 准备配置文件
    config_path = self._prepare_quant_config(
        saved_model_path, input_size, calib_dataset_path
    )

    # 量化脚本路径
    quant_script = Path(__file__).parent.parent / "tools" / "quantization" / "tflite_quant.py"

    # 执行量化
    result = subprocess.run(
        ["python", str(quant_script), "--config", str(config_path)],
        capture_output=True,
        text=True,
        timeout=600
    )

    if result.returncode != 0:
        raise RuntimeError(f"量化失败: {result.stderr}")

    # 查找输出文件
    output_files = list(Path(output_dir).glob("*.tflite"))
    if not output_files:
        raise FileNotFoundError("量化文件未生成")

    return str(output_files[0])


def _validate_quantized_model(
    self,
    tflite_path: str,
    input_size: int
) -> bool:
    """验证量化后的模型"""
    import tensorflow as tf

    if not Path(tflite_path).exists():
        raise FileNotFoundError(f"模型文件不存在: {tflite_path}")

    try:
        interpreter = tf.lite.Interpreter(model_path=tflite_path)
        output_details = interpreter.get_output_details()[0]
        output_shape = output_details['shape']

        # 验证输出形状
        expected_boxes = {
            256: 1344, 320: 2100, 416: 3549,
            512: 5376, 640: 8400
        }

        expected = expected_boxes.get(input_size)
        if expected:
            actual_boxes = output_shape[2] if len(output_shape) > 2 else output_shape[1]

            if actual_boxes != expected:
                raise ValueError(
                    f"输出形状错误: {output_shape} != (1, 34, {expected})"
                )

        return True

    except Exception as e:
        raise RuntimeError(f"无效的 TFLite 模型: {e}")
```

### 步骤 2: 修改 convert_model() 方法

在 `convert_model()` 中替换步骤 1 的实现:

```python
def convert_model(self, task_id, model_path, config, calib_dataset_path=None, yaml_path=None, progress_callback=None):
    # ... 前面的代码保持不变 ...

    # ❌ 旧方法（直接导出量化 TFLite）
    # quantized_tflite = self._export_to_quantized_tflite(...)

    # ✅ 新方法（SavedModel + ST 量化）
    with self.performance_monitor.measure_step(task_id, "saved_model_export"):
        # 1. 导出 SavedModel
        saved_model_path = self._export_to_saved_model(
            model_path,
            config["input_size"]
        )

    with self.performance_monitor.measure_step(task_id, "st_quantization"):
        # 2. ST 量化
        quantized_tflite = self._run_st_quantization(
            saved_model_path=saved_model_path,
            input_size=config["input_size"],
            calib_dataset_path=calib_dataset_path,
            output_dir=str(Path(model_path).parent)
        )

    with self.performance_monitor.measure_step(task_id, "validate_quantized"):
        # 3. 验证量化模型
        self._validate_quantized_model(
            quantized_tflite,
            config["input_size"]
        )

    # ... 后续代码保持不变 ...
```

### 步骤 3: 运行测试

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行所有量化流程测试
cd backend
pytest tests/test_quantization_flow.py -v

# 只运行单元测试
pytest tests/test_quantization_flow.py -m unit -v

# 只运行集成测试
pytest tests/test_quantization_flow.py -m integration -v

# 运行特定测试类
pytest tests/test_quantization_flow.py::TestExportToSavedModel -v

# 运行特定测试
pytest tests/test_quantization_flow.py::TestExportToSavedModel::test_export_to_saved_model_success -v

# 生成覆盖率报告
pytest tests/test_quantization_flow.py --cov=app.core.docker_adapter --cov-report=html
```

## 测试场景说明

### 1. 无校准数据集（Fake 量化）
```python
# 使用随机数据进行量化
converter.convert_model(
    task_id="test-fake",
    model_path="model.pt",
    config={"input_size": 640, "num_classes": 80},
    calib_dataset_path=None  # 无校准数据
)
```

### 2. 有校准数据集（真实量化）
```python
# 使用真实图片进行量化
converter.convert_model(
    task_id="test-calib",
    model_path="model.pt",
    config={"input_size": 640, "num_classes": 80},
    calib_dataset_path="calibration.zip"  # 包含真实图片的 ZIP
)
```

### 3. 不同输入尺寸
```python
# 支持的输入尺寸
input_sizes = [256, 320, 416, 512, 640]

for size in input_sizes:
    converter.convert_model(
        task_id=f"test-{size}",
        model_path="model.pt",
        config={"input_size": size, "num_classes": 80}
    )
```

### 4. 错误处理
```python
# 测试各种错误场景
# - 文件不存在
# - 量化失败
# - 输出形状错误
# - 损坏的校准数据集
```

## 预期测试覆盖率

实现新方法后,预期测试覆盖率:

| 组件 | 预期覆盖率 |
|------|-----------|
| `_export_to_saved_model()` | 90%+ |
| `_run_st_quantization()` | 85%+ |
| `_validate_quantized_model()` | 95%+ |
| `convert_model()` (修改部分) | 80%+ |
| 辅助方法 | 85%+ |

**整体目标**: 80%+ 分支覆盖率

## 注意事项

### 1. 依赖库要求
- ✅ `ultralytics` - YOLO 模型导出
- ✅ `tensorflow` - TFLite 模型验证
- ✅ `opencv-python` - 图片处理（校准数据集）
- ✅ `hydra-core` - ST 量化脚本配置

### 2. 集成测试要求
集成测试需要:
- 真实的 PyTorch 模型文件 (.pt)
- 完整的 ML 库环境
- Docker 运行中（NE301 打包）

### 3. 性能考虑
- 校准数据集图片数量限制: 200 张（防止 OOM）
- 量化超时时间: 600 秒（10 分钟）
- 并发任务支持: 通过线程安全设计

## 下一步行动

1. ✅ **测试文件已创建** - `backend/tests/test_quantization_flow.py`
2. ⏳ **实现新方法** - 在 `docker_adapter.py` 中添加 4 个新方法
3. ⏳ **修改 convert_model()** - 替换步骤 1 的实现
4. ⏳ **运行测试** - 验证所有测试通过
5. ⏳ **生成覆盖率报告** - 确认 80%+ 覆盖率

## 相关文件

- **测试文件**: `/Users/harryhua/Documents/GitHub/model-converter/backend/tests/test_quantization_flow.py`
- **实现文件**: `/Users/harryhua/Documents/GitHub/model-converter/backend/app/core/docker_adapter.py`
- **ST 量化脚本**: `/Users/harryhua/Documents/GitHub/model-converter/backend/tools/quantization/tflite_quant.py`
- **配置模板**: `/Users/harryhua/Documents/GitHub/model-converter/backend/tools/quantization/user_config_quant.yaml`

---

**创建时间**: 2025-03-16
**版本**: 1.0.0
**状态**: 测试已创建,等待实现
