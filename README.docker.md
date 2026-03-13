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

访问 http://localhost:8000/docs 查看 API 文档并测试转换

## 架构说明

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

1. **零依赖部署** - 宿主机只需 Docker
2. **Docker-in-Docker** - API 容器可以调用 NE301 容器
3. **参考 AIToolStack** - 基于成熟的架构实现
4. **完整转换流程** - PyTorch → TFLite → 量化 → NE301 .bin

## 开发模式

```bash
docker-compose -f docker-compose.dev.yml up --build
```

支持代码热重载，修改 `backend/app/` 中的文件会自动重新加载。
