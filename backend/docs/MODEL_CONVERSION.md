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

## 环境要求

### Python 环境
- Python 3.11 或 3.12（推荐）
- Python 3.14 存在兼容性问题（TensorFlow 不支持）

### 必需依赖
```bash
pip install ultralytics tensorflow hydra-core opencv-python
```

### Docker 环境
- Docker Desktop 已安装并运行
- 镜像：camthink/ne301-dev:latest（自动拉取）

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

### ML 库导入错误
```
错误: No module named 'ultralytics' 或 'tensorflow'
解决:
1. 使用 Python 3.11/3.12 环境
2. 安装依赖: pip install ultralytics tensorflow
```

## 技术架构

### 混合部署方式
- **宿主机**: 步骤 1-2（PyTorch → TFLite → 量化）
- **Docker 容器**: 步骤 3（量化 → NE301 .bin）

### 为什么采用混合方式？
1. **性能**: 宿主机执行步骤 1-2 更快
2. **隔离**: NE301 工具链在容器中隔离
3. **灵活性**: 支持不同 Python 版本

## 进阶配置

### 自定义校准数据集
上传包含 32-100 张图片的 ZIP 文件，可提高量化精度。

### 类别定义文件
支持 YAML 格式，自动识别类别数量：
```yaml
names:
  - person
  - car
  - dog
  # ...
```

### 转换预设
- **快速模式**: 256x256，速度优先
- **平衡模式**: 480x480，推荐
- **高精度模式**: 640x640，精度优先
