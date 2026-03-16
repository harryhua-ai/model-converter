# NE301 模型真实转换功能实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标:** 实现真实的 PyTorch 模型转换为 NE301 .bin 部署包的完整流程

**架构:** 混合方式 - 步骤 1-2 在宿主机执行（通用 ML 工具链），步骤 3 在 Docker 容器执行（NE301 专用工具）

**技术栈:** Ultralytics, TensorFlow, Docker, ST Edge AI

---

## 📋 转换流程概览

```
用户上传 .pt 模型
    ↓
步骤 1: PyTorch → TFLite (宿主机)
    使用 Ultralytics YOLO.export()
    ↓
步骤 2: TFLite → 量化 TFLite (宿主机)
    使用 ST tflite_quant.py + 校准数据集
    ↓
步骤 3: 量化 TFLite → NE301 .bin (Docker)
    使用 model_packager.py + JSON 配置
    ↓
返回下载链接
```

---

## 📦 文件结构

### 新增文件
- `backend/tools/quantization/tflite_quant.py` - ST 量化脚本（已迁移到 quantization/ 子目录）
- `backend/tools/quantization/user_config_quant.yaml` - 量化配置模板（已迁移到 quantization/ 子目录）
- `backend/app/core/converter.py` - 转换核心逻辑
- `backend/app/api/convert.py` - 修改为真实转换
- `backend/requirements.txt` - 添加依赖

### 修改文件
- `backend/app/core/docker_adapter.py` - 简化为只执行步骤 3

---

## Chunk 1: 环境准备

### Task 1: 添加 Python 依赖

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: 读取当前依赖**

```bash
cat backend/requirements.txt
```

- [ ] **Step 2: 添加必要的依赖**

在 `backend/requirements.txt` 末尾添加：

```txt
# NE301 模型转换依赖
ultralytics>=8.0.0
tensorflow>=2.13.0
hydra-core>=1.3.0
opencv-python>=4.8.0
```

- [ ] **Step 3: 安装依赖验证**

```bash
cd backend
pip install -r requirements.txt
python -c "import ultralytics; import tensorflow; print('✅ 依赖安装成功')"
```

Expected: `✅ 依赖安装成功`

- [ ] **Step 4: 提交**

```bash
git add backend/requirements.txt
git commit -m "feat: 添加 NE301 转换所需的 Python 依赖"
```

---

### Task 2: 下载 ST 量化脚本

**Files:**
- Create: `backend/tools/quantization/tflite_quant.py`
- Create: `backend/tools/quantization/user_config_quant.yaml`

- [ ] **Step 1: 创建 tools 目录**

```bash
mkdir -p backend/tools/quantization
```

- [ ] **Step 2: 下载量化脚本**

```bash
cd backend/tools/quantization
curl -o tflite_quant.py https://raw.githubusercontent.com/STMicroelectronics/stm32ai-modelzoo-services/main/tutorials/scripts/yolov8_quantization/tflite_quant.py
```

- [ ] **Step 3: 验证脚本下载**

```bash
head -20 tflite_quant.py
```

Expected: 看到脚本头部，包含版权信息和导入语句

- [ ] **Step 4: 创建配置文件**

创建 `backend/tools/quantization/user_config_quant.yaml`：

```yaml
# Model configuration
model:
    name: yolov8n_custom
    uc: od_coco
    model_path: ./saved_model  # 运行时替换
    input_shape: [480, 480, 3]  # 运行时替换

# Quantization settings
quantization:
    fake: False
    quantization_type: per_channel
    quantization_input_type: uint8
    quantization_output_type: int8
    calib_dataset_path: ./calibration_dataset  # 运行时替换
    export_path: ./quantized_models

# Preprocessing parameters
pre_processing:
    rescaling: {scale: 255, offset: 0}
```

- [ ] **Step 5: 提交**

```bash
git add backend/tools/
git commit -m "feat: 添加 ST 量化脚本和配置文件"
```

---

## Chunk 2: 核心转换逻辑

### Task 3: 实现转换核心类

**Files:**
- Create: `backend/app/core/converter.py`

- [ ] **Step 1: 编写测试**

创建 `backend/tests/test_converter.py`：

