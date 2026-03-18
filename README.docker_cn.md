# NE301 Model Converter - Docker 部署指南

## 快速开始

### 前置要求

- **Docker Desktop** 已安装并运行
- **4GB+ 内存** 可用于 Docker
- **10GB+ 磁盘空间** 用于 Docker 镜像

### 一键部署

```bash
# 1. 拉取 NE301 依赖镜像
docker pull camthink/ne301-dev:latest

# 2. 构建并启动服务
docker-compose up -d

# 3. 访问 Web 界面
# 在浏览器中打开 http://localhost:8000
```

**部署完成！** 现在可以开始转换模型了。

---

## Docker Compose 配置选项

本项目提供三个 Docker Compose 配置文件，适用于不同场景：

| 文件 | 用途 | 启动速度 | 适用场景 |
|------|------|---------|---------|
| `docker-compose.yml` | **生产部署** | ~2 分钟 | 生产环境、首次部署 |
| `docker-compose.dev.yml` | 开发环境 | ~2 分钟 | 搭建开发环境 |
| `docker-compose.dev.local.yml` | **本地开发** | ~5 秒 | 日常开发（推荐） |

### 生产部署（推荐）

```bash
# 使用生产配置构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 本地快速开发（最快）

```bash
# 首次构建镜像
docker-compose build

# 使用本地开发配置启动（~5 秒）
docker-compose -f docker-compose.dev.local.yml up -d

# 代码修改自动生效（~2 秒）
# 无需重建镜像即可应用 Python 代码修改

# 查看日志
docker-compose -f docker-compose.dev.local.yml logs -f
```

---

## 何时需要重建 Docker 镜像

### 无需重建（代码挂载模式）

使用 `docker-compose.dev.local.yml` 时：
- 修改了 `backend/app/` 下的 Python 文件
- 修改了 `backend/tools/` 下的脚本

**解决方法**：只需重启容器
```bash
docker-compose -f docker-compose.dev.local.yml restart api
```

### 必须重建

以下情况必须重新构建镜像：

1. **修改了 `requirements.txt`**
   ```bash
   docker-compose build --no-cache api
   ```

2. **修改了前端代码** (`frontend/`)
   ```bash
   docker-compose build --no-cache api
   ```

3. **修改了 `Dockerfile`**
   ```bash
   docker-compose build --no-cache api
   ```

---

## 环境变量配置

创建 `backend/.env` 文件（可选）：

```env
# Docker 配置
NE301_DOCKER_IMAGE=camthink/ne301-dev:latest
NE301_PROJECT_PATH=/app/ne301

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=False

# 日志级别
LOG_LEVEL=INFO

# 文件路径
UPLOAD_DIR=./uploads
TEMP_DIR=./temp
OUTPUT_DIR=./outputs
MAX_UPLOAD_SIZE=524288000  # 500MB
```

---

## 常用命令

### 服务管理

```bash
# 查看状态
docker-compose ps

# 查看日志（实时）
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止并删除容器
docker-compose down

# 停止并删除容器和卷
docker-compose down -v
```

### 容器操作

```bash
# 进入容器终端
docker-compose exec api /bin/bash

# 检查容器健康状态
docker inspect --format='{{.State.Health.Status}}' model-converter-api

# 查看资源使用
docker stats model-converter-api
```

### 镜像管理

```bash
# 构建镜像
docker-compose build

# 强制重建（无缓存）
docker-compose build --no-cache

# 查看镜像
docker images | grep model-converter
```

---

## 故障排查

### Docker 未运行

**错误**: `Cannot connect to the Docker daemon`

**解决方法**:
1. 启动 Docker Desktop
2. 验证: `docker ps`

### 镜像拉取失败

**错误**: `failed to resolve reference`

**解决方法**:
```bash
# 检查网络连接
# 手动拉取镜像
docker pull camthink/ne301-dev:latest
```

### 端口被占用

**错误**: `port is already allocated`

**解决方法**:
```bash
# 查找占用端口 8000 的进程
lsof -i :8000

# 停止旧容器
docker-compose down

# 重启服务
docker-compose up -d
```

### 内存不足

**错误**: `OCI runtime create failed`

**解决方法**:
```bash
# 使用带内存限制的开发配置
docker-compose -f docker-compose.dev.local.yml up -d

# 或在 Docker Desktop 设置中增加内存限制
```

### 代码修改不生效

**原因**: 使用了生产配置，代码未挂载

**解决方法**:
```bash
# 方案 1: 重启容器
docker-compose restart

# 方案 2: 使用开发配置（推荐）
docker-compose -f docker-compose.dev.local.yml up -d
```

---

## 架构说明

### 单容器部署

```
┌─────────────────────────────────────────┐
│    Docker Container (API + Frontend)     │
│  ┌──────────┐         ┌──────────┐      │
│  │ Frontend │─────▶   │ Backend  │      │
│  │ (dist/)  │         │ (FastAPI)│      │
│  └──────────┘         └──────────┘      │
│                              │          │
│                              ▼          │
│                    Docker Adapter       │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│     Docker Container (NE301 Tools)       │
│  PyTorch → TFLite → NE301 .bin           │
└─────────────────────────────────────────┘
```

### 多阶段构建

- **阶段 1**: `node:20-slim`（构建前端）
- **阶段 2**: `python:3.10-slim`（运行后端）
- **镜像大小**: 约 1.01 GB

---

## 性能对比

| 操作 | 代码挂载模式 | 镜像内置模式 |
|------|------------|-------------|
| 代码修改生效 | ~2 秒（重启） | ~5-10 分钟（重建） |
| 镜像大小 | 1.01 GB | 1.01 GB |
| 适用场景 | 开发调试 | 生产部署 |
| 依赖修改 | 需要重建 | 需要重建 |
| 前端修改 | 需要重建 | 需要重建 |

---

## 最佳实践

1. **日常开发使用开发配置**
   ```bash
   docker-compose -f docker-compose.dev.local.yml up -d
   ```

2. **修改依赖后重建镜像**
   ```bash
   docker-compose build
   ```

3. **生产部署使用生产配置**
   ```bash
   docker-compose up -d
   ```

4. **定期清理环境**
   ```bash
   docker-compose down
   docker system prune -f
   ```

---

## 相关文档

- [Docker Compose 使用指南](docs/DOCKER_COMPOSE_GUIDE.md) - 三种配置的详细对比
- [快速开始指南](docs/QUICK_START_cn.md) - 5 分钟上手指南
- [用户指南](docs/USER_GUIDE_cn.md) - 完整功能文档
- [开发文档](CLAUDE.md) - 完整开发文档

---

**最后更新**: 2026-03-18
**文档版本**: 1.0.0
