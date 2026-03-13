# Model Converter - 容器化部署指南

## 前提条件

- Docker Desktop（macOS/Windows）或 Docker Engine（Linux）
- Docker Compose

## 快速开始

### 1. 克隆项目

```bash
git clone <repo>
cd model-converter
```

### 2. 一键部署

```bash
chmod +x deploy.sh
./deploy.sh
```

### 3. 使用

访问 http://localhost:8000

## 前端 Docker 化

### 架构说明

**单容器部署**（前端 + 后端）:
```
┌─────────────────────────────────────────┐
│   Docker Container (model-converter-api) │
│  ┌──────────┐         ┌──────────┐      │
│  │ Frontend │─────▶   │ Backend  │      │
│  │  (dist)  │         │ (FastAPI)│      │
│  └──────────┘         └──────────┘      │
│         ▲                    │          │
│         │                    ▼          │
│    Static Files    Docker Adapter       │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│     Docker Container (NE301 Tools)       │
│  PyTorch → TFLite → NE301 .bin           │
└─────────────────────────────────────────┘
```

**多阶段构建**:
- **阶段 1**: node:20-slim（构建前端）
  - 安装前端依赖（npm install）
  - 构建生产版本（npm run build）
  - 生成优化后的静态文件

- **阶段 2**: python:3.10-slim（运行后端）
  - 安装 Python 依赖
  - 复制后端代码
  - **从前端阶段复制构建产物**
  - 启动 FastAPI 服务

### Dockerfile 结构

```dockerfile
# ===== 阶段 1: 构建前端 =====
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ===== 阶段 2: 构建后端 =====
FROM python:3.10-slim

WORKDIR /app
# 安装系统依赖和 Python 包
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

# 复制后端代码
COPY backend/app/ ./app/
COPY backend/tools/ ./tools/

# 从前端构建阶段复制构建产物
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# 启动服务
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 性能指标

- **镜像大小**: 约 1.01 GB
- **前端构建时间**: ~1.7 秒
- **依赖安装时间**: ~3.3 秒
- **静态资源大小**:
  - HTML: 0.73 kB (gzip: 0.43 kB)
  - CSS: 42.50 kB (gzip: 6.66 kB)
  - JS: 167.94 kB (gzip: 58.30 kB)

### 静态文件服务

**后端配置**（`backend/app/main.py`）:
```python
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# 获取应用根目录
app_root = Path(__file__).parent.parent
frontend_path = app_root / "frontend" / "dist"

# 挂载静态文件
app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
```

**关键点**:
- 静态文件路径：`/app/frontend/dist`
- `html=True` 支持 SPA 路由（所有路由返回 index.html）
- FastAPI 直接提供静态文件，无需 Nginx

### 部署验证

```bash
# 1. 验证镜像构建
docker images | grep model-converter-api

# 2. 验证容器内前端文件
docker exec model-converter-api ls -la /app/frontend/dist

# 3. 验证前端访问
curl -I http://localhost:8000/

# 4. 验证 API 访问
curl http://localhost:8000/api/setup/check
```

## 旧版架构说明（双容器）

```
宿主机（只需 Docker）
    │
    └─ Docker Compose
        ├─ api 容器
        │   ├─ FastAPI
        │   ├─ PyTorch → TFLite（Ultralytics）
        │   ├─ TFLite → 量化 TFLite（ST 量化脚本）
        │   └─ Docker SDK
        │
        └─ ne301-dev 容器（按需调用）
            └─ 量化 TFLite → NE301 .bin
```

## 关键特性

1. **单容器部署** - 前端和后端集成在一个镜像中
2. **零依赖部署** - 宿主机只需 Docker
3. **Docker-in-Docker** - API 容器可以调用 NE301 容器
4. **参考 AIToolStack** - 基于成熟的架构实现
5. **完整转换流程** - PyTorch → TFLite → 量化 → NE301 .bin

## 开发模式

```bash
docker-compose -f docker-compose.dev.yml up --build
```

支持代码热重载，修改 `backend/app/` 中的文件会自动重新加载。
