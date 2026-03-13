# NE301 模型转换工具

将 PyTorch YOLO 模型转换为 NE301 设备可用的 .bin 固件格式。

## 📦 两种使用方式

| 方式 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| **🚀 本地运行** | 开发者、快速测试 | 启动快，调试方便 | 需要配置 Python 环境 |
| **🐳 Docker** | 生产环境、最终用户 | 环境一致，依赖隔离 | 首次构建需要时间 |

---

## 🚀 方式一：本地运行（推荐开发者）

### 前置要求

- Python 3.11+
- Node.js 20+
- pnpm 9+ (或 npm)
- ST Edge AI 工具链（可选，用于完整转换流程）

### 一键启动

```bash
cd model-converter

# 启动服务（自动安装依赖）
./start.sh

# 或使用 Makefile
make start
```

**首次启动**：
- 自动检查环境依赖
- 自动创建虚拟环境并安装 Python 依赖
- 自动安装前端依赖
- 预计时间：2-3 分钟

**访问服务**：
- Web 界面: http://localhost:3000
- API 文档: http://localhost:8000/docs

**停止服务**：
```bash
./stop.sh
# 或
make stop
```

### 手动启动（高级用户）

**仅启动后端**：
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

**仅启动前端**：
```bash
cd frontend
pnpm install
pnpm dev
```

---

## 🏗️ Docker 架构说明

### ⚠️ 重要限制

**基础镜像限制**: `camthink/ne301-dev:latest` 仅支持 **AMD64 架构**

| 环境 | 架构 | 模型转换 | 其他功能 | 说明 |
|------|------|----------|----------|------|
| **Apple Silicon 开发** | AMD64 (Rosetta 2) | ❌ **不可用** | ✅ 可用 | PyTorch 量化会遇到 SIGILL 错误 |
| **AMD64 用户** | AMD64 原生 | ✅ 完全可用 | ✅ 完全可用 | 所有功能正常 |

**详细说明**: 请查看 [ARCHITECTURE_LIMITATIONS.md](ARCHITECTURE_LIMITATIONS.md)

### Apple Silicon 开发者

**可以做什么**：
- ✅ 前端开发和 UI 调试
- ✅ API 接口开发和测试
- ✅ 文件上传下载功能
- ✅ 任务状态管理

**不能做什么**：
- ❌ 完整的模型转换（需要在 AMD64 环境测试）

**推荐开发方式**：
```bash
# 仅启动后端 API（用于开发）
docker-compose up -d backend redis

# 本地运行前端
cd frontend && pnpm dev
```

### AMD64 用户（生产环境）

**所有功能完全可用**：

```bash
cd model-converter
docker-compose up -d
```

访问服务：
- Web 界面: http://localhost:3000
- API 文档: http://localhost:8000/docs

### 架构验证

启动服务后，验证容器架构：

```bash
# 查看容器架构
docker ps --format "table {{.Names}}\t{{.Architecture}}"
```

**预期输出**（所有环境都显示 AMD64）：
```
NAMES                              ARCH
model-converter-frontend-1        amd64
model-converter-backend-1         amd64
model-converter-redis-1           amd64
model-converter-celery-worker-1   amd64
```

---

## 🐳 方式二：Docker（推荐生产环境）

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 8 GB RAM
- 10 GB 磁盘空间

### 一键启动

```bash
cd model-converter

# 首次运行：构建镜像并启动（需要 10-20 分钟）
docker-compose up -d --build

# 后续启动：直接启动（< 1 分钟）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

**访问服务**：
- Web 界面: http://localhost:3000
- API 文档: http://localhost:8000/docs

**停止服务**：
```bash
docker-compose down
```

### 使用 Makefile

```bash
# Docker 方式启动
make docker-build    # 构建镜像
make docker-up       # 启动服务
make docker-down     # 停止服务
make docker-logs     # 查看日志
```

### Docker 架构说明

```
┌─────────────────────────────────────────┐
│           Docker Compose                │
├─────────────────────────────────────────┤
│                                           │
│  ┌──────────────────────────────────┐   │
│  │  Frontend (Nginx + 静态文件)     │   │
│  │  端口: 3000                       │   │
│  └──────────────┬───────────────────┘   │
│                 │                        │
│  ┌──────────────▼───────────────────┐   │
│  │  Backend (FastAPI)               │   │
│  │  端口: 8000                       │   │
│  │  - Python 3.11                   │   │
│  │  - PyTorch + TensorFlow          │   │
│  │  - ST Edge AI                    │   │
│  └──────────────────────────────────┘   │
│                                           │
└─────────────────────────────────────────┘
```

### 镜像构建说明

**基础镜像**：`camthink/ne301-dev:latest`
- 包含 ST Edge AI 工具链
- 包含 ARM GCC 交叉编译器
- Ubuntu 22.04 + Python 3.11

**挂载目录**：
- `./backend:/app` - 后端代码（开发模式热重载）
- `./uploads:/app/uploads` - 上传的模型文件
- `./temp:/app/temp` - 临时转换文件
- `./outputs:/app/outputs` - 转换结果
- `../Model:/workspace/Model:ro` - NE301 Model 目录（只读）
- `../Script:/workspace/Script:ro` - NE301 Script 目录（只读）

---

## 💻 命令行工具

### 本地运行

```bash
# 基本用法
./convert.sh yolov8n.pt --preset yolov8n-480