```python
import pytest
from app.core.converter import ModelConverter
from pathlib import Path

@pytest.fixture
def converter():
    return ModelConverter()

@pytest.fixture
def sample_config():
    return {
        "model_type": "YOLOv8",
        "input_size": 480,
        "num_classes": 80,
        "confidence_threshold": 0.25,
        "quantization": "int8"
    }

def test_converter_initialization(converter):
    assert converter is not None
    assert converter.temp_dir.exists()

@pytest.mark.integration
def test_pytorch_to_tflite_conversion(converter, sample_config, tmp_path):
    """测试 PyTorch 到 TFLite 的转换"""
    # 这个测试需要真实的模型文件，标记为 integration
    pass

@pytest.mark.integration
def test_full_conversion_pipeline(converter, sample_config, tmp_path):
    """测试完整转换流程"""
    # 标记为 integration，需要真实环境和 Docker
    pass
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend
pytest tests/test_converter.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.core.converter'`

- [ ] **Step 3: 实现 ModelConverter 类**

创建 `backend/app/core/converter.py`：

```python
"""
NE301 模型转换核心逻辑

混合方式：
- 步骤 1-2: 宿主机执行（通用 ML 工具链）
- 步骤 3: Docker 容器执行（NE301 专用工具）
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from ultralytics import YOLO
import tensorflow as tf

logger = logging.getLogger(__name__)


class ModelConverter:
    """模型转换器 - PyTorch → NE301 .bin"""

    def __init__(self, work_dir: Optional[Path] = None):
        """
        初始化转换器

        Args:
            work_dir: 工作目录，默认为 temp/converter/
        """
        self.work_dir = work_dir or Path("temp/converter")
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # 工具脚本路径
        self.tools_dir = Path(__file__).parent.parent.parent / "tools"
        self.quant_script = self.tools_dir / "tflite_quant.py"
        self.quant_config_template = self.tools_dir / "user_config_quant.yaml"

    def convert(
        self,
        model_path: str,
        config: Dict[str, Any],
        calib_dataset_path: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> str:
        """
        完整转换流程：PyTorch → TFLite → 量化 → NE301 .bin

        Args:
            model_path: PyTorch 模型路径 (.pt/.pth)
            config: 转换配置
            calib_dataset_path: 校准数据集路径（可选）
            progress_callback: 进度回调函数

        Returns:
            NE301 .bin 文件路径
        """
        task_id = config.get("task_id", "unknown")

        # 步骤 1: PyTorch → TFLite (0-30%)
        if progress_callback:
            progress_callback(10, "正在导出 TFLite 模型...")

        saved_model_dir, tflite_path = self._pytorch_to_tflite(
            model_path,
            config["input_size"]
        )

        # 步骤 2: TFLite → 量化 TFLite (30-70%)
        if progress_callback:
            progress_callback(30, "正在量化模型...")

        quantized_tflite = self._quantize_tflite(
            saved_model_dir,
            config["input_size"],
            calib_dataset_path
        )

        # 步骤 3: 量化 TFLite → NE301 .bin (70-100%)
        if progress_callback:
            progress_callback(70, "正在生成 NE301 部署包...")

        from app.core.docker_adapter import DockerToolChainAdapter

        docker = DockerToolChainAdapter()
        bin_path = docker.convert_model(
            task_id=task_id,
            model_path=str(quantized_tflite),
            config=config
        )

        if progress_callback:
            progress_callback(100, "转换完成!")

        return bin_path

    def _pytorch_to_tflite(
        self,
        model_path: str,
        input_size: int
    ) -> tuple[Path, Path]:
        """
        步骤 1: PyTorch → TFLite

        Returns:
            (saved_model_dir, tflite_path)
        """
        logger.info(f"步骤 1: 导出 {model_path} 为 TFLite 格式")

        # 使用 Ultralytics 导出
        model = YOLO(model_path)

        # 导出目录
        export_dir = self.work_dir / "tflite_export"
        export_dir.mkdir(exist_ok=True)

        # 执行导出
        model.export(
            format="tflite",
            imgsz=input_size,
            int8=False  # 先不量化，后面用 ST 脚本量化
        )

        # Ultralytics 会生成与模型同名的 .tflite 文件
        tflite_path = Path(model_path).stem + ".tflite"

        if not Path(tflite_path).exists():
            raise FileNotFoundError(f"TFLite 导出失败: {tflite_path}")

        # TFLite 模型本身就是 SavedModel 格式的一部分
        return (export_dir, Path(tflite_path))

    def _quantize_tflite(
        self,
        tflite_path: Path,
        input_size: int,
        calib_dataset_path: Optional[str] = None
    ) -> Path:
        """
        步骤 2: TFLite → 量化 TFLite

        使用 ST Microelectronics 的量化脚本
        """
        logger.info(f"步骤 2: 量化 {tflite_path}")

        # 准备配置文件
        config_path = self._prepare_quant_config(
            input_size,
            calib_dataset_path
        )

        # 执行量化脚本
        cmd = [
            "python",
            str(self.quant_script),
            "--config-name", "user_config_quant",
            "--config-dir", str(self.tools_dir)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 分钟超时
        )

        if result.returncode != 0:
            logger.error(f"量化失败: {result.stderr}")
            raise RuntimeError(f"TFLite 量化失败: {result.stderr}")

        # 查找生成的量化模型
        quantized_dir = self.work_dir / "quantized_models"
        quantized_models = list(quantized_dir.glob("*.tflite"))

        if not quantized_models:
            raise FileNotFoundError("量化后的模型文件未找到")

        return quantized_models[0]

    def _prepare_quant_config(
        self,
        input_size: int,
        calib_dataset_path: Optional[str]
    ) -> Path:
        """
        准备量化配置文件
        """
        import yaml

        # 读取模板
        with open(self.quant_config_template) as f:
            config = yaml.safe_load(f)

        # 更新配置
        config["model"]["input_shape"] = [input_size, input_size, 3]

        if calib_dataset_path:
            config["quantization"]["calib_dataset_path"] = calib_dataset_path
        else:
            # 使用默认的少量图片
            config["quantization"]["calib_dataset_path"] = str(
                self.work_dir / "default_calib"
            )

        # 保存到工作目录
        config_path = self.work_dir / "user_config_quant.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        return config_path
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend
pytest tests/test_converter.py::test_converter_initialization -v
```

