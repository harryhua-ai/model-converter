# 配置参数参考

## 概述

本文档提供 NE301 Model Converter 所有配置参数的详细说明，包括 API 参数、环境变量和配置文件。

## API 参数

### 转换请求参数

**端点**: `POST /api/convert`

**Content-Type**: `multipart/form-data`

| 参数 | 类型 | 必填 | 说明 | 默认值 | 示例 |
|------|------|------|------|--------|------|
| model | file | ✅ | PyTorch 模型文件 | - | `model.pt` |
| config | JSON | ✅ | 转换配置 | - | `{"input_size": 640}` |
| yaml_file | file | ❌ | 类别配置文件 | - | `classes.yaml` |
| calibration_dataset | file | ❌ | 校准数据集 ZIP | - | `calibration.zip` |

### config 参数详解

```json
{
  "model_type": "yolov8",
  "input_size": 640,
  "num_classes": 80,
  "confidence_threshold": 0.25,
  "nms_threshold": 0.45,
  "quantization": "int8",
  "task_id": "task-123"
}
```

| 字段 | 类型 | 必填 | 说明 | 取值范围 | 默认值 |
|------|------|------|------|---------|--------|
| model_type | str | ❌ | 模型类型 | `"yolov8"`, `"yolov5"` | `"yolov8"` |
| input_size | int | ❌ | 输入尺寸 | 256, 480, 640 | 640 |
| num_classes | int | ❌ | 类别数量 | ≥ 1 | 80 |
| confidence_threshold | float | ❌ | 置信度阈值 | 0.0-1.0 | 0.25 |
| nms_threshold | float | ❌ | NMS 阈值 | 0.0-1.0 | 0.45 |
| quantization | str | ❌ | 量化类型 | `"int8"`, `"float32"` | `"int8"` |
| task_id | str | ❌ | 任务 ID | UUID 格式 | 自动生成 |

### yaml_file 格式

`classes.yaml` 示例:

```yaml
names:
  0: person
  1: bicycle
  2: car
  3: motorcycle
  4: airplane
  # ... 更多类别
```

**注意**: 如果不提供 `yaml_file`，系统将使用 COCO 默认类别（80 类）。

## 环境变量

### Docker 配置

| 变量名 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `NE301_DOCKER_IMAGE` | str | NE301 Docker 镜像名称 | `camthink/ne301-dev:latest` |
| `NE301_PROJECT_PATH` | str | NE301 项目路径（容器内） | `/app/ne301` |
| `CONTAINER_NAME` | str | 容器名称 | `model-converter-api` |

### 服务器配置

| 变量名 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `HOST` | str | 服务器监听地址 | `0.0.0.0` |
| `PORT` | int | 服务器监听端口 | `8000` |
| `DEBUG` | bool | 调试模式 | `False` |
| `ENVIRONMENT` | str | 运行环境 | `development` |

### 日志配置

| 变量名 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `LOG_LEVEL` | str | 日志级别 | `INFO` |

**日志级别**:
- `DEBUG`: 详细调试信息
- `INFO`: 常规信息
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

### 文件路径配置

| 变量名 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `UPLOAD_DIR` | str | 上传目录 | `./uploads` |
| `TEMP_DIR` | str | 临时目录 | `./temp` |
| `OUTPUT_DIR` | str | 输出目录 | `./outputs` |
| `MAX_UPLOAD_SIZE` | int | 最大上传大小（字节） | `524288000` (500MB) |

### 示例配置文件

`backend/.env`:

```env
# Docker 配置
NE301_DOCKER_IMAGE=camthink/ne301-dev:latest
NE301_PROJECT_PATH=/app/ne301
CONTAINER_NAME=model-converter-api

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=False
ENVIRONMENT=production

# 日志配置
LOG_LEVEL=INFO

# 文件路径配置
UPLOAD_DIR=./uploads
TEMP_DIR=./temp
OUTPUT_DIR=./outputs
MAX_UPLOAD_SIZE=524288000
```

## 配置文件

### ST 量化配置文件

`backend/tools/quantization/user_config_quant.yaml`:

```yaml
# 模型配置
model:
  model_path: "/path/to/saved_model"    # SavedModel 路径
  input_shape: [640, 640, 3]            # 输入形状 [H, W, C]

# 量化配置
quantization:
  calib_dataset_path: "/path/to/images"  # 校准数据集路径
  export_path: "/app/outputs"            # 输出路径
  max_calib_images: 200                  # 最大校准图片数量
  fake: false                            # 是否使用 fake quantization
```

**字段说明**:

| 字段 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| model.model_path | str | SavedModel 目录路径 | - |
| model.input_shape | list | 输入形状 [H, W, C] | [640, 640, 3] |
| quantization.calib_dataset_path | str | 校准数据集路径 | "" |
| quantization.export_path | str | 输出路径 | "/app/outputs" |
| quantization.max_calib_images | int | 最大校准图片数 | 200 |
| quantization.fake | bool | 是否 fake quantization | false |

### NE301 JSON 配置

