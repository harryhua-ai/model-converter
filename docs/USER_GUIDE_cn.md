# NE301 Model Converter - 用户指南

NE301 Model Converter 完整使用指南。

---

## 目录

1. [概述](#概述)
2. [快速开始](#快速开始)
3. [模型转换](#模型转换)
4. [配置选项](#配置选项)
5. [高级功能](#高级功能)
6. [故障排查](#故障排查)
7. [常见问题](#常见问题)

---

## 概述

NE301 Model Converter 是一个零代码的端到端模型转换平台，可自动将 PyTorch 模型转换为 NE301 边缘设备格式（.bin）。

### 核心特性

- **零代码操作**: 基于 Web 的界面，无需编程
- **端到端自动化**: PyTorch → 量化 → NE301 .bin 全自动
- **实时反馈**: 基于 WebSocket 的进度更新
- **跨平台支持**: macOS / Linux / Windows
- **智能 OOM 修复**: 自动诊断和修复 NE301 OOM 问题

### 支持的模型

| 模型类型 | 格式 | 输入尺寸 |
|---------|------|---------|
| YOLOv5 | .pt, .pth | 256, 480, 640 |
| YOLOv8 | .pt, .pth | 256, 480, 640 |
| 自定义 PyTorch | .pt, .pth | 自定义 |

---

## 快速开始

### 系统要求

- **Docker Desktop**: 必须安装并运行
- **内存**: 最低 4GB，推荐 8GB
- **磁盘空间**: 10GB 用于 Docker 镜像
- **浏览器**: Chrome, Firefox, Safari, Edge（最新版本）

### 启动服务

```bash
# 1. 拉取依赖镜像
docker pull camthink/ne301-dev:latest

# 2. 启动服务
docker-compose up -d

# 3. 访问 Web 界面
# 打开 http://localhost:8000
```

### 停止服务

```bash
docker-compose down
```

---

## 模型转换

### 分步指南

#### 1. 上传模型文件

点击 **"选择模型文件"** 并选择你的 PyTorch 模型：
- 支持格式：`.pt`, `.pth`
- 最大文件大小：500MB

#### 2. （可选）上传类别定义

上传定义类别名称的 YAML 文件：

```yaml
names:
  - person
  - bicycle
  - car
  - motorcycle
  # 添加更多类别
```

此文件用于：
- 设置正确的类别数量
- 在检测结果中显示类别名称

#### 3. （可选）上传校准数据集

上传包含校准图片的 ZIP 文件：
- **最少**：32 张图片
- **推荐**：50-100 张图片
- **格式**：.jpg, .png
- **目的**：提高量化精度

#### 4. 选择转换预设

| 预设 | 输入尺寸 | 速度 | 精度 | 使用场景 |
|------|---------|------|------|---------|
| 快速 | 256x256 | 最快 | 良好 | 实时应用 |
| 平衡 | 480x480 | 快速 | 较好 | 通用场景（推荐） |
| 高精度 | 640x640 | 较慢 | 最好 | 高精度要求 |

#### 5. 开始转换

点击 **"开始转换"** 并监控进度：
- 实时进度条
- 详细转换日志
- 基于 WebSocket 的更新

#### 6. 下载结果

完成后：
- 点击 **"下载 .bin 文件"**
- 文件已准备好用于 NE301 部署

---

## 配置选项

### 环境变量

创建 `backend/.env` 自定义设置：

```env
# Docker 配置
NE301_DOCKER_IMAGE=camthink/ne301-dev:latest
NE301_PROJECT_PATH=/app/ne301

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=False

# 日志
LOG_LEVEL=INFO

# 文件存储
UPLOAD_DIR=./uploads
TEMP_DIR=./temp
OUTPUT_DIR=./outputs
MAX_UPLOAD_SIZE=524288000  # 500MB
```

### 转换参数

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `input_size` | 模型输入分辨率 | 480 |
| `num_classes` | 检测类别数量 | 自动检测 |
| `quantization` | 量化类型 | int8 |

---

## 高级功能

### 校准数据集

**目的**：通过提供代表性样本提高量化精度。

**要求**：
- 包含图片的 ZIP 文件
- 最少 32 张图片（推荐：50-100 张）
- 图片应代表真实使用场景
- 支持格式：.jpg, .png

**创建校准数据集**：

```bash
# 创建包含样本图片的目录
mkdir calibration_images

# 添加 32-100 张代表性图片
cp /path/to/your/images/*.jpg calibration_images/

# 创建 ZIP 文件
zip -r calibration.zip calibration_images/
```

**最佳实践**：
- 使用与生产数据相似的图片
- 包含各种光照条件
- 覆盖不同物体大小和角度
- 避免重复或非常相似的图片

### 自定义类别定义

**YAML 格式**：

```yaml
# classes.yaml
names:
  - person
  - bicycle
  - car
  - motorcycle
  - airplane
  - bus
  - train
  - truck
  - boat
  - traffic light
```

**自动检测**：
- 如果未提供，系统会尝试从模型自动检测
- 对于 YOLO 模型，默认使用 COCO 类别（80 个）

### 批量转换

对于多个模型，使用 REST API：

```bash
# 顺序转换多个模型
for model in model1.pt model2.pt model3.pt; do
  curl -X POST "http://localhost:8000/api/convert" \
    -F "model_file=@$model" \
    -F 'config={"model_type": "yolov8", "input_size": 480}'
done
```

---

## 故障排查

### 常见问题

#### Docker 未运行

**症状**：
- 错误："Cannot connect to Docker daemon"
- 服务无法启动

**解决方法**：
1. 启动 Docker Desktop
2. 等待 Docker 完全初始化
3. 验证：`docker ps`

#### 镜像拉取失败

**症状**：
- 错误："failed to resolve reference"
- 拉取镜像超时

**解决方法**：
```bash
# 检查网络连接
ping google.com

# 手动拉取镜像
docker pull camthink/ne301-dev:latest

# 如果仍然失败，配置 Docker 镜像加速器
```

#### 端口被占用

**症状**：
- 错误："port is already allocated"
- 服务启动失败

**解决方法**：
```bash
# 查找占用端口 8000 的进程
lsof -i :8000

# 停止冲突的服务
kill -9 <PID>

# 或停止现有容器
docker-compose down
docker-compose up -d
```

#### 转换失败

**症状**：
- 进度在某个步骤停止
- 日志中显示错误信息

**解决方法**：

1. **检查模型格式**：
   - 必须是有效的 PyTorch 模型（.pt/.pth）
   - 推荐使用 YOLOv5/v8 模型

2. **检查校准数据集**：
   - 必须是 ZIP 文件
   - 必须包含 .jpg/.png 图片
   - 最少 32 张图片

3. **检查日志**：
   ```bash
   docker-compose logs -f
   ```

4. **检查内存**：
   - 确保有 4GB+ 可用内存
   - 关闭其他内存密集型应用程序

#### NE301 设备 OOM（内存不足）

**症状**：
- 模型加载到设备时报错
- "[DRIVER] model_init: OOM"

**解决方法**（v2.1+）：
- 此问题在转换时会**自动修复**
- 系统会检测并修正 mpool 配置
- 无需用户操作

---

## 常见问题

### 一般问题

**Q: 支持哪些模型？**

A: 目前支持：
- YOLOv5（所有变体）
- YOLOv8（所有变体）
- 自定义 PyTorch 模型（实验性）

**Q: 转换需要多长时间？**

A: 典型转换时间：
- 小型模型（YOLOv8n）：2-3 分钟
- 中型模型（YOLOv8s/m）：3-5 分钟
- 大型模型（YOLOv8l/x）：5-10 分钟

**Q: 校准数据集是必需的吗？**

A: 不是，它是可选的。没有它，系统会使用 fake 量化，精度可能会略有降低。

**Q: 各预设之间有什么区别？**

A:
- **快速**：最小模型，推理最快，精度略低
- **平衡**：速度和精度的良好平衡（推荐）
- **高精度**：最大模型，精度最好，推理较慢

### 技术问题

**Q: 支持哪个 Python 版本？**

A: Python 3.11 或 3.12。由于 TensorFlow 兼容性，不支持 Python 3.14。

**Q: 可以离线转换模型吗？**

A: 初始设置（拉取 Docker 镜像）后，转换可以离线进行。

**Q: 转换后的文件存储在哪里？**

A: 文件存储在 Docker 卷中：
- `uploads/`: 上传的模型
- `outputs/`: 转换后的 .bin 文件
- `temp/`: 临时文件

**Q: 如何访问转换后的文件？**

A:
1. 通过 Web 界面下载（推荐）
2. 或从容器复制：
   ```bash
   docker cp model-converter-api:/app/outputs/ ./
   ```

### 部署问题

**Q: 可以在服务器上部署吗？**

A: 可以。基于 Docker 的部署适用于任何安装了 Docker 的服务器。

**Q: 如何更新到新版本？**

A:
```bash
git pull
docker-compose build --no-cache
docker-compose up -d
```

**Q: 支持身份验证吗？**

A: 当前版本不支持。对于生产部署，可通过反向代理（如 Nginx）添加身份验证。

---

## 相关文档

- [快速开始指南](QUICK_START_cn.md) - 5 分钟上手
- [Docker 部署指南](../README.docker_cn.md) - 详细 Docker 说明
- [Docker Compose 指南](DOCKER_COMPOSE_GUIDE.md) - 配置选项
- [开发文档](../CLAUDE.md) - 技术文档

---

## 获取帮助

- **文档**: 查看本指南和相关文档
- **日志**: `docker-compose logs -f` 查看详细日志
- **问题反馈**: 在 GitHub Issues 上提交
- **社区**: 在 GitHub 上参与讨论

---

**最后更新**: 2026-03-18
**文档版本**: 1.0.0