Expected: `PASSED`

- [ ] **Step 5: 提交**

```bash
git add backend/app/core/converter.py backend/tests/test_converter.py
git commit -m "feat: 实现模型转换核心逻辑"
```

---

## Chunk 3: Docker 适配器简化

### Task 4: 简化 DockerToolChainAdapter

**Files:**
- Modify: `backend/app/core/docker_adapter.py:50-150`

- [ ] **Step 1: 编写测试**

在 `backend/tests/test_docker_adapter.py` 添加：

```python
def test_convert_model_with_tflite(adapter, tmp_path):
    """测试使用 TFLite 模型转换为 NE301 .bin"""
    # 创建模拟的量化 TFLite 文件
    tflite_path = tmp_path / "quantized_model.tflite"
    tflite_path.write_bytes(b"fake_tflite_data")

    config = {
        "model_type": "YOLOv8",
        "input_size": 480,
        "num_classes": 80
    }

    # 这个测试需要真实的 Docker 环境，标记为 integration
    # 实际测试在集成测试中进行
```

- [ ] **Step 2: 修改 convert_model 方法**

修改 `backend/app/core/docker_adapter.py` 中的 `convert_model` 方法：

```python
def convert_model(
    self,
    task_id: str,
    model_path: str,  # 现在接收 TFLite 文件路径
    config: Dict[str, Any],
    yaml_path: Optional[str] = None
) -> str:
    """
    使用 Docker 容器将量化 TFLite 模型转换为 NE301 .bin

    Args:
        task_id: 任务 ID
        model_path: 量化后的 TFLite 模型路径
        config: 转换配置
        yaml_path: YAML 类别定义文件（可选）

    Returns:
        NE301 .bin 文件路径
    """
    logger.info(f"步骤 3: 使用 Docker 转换 {model_path} 为 NE301 .bin")

    # 准备输出路径
    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_filename = f"ne301_model_{task_id}.bin"
    output_path = output_dir / output_filename

    # 准备 NE301 JSON 配置
    ne301_config = self._prepare_ne301_config(task_id, config, yaml_path)
    config_path = self.work_dir / f"{task_id}_config.json"
    with open(config_path, "w") as f:
        json.dump(ne301_config, f, indent=2)

    # 准备卷映射
    model_dir = Path(model_path).parent
    volumes = {
        str(model_dir): {"bind": "/input", "mode": "ro"},
        str(output_dir): {"bind": "/output", "mode": "rw"},
        str(config_path.parent): {"bind": "/config", "mode": "ro"}
    }

    # 构建命令
    model_filename = Path(model_path).name
    command = [
        "python",
        "/workspace/ne301/Script/model_packager.py",
        "create",
        "--model", f"/input/{model_filename}",
        "--config", json.dumps(ne301_config),
        "--output", f"/output/{output_filename}"
    ]

    # 运行容器
    logger.info(f"启动 Docker 容器执行转换...")
    result = self.client.containers.run(
        self.image_name,
        command=command,
        volumes=volumes,
        remove=True,
        detach=False,
        mem_limit="2g",
        cpu_count=1
    )

    logger.info(f"Docker 容器输出: {result.decode('utf-8')}")

    # 验证输出文件
    if not output_path.exists():
        raise FileNotFoundError(f"NE301 .bin 文件未生成: {output_path}")

    logger.info(f"✅ 转换成功: {output_path}")
    return str(output_path)

def _prepare_ne301_config(
    self,
    task_id: str,
    config: Dict[str, Any],
    yaml_path: Optional[str]
) -> Dict[str, Any]:
    """
    准备 NE301 JSON 配置
    """
    ne301_config = {
        "model_name": f"ne301_model_{task_id}",
        "input_size": config["input_size"],
        "num_classes": config["num_classes"],
        "confidence_threshold": config.get("confidence_threshold", 0.25),
        "model_type": config["model_type"],
        "quantization": config.get("quantization", "int8")
    }

    # 如果有 YAML 文件，添加类别信息
    if yaml_path and Path(yaml_path).exists():
        import yaml
        with open(yaml_path) as f:
            yaml_data = yaml.safe_load(f)
            # 尝试读取类别名称
            for key in ["names", "classes", "labels", "categories"]:
                if key in yaml_data:
                    ne301_config["class_names"] = yaml_data[key]
                    break

    return ne301_config
```