# 使用 Makefile
make convert MODEL=yolov8n.pt PRESET=yolov8n-480

# 自定义类别数量
./convert.sh model.pt --preset yolov8n-480 --num-classes 10

# 使用校准数据集
./convert.sh model.pt --preset yolov8n-480 --calibration coco8.zip
```

### Docker 运行

```bash
# 在容器中执行命令
docker-compose exec backend python3 /app/convert.py \
  /app/uploads/model.pt --preset yolov8n-480
```

---

## 📖 使用指南

### 1. 上传模型文件

- 支持格式：`.pt`, `.pth`, `.onnx`
- 文件大小限制：500 MB

### 2. 选择配置预设

| 预设 | 输入尺寸 | 特点 |
|------|----------|------|
| yolov8n-256 | 256x256 | 快速检测，适合实时场景 |
| yolov8n-480 | 480x480 | **推荐**，平衡精度和性能 |
| yolov8n-640 | 640x640 | 高精度，推理速度较慢 |

### 3. 开始转换

点击"开始转换"按钮，系统将自动执行：
1. 验证模型文件 (5%)
2. PyTorch → TFLite 转换 (5-30%)
3. TFLite → C 模型 (30-60%)
4. 生成配置文件 (60-80%)
5. 打包 ZIP (80-100%)

转换时间：约 3-5 分钟

### 4. 下载结果

转换完成后，下载 `*.zip` 文件：
```bash
# 解压
unzip yolov8n_480_20260311_123456.zip

# 复制到 NE301 项目
cp yolov8n_480/* ../../../Model/weights/

# 烧录到设备
cd ../..
make flash-model
```

---

## 🔧 Makefile 快捷命令

```bash
# 本地运行
make help          # 显示帮助
make start         # 启动 Web 服务
make stop          # 停止服务
make restart       # 重启服务
make convert       # 命令行转换
make install       # 安装所有依赖
make clean         # 清理依赖和临时文件

# Docker 运行
make docker-build  # 构建 Docker 镜像
make docker-up     # 启动 Docker 服务
make docker-down   # 停止 Docker 服务
make docker-logs   # 查看 Docker 日志
```

---

## 🛠️ 开发指南

### 前端开发

```bash
cd frontend

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev

# 构建生产版本
pnpm build

# 代码检查
pnpm lint
```

### 后端开发

```bash
cd backend

# 本地开发
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py

# Docker 开发
docker-compose up -d --build
docker-compose logs -f backend
```

---

## 📋 环境变量配置

在 `backend/.env` 文件中配置：

```bash
# API 配置
API_PREFIX=/api/v1
HOST=0.0.0.0
PORT=8000
DEBUG=true

# 文件存储
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=524288000  # 500MB
TEMP_DIR=./temp
OUTPUT_DIR=./outputs

# NE301 项目路径
NE301_PROJECT_PATH=/workspace  # Docker 环境
# NE301_PROJECT_PATH=/path/to/ne301  # 本地环境

# ST Edge AI 路径（可选）
STEDGEAI_PATH=/opt/stedgeai
```

---

## ❓ 故障排查

### 本地运行问题

**Q: 转换失败，提示 "ML 库未安装"**
A: 安装完整的 ML 依赖：
```bash
cd backend
source venv/bin/activate
pip install ultralytics torch torchvision
```

**Q: ST Edge AI 相关错误**
A: 设置 `STEDGEAI_PATH` 环境变量指向 ST Edge AI 安装目录。

### Docker 问题

**Q: 镜像构建失败**
A: 检查网络连接，确保可以访问 Docker Hub 和 PyPI：
```bash
# 使用国内镜像源（如果需要）
# 编辑 /etc/docker/daemon.json 添加：
{
  "registry-mirrors": ["https://docker.mirrors.ustc.edu.cn"]
}
```

**Q: 容器启动失败**
A: 查看详细日志：
```bash
docker-compose logs backend
docker-compose ps
```

**Q: 转换时间过长**
A: 正常情况，YOLOv8n 480x480 转换约需 3-5 分钟。

**Q: 内存占用过高**
A: 限制 Docker 内存使用：
```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G
```

---

## 📂 项目结构

```
model-converter/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── core/        # 核心配置
│   │   ├── models/      # 数据模型
│   │   └── services/    # 业务逻辑（转换、任务管理）
│   ├── main.py          # 应用入口
│   ├── Dockerfile       # Docker 镜像构建
│   └── requirements.txt # Python 依赖
├── frontend/            # Preact 前端
│   ├── src/
│   │   ├── pages/      # 页面组件
│   │   ├── components/ # 可复用组件
│   │   └── services/   # API 客户端
│   ├── Dockerfile      # Docker 镜像构建
│   └── package.json
├── docker-compose.yml   # Docker 服务编排
├── convert.py           # 命令行工具
├── convert.sh           # Shell 封装
├── start.sh             # 一键启动脚本（本地）
├── stop.sh              # 停止脚本
├── Makefile             # 快捷命令
└── README.md            # 本文档
```

---

## 🤝 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Preact](https://preactjs.com/)
- [ST Edge AI](https://www.st.com/en/development-tools/stedgeai-core.html)

---

**最后更新**: 2026-03-11
**版本**: 2.0.0