`ne301/models/model_name/model.json`:

```json
{
  "name": "yolov8n",
  "version": "1.0.0",
  "input_shape": [1, 640, 640, 3],
  "output_shape": [1, 34, 1344],
  "num_classes": 80,
  "confidence_threshold": 0.25,
  "nms_threshold": 0.45,
  "anchors": [
    [10, 13, 16, 30, 33, 23],
    [30, 61, 62, 45, 59, 119],
    [116, 90, 156, 198, 373, 326]
  ],
  "created_at": "2026-03-16T12:00:00Z"
}
```

**字段说明**:

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| name | str | 模型名称 | ✅ |
| version | str | 版本号 | ✅ |
| input_shape | list | 输入形状 [N, H, W, C] | ✅ |
| output_shape | list | 输出形状 | ✅ |
| num_classes | int | 类别数量 | ✅ |
| confidence_threshold | float | 置信度阈值 | ❌ |
| nms_threshold | float | NMS 阈值 | ❌ |
| anchors | list | Anchor 尺寸 | ❌ |
| created_at | str | 创建时间（ISO 8601） | ❌ |

### Makefile 配置

`ne301/Makefile`:

```makefile
# 模型配置
MODEL_NAME = yolov8n
MODEL_INPUT_SIZE = 640
MODEL_NUM_CLASSES = 80
MODEL_OUTPUT_SHAPE = 1344

# 编译选项
CC = gcc
CFLAGS = -O3 -Wall

# 输出路径
BUILD_DIR = build
OUTPUT_DIR = outputs
```

## 性能参数

### 并发配置

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `MAX_CONCURRENT_TASKS` | int | 最大并发任务数 | 5 |
| `TASK_TIMEOUT` | int | 任务超时时间（秒） | 600 |

### 缓存配置

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `ENABLE_CACHE` | bool | 是否启用缓存 | `True` |
| `CACHE_DIR` | str | 缓存目录 | `./cache` |
| `CACHE_MAX_SIZE` | int | 缓存最大大小（字节） | `10737418240` (10GB) |

### Docker 资源限制

```yaml
# docker-compose.yml
services:
  model-converter-api:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G
```

## 高级配置

### WebSocket 配置

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `WS_HEARTBEAT_INTERVAL` | int | 心跳间隔（秒） | 30 |
| `WS_MAX_CONNECTIONS` | int | 最大连接数 | 100 |

### 任务队列配置

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `QUEUE_MAX_SIZE` | int | 队列最大长度 | 1000 |
| `QUEUE_TIMEOUT` | int | 队列超时（秒） | 300 |

### 监控配置

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `ENABLE_MONITORING` | bool | 是否启用监控 | `True` |
| `METRICS_PORT` | int | 监控端口 | 9090 |
| `METRICS_PATH` | str | 监控路径 | `/metrics` |

## 配置验证

### 验证环境变量

```bash
# 检查必要的环境变量
env | grep NE301
env | grep PORT
env | grep LOG_LEVEL
```

### 验证配置文件

```python
import yaml
from pathlib import Path

def validate_config(config_path: str) -> bool:
    """验证配置文件"""
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # 检查必要字段
        required_fields = ['model', 'quantization']
        for field in required_fields:
            if field not in config:
                print(f"❌ 缺少字段: {field}")
                return False

        # 检查模型配置
        if 'model_path' not in config['model']:
            print("❌ 缺少 model.model_path")
            return False

        if 'input_shape' not in config['model']:
            print("❌ 缺少 model.input_shape")
            return False

        print("✅ 配置文件验证通过")
        return True

    except Exception as e:
        print(f"❌ 配置文件验证失败: {e}")
        return False
```

## 配置最佳实践

### 开发环境

```env
DEBUG=True
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

### 生产环境

```env
DEBUG=False
LOG_LEVEL=INFO
ENVIRONMENT=production
ENABLE_MONITORING=True
```

### 高性能配置

```env
MAX_CONCURRENT_TASKS=10
CACHE_MAX_SIZE=21474836480  # 20GB
ENABLE_CACHE=True
```

### 低资源配置

```env
MAX_CONCURRENT_TASKS=2
CACHE_MAX_SIZE=5368709120   # 5GB
MAX_UPLOAD_SIZE=262144000   # 250MB
```

## 故障排查

### 配置加载失败

**症状**:
```
ERROR: Failed to load configuration
```

**原因**:
- 配置文件格式错误
- 环境变量未设置
- 文件路径不存在

**解决**:
1. 验证 YAML 语法
2. 检查环境变量
3. 确认文件路径

### 参数验证失败

**症状**:
```
ERROR: Invalid parameter: input_size
```

**原因**:
- 参数值不在有效范围内
- 参数类型不匹配

**解决**:
1. 检查参数取值范围
2. 确认参数类型正确

## 参考

- [Pydantic Settings 文档](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Docker Compose 配置](https://docs.docker.com/compose/compose-file/)
- [Hydra 配置框架](https://hydra.cc/docs/intro/)