- [ ] **Step 3: 运行测试**

```bash
cd backend
pytest tests/test_docker_adapter.py -v -k "test_check_image"
```

Expected: 至少镜像检查测试通过

- [ ] **Step 4: 提交**

```bash
git add backend/app/core/docker_adapter.py
git commit -m "refactor: 简化 Docker 适配器为步骤 3 专用"
```

---

## Chunk 4: API 集成

### Task 5: 修改转换 API 端点

**Files:**
- Modify: `backend/app/api/convert.py:80-150`

- [ ] **Step 1: 编写集成测试**

创建 `backend/tests/integration/test_real_conversion.py`：

```python
import pytest
from pathlib import Path

@pytest.mark.integration
@pytest.mark.slow
def test_full_conversion_workflow(client, sample_model_file):
    """测试完整的转换流程（需要 Docker）"""
    # 准备测试文件
    model_path = Path("tests/fixtures/yolov8n.pt")

    if not model_path.exists():
        pytest.skip("需要真实的测试模型文件")

    # 上传并启动转换
    response = client.post("/api/convert", data={
        "model_file": open(model_path, "rb"),
        "config_file": ("config.json", '{"input_size": 256, "num_classes": 80}', "application/json")
    })

    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data

    # 轮询任务状态
    import time
    task_id = data["task_id"]
    for _ in range(60):  # 最多等待 5 分钟
        time.sleep(5)
        status_response = client.get(f"/api/tasks/{task_id}")
        status_data = status_response.json()

        if status_data["status"] == "completed":
            break
        elif status_data["status"] == "failed":
            pytest.fail(f"转换失败: {status_data.get('error_message')}")

    assert status_data["status"] == "completed"
```

- [ ] **Step 2: 修改后台任务函数**

修改 `backend/app/api/convert.py` 中的 `_run_conversion` 函数：

```python
async def _run_conversion(
    task_id: str,
    model_path: str,
    config: Dict[str, Any],
    yaml_path: Optional[str] = None,
    calib_dataset_path: Optional[str] = None
):
    """
    后台执行模型转换任务

    现在使用真实的转换流程
    """
    from app.core.converter import ModelConverter

    try:
        logger.info(f"开始任务 {task_id} 的真实转换流程")

        # 初始化转换器
        converter = ModelConverter()

        # 进度回调
        def progress_callback(progress: int, message: str):
            task_manager.update_progress(task_id, progress, message)
            logger.info(f"[{progress}%] {message}")

        # 执行转换
        output_path = converter.convert(
            model_path=model_path,
            config=config,
            calib_dataset_path=calib_dataset_path,
            progress_callback=progress_callback
        )

        # 标记任务完成
        task_manager.complete_task(task_id, output_path)
        logger.info(f"✅ 任务 {task_id} 转换成功")

    except Exception as e:
        logger.error(f"❌ 任务 {task_id} 转换失败: {str(e)}")
        task_manager.fail_task(task_id, str(e))
        raise
```

- [ ] **Step 3: 运行测试（如果环境允许）**

```bash
cd backend
# 先运行快速测试
pytest tests/ -v -k "not integration and not slow"

# 如果有 Docker 和模型文件，运行集成测试
pytest tests/integration/test_real_conversion.py -v
```

Expected: 单元测试通过，集成测试根据环境

- [ ] **Step 4: 提交**

```bash
git add backend/app/api/convert.py backend/tests/integration/test_real_conversion.py
git commit -m "feat: 集成真实模型转换流程"
```

---

## Chunk 5: 文档和收尾

### Task 6: 更新用户文档

**Files:**
- Create: `backend/docs/MODEL_CONVERSION.md`

- [ ] **Step 1: 创建转换流程文档**

创建 `backend/docs/MODEL_CONVERSION.md`：

```markdown
# NE301 模型转换流程

## 概述

本系统将 PyTorch/YOLOv8 模型转换为 NE301 设备可用的 .bin 部署包。

## 转换步骤

### 步骤 1: PyTorch → TFLite
- 使用 Ultralytics YOLO 库
- 输入：`.pt` / `.pth` 文件
- 输出：TensorFlow Lite 模型
- 参数：输入尺寸（256/480/640）

### 步骤 2: TFLite → 量化 TFLite
- 使用 STMicroelectronics 量化脚本
- 输入：TFLite 模型 + 校准数据集（可选）
- 输出：INT8 量化的 TFLite 模型
- 参数：量化类型（int8/float）

### 步骤 3: 量化 TFLite → NE301 .bin
- 使用 Docker 容器（camthink/ne301-dev）
- 输入：量化 TFLite 模型 + JSON 配置
- 输出：NE301 .bin 部署包
- 工具：model_packager.py

## 使用方式

### Web 界面

1. 访问 http://localhost:8000
2. 上传 PyTorch 模型文件（.pt/.pth）
3. （可选）上传类别定义 YAML 文件
4. （可选）上传校准数据集 ZIP 文件
5. 选择转换预设（快速/平衡/高精度）
6. 点击"开始转换"
7. 等待转换完成并下载 .bin 文件

### API 调用

```bash
curl -X POST "http://localhost:8000/api/convert" \
  -F "model_file=@yolov8n.pt" \
  -F "config_file=@config.json" \
  -F "yaml_file=@classes.yaml" \
  -F "calibration_dataset=@calib.zip"
```

## 性能指标

- 转换时间：3-5 分钟（YOLOv8n @ 480x480）
- 内存使用：< 4GB
- Docker 镜像大小：~3GB（首次下载）

## 故障排查

### Docker 未启动
```
错误: Docker 未运行
解决: 启动 Docker Desktop
```

### 镜像拉取失败
```
错误: failed to resolve reference
解决: 检查网络连接，手动拉取: docker pull camthink/ne301-dev:latest
```

### 量化失败
```
错误: TFLite 量化失败
解决: 检查校准数据集格式（必须是包含 .jpg/.png 的 ZIP 文件）
```
```

- [ ] **Step 2: 更新 README**

在项目根目录 `README.md` 添加：

```markdown
## 快速开始

### 1. 安装依赖

\`\`\`bash
# 安装 Python 依赖
pip install -r backend/requirements.txt

# 确保Docker已启动
docker --version
\`\`\`

### 2. 启动服务

\`\`\`bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
\`\`\`

### 3. 访问 Web 界面

打开浏览器访问 http://localhost:8000

## 模型转换

支持将 YOLOv8 PyTorch 模型转换为 NE301 .bin 格式。详细文档请参阅 [MODEL_CONVERSION.md](backend/docs/MODEL_CONVERSION.md)。
```

- [ ] **Step 3: 提交**

```bash
git add backend/docs/MODEL_CONVERSION.md README.md
git commit -m "docs: 添加模型转换流程文档"
```

---

## 验收标准

### 功能验收
- [ ] 上传 YOLOv8n.pt 模型 → 成功生成 .bin 文件
- [ ] 支持校准数据集上传 → 提高量化精度
- [ ] 支持类别 YAML 文件 → 自动识别类别数量
- [ ] 实时进度显示（0-100%）→ 用户体验良好
- [ ] 转换日志实时输出 → 便于调试

### 性能验收
- [ ] YOLOv8n 480x480 转换时间 < 5 分钟
- [ ] 内存使用 < 4GB
- [ ] 支持并发 1 个任务（避免资源冲突）

### 错误处理验收
- [ ] Docker 未启动 → 显示友好提示
- [ ] 模型格式错误 → 提示支持的格式
- [ ] 校准数据集无效 → 显示具体错误
- [ ] 转换失败 → 显示详细日志

---

**下一步:** 执行此计划前，请确保：
1. Docker Desktop 已安装并运行
2. 已拉取 camthink/ne301-dev:latest 镜像（可选，首次自动拉取）
3. 有测试用的 YOLOv8 模型文件
