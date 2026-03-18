# Docker Compose 使用指南

本文档详细说明项目中三个 Docker Compose 配置文件的区别和使用场景。

---

## 📋 配置文件对比

| 配置文件 | 用途 | 镜像构建 | 启动速度 | 代码挂载 | 热重载 | 适用场景 |
|---------|------|---------|---------|---------|--------|---------|
| `docker-compose.yml` | **生产部署** | ✅ 每次构建 | ~2 分钟 | ✅ 只读 | ✅ | 生产环境、首次部署 |
| `docker-compose.dev.yml` | 开发环境 | ✅ 每次构建 | ~2 分钟 | ✅ 只读 | ✅ | 搭建开发环境 |
| `docker-compose.dev.local.yml` | **本地开发** | ❌ 预构建 | ~5 秒 | ✅ 读写 | ✅✅ | 日常开发（推荐） |

---

## 🎯 推荐使用方式

### 场景 1: 生产部署 ⭐

**使用配置**: `docker-compose.yml`

**特点**:
- ✅ 从源代码构建镜像
- ✅ 包含健康检查和自动重启
- ✅ 适合生产环境
- ⚠️ 启动较慢（需要构建）

**命令**:
```bash
# 1. 拉取 NE301 依赖镜像
docker pull camthink/ne301-dev:latest

# 2. 构建并启动（首次需要 ~2 分钟）
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 停止服务
docker-compose down
```

**适用场景**:
- ✅ 生产环境部署
- ✅ 首次搭建环境
- ✅ 修改 `requirements.txt` 后重新部署
- ✅ CI/CD 流水线

---

### 场景 2: 本地快速开发 ⭐⭐⭐（推荐）

**使用配置**: `docker-compose.dev.local.yml`

**特点**:
- ✅ 使用预构建镜像（启动快 ~5 秒）
- ✅ 代码读写挂载（支持 .pyc 缓存更新）
- ✅ 自动清除 Python 缓存
- ✅ 内存限制（4GB）
- ✅ 适合频繁修改和测试

**命令**:
```bash
# 1. 首次构建镜像（只需一次）
docker-compose build

# 2. 启动开发环境（~5 秒）
docker-compose -f docker-compose.dev.local.yml up -d

# 3. 修改 Python 代码后自动生效（~2 秒）
# 编辑 backend/app/... 文件
# 等待 2 秒，代码自动热重载

# 4. 查看日志
docker-compose -f docker-compose.dev.local.yml logs -f

# 5. 停止服务
docker-compose -f docker-compose.dev.local.yml down
```

**适用场景**:
- ✅ 日常开发（最推荐）
- ✅ 频繁修改 Python 代码
- ✅ 快速测试和验证
- ✅ 本地调试

**何时重新构建镜像**:
```bash
# 修改 requirements.txt 后
docker-compose build

# 修改 Dockerfile 后
docker-compose build --no-cache

# 重启开发环境
docker-compose -f docker-compose.dev.local.yml up -d
```

---

### 场景 3: 搭建开发环境

**使用配置**: `docker-compose.dev.yml`

**特点**:
- ✅ DEBUG 模式启用
- ✅ 从源代码构建
- ✅ 适合首次搭建环境
- ⚠️ 启动较慢

**命令**:
```bash
# 1. 构建并启动
docker-compose -f docker-compose.dev.yml up --build

# 2. 查看详细日志（DEBUG 模式）
docker-compose -f docker-compose.dev.yml logs -f

# 3. 停止服务
docker-compose -f docker-compose.dev.yml down
```

**适用场景**:
- ✅ 首次搭建开发环境
- ✅ 修改 `requirements.txt` 后验证
- ✅ 需要详细 DEBUG 日志

---

## 🔄 工作流程推荐

### 日常工作流（推荐）

```bash
# 1. 首次设置（只需一次）
docker-compose build

# 2. 启动开发环境（快速）
docker-compose -f docker-compose.dev.local.yml up -d

# 3. 开发和测试
# - 修改 backend/app/... 文件
# - 自动热重载（~2 秒）
# - 测试 API 和功能

# 4. 提交代码
git add .
git commit -m "feat: 添加新功能"

# 5. 结束工作
docker-compose -f docker-compose.dev.local.yml down
```

### 修改依赖后

```bash
# 1. 修改 requirements.txt
vim backend/requirements.txt

# 2. 重新构建镜像
docker-compose build

# 3. 重启开发环境
docker-compose -f docker-compose.dev.local.yml up -d

# 4. 验证新依赖
docker-compose -f docker-compose.dev.local.yml exec api pip list
```

### 部署到生产环境

```bash
# 1. 使用生产配置
docker-compose up -d

# 2. 验证服务
curl http://localhost:8000/health

# 3. 查看日志
docker-compose logs -f
```

---

## 🛠️ 常用命令速查

### 通用命令

```bash
# 查看运行状态
docker-compose ps

# 查看日志（实时）
docker-compose logs -f

# 进入容器
docker-compose exec api /bin/bash

# 重启服务
docker-compose restart

# 停止并删除容器
docker-compose down

# 停止并删除容器和卷
docker-compose down -v
```

### 开发环境专用

```bash
# 使用本地开发配置
docker-compose -f docker-compose.dev.local.yml up -d
docker-compose -f docker-compose.dev.local.yml logs -f
docker-compose -f docker-compose.dev.local.yml down

# 清除 Python 缓存
docker-compose -f docker-compose.dev.local.yml exec api \
  find /app/app -type d -name '__pycache__' -exec rm -rf {} +

# 查看容器内依赖
docker-compose -f docker-compose.dev.local.yml exec api pip list
```

### 生产环境专用

```bash
# 构建镜像
docker-compose build

# 强制重建（无缓存）
docker-compose build --no-cache

# 查看健康状态
docker inspect --format='{{.State.Health.Status}}' model-converter-api

# 查看资源使用
docker stats model-converter-api
```

---

## 📊 配置文件详解

### docker-compose.yml（生产）

**关键配置**:
```yaml
services:
  api:
    build:                    # 从源代码构建
      context: .
      dockerfile: backend/Dockerfile
    volumes:
      - ./backend/app:/app/app:ro      # 只读挂载
    restart: unless-stopped            # 自动重启
    healthcheck:                       # 健康检查
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
```

**优势**:
- ✅ 生产级别的稳定性
- ✅ 自动故障恢复
- ✅ 健康监控

**劣势**:
- ⚠️ 启动较慢（需要构建）
- ⚠️ 代码只读挂载

---

### docker-compose.dev.yml（开发）

**关键配置**:
```yaml
services:
  api:
    build:
      context: ./backend
    environment:
      - DEBUG=1               # DEBUG 模式
    volumes:
      - ./backend/app:/app/app:ro      # 只读挂载
```

**优势**:
- ✅ DEBUG 日志详细
- ✅ 构建上下文简单

**劣势**:
- ⚠️ 启动较慢（需要构建）
- ⚠️ 代码只读挂载

---

### docker-compose.dev.local.yml（本地快速开发）⭐

**关键配置**:
```yaml
services:
  api:
    image: model-converter-api          # 使用预构建镜像
    volumes:
      - ./backend/app:/app/app:rw       # 读写挂载
    deploy:
      resources:
        limits:
          memory: 4G                    # 内存限制
    command: ["sh", "-c", "find /app/app -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true && cd /app && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
```

**优势**:
- ✅ 启动最快（~5 秒）
- ✅ 代码读写挂载
- ✅ 自动清除缓存
- ✅ 内存限制保护

**劣势**:
- ⚠️ 需要先构建镜像
- ⚠️ 修改依赖后需重建

---

## 🔧 故障排查

### 问题 1: 镜像不存在

**错误**: `ERROR: image 'model-converter-api' not found`

**解决**:
```bash
# 先构建镜像
docker-compose build

# 再启动开发环境
docker-compose -f docker-compose.dev.local.yml up -d
```

---

### 问题 2: 代码修改不生效

**原因**: 使用了生产配置（`docker-compose.yml`）

**解决**:
```bash
# 方案 1: 重启容器
docker-compose restart

# 方案 2: 使用开发配置（推荐）
docker-compose -f docker-compose.dev.local.yml up -d
```

---

### 问题 3: 内存不足

**错误**: `ERROR: Service 'api' failed to build: OCI runtime create failed`

**解决**:
```bash
# 使用开发配置（已设置 4GB 限制）
docker-compose -f docker-compose.dev.local.yml up -d

# 或手动限制内存
docker-compose -f docker-compose.dev.local.yml up -d --memory 4g
```

---

### 问题 4: 端口被占用

**错误**: `ERROR: port is already allocated`

**解决**:
```bash
# 查看端口占用
lsof -i :8000

# 停止旧容器
docker-compose down

# 重新启动
docker-compose up -d
```

---

## 💡 最佳实践

### 1. 日常开发

```bash
# ✅ 推荐：使用本地快速开发配置
docker-compose -f docker-compose.dev.local.yml up -d
```

### 2. 修改依赖

```bash
# ✅ 推荐：重新构建后使用开发配置
docker-compose build
docker-compose -f docker-compose.dev.local.yml up -d
```

### 3. 生产部署

```bash
# ✅ 推荐：使用生产配置
docker-compose up -d
```

### 4. 清理环境

```bash
# ✅ 推荐：定期清理
docker-compose down
docker system prune -f
```

---

## 📚 相关文档

- [Docker 部署指南](../README.docker.md) - 详细的 Docker 部署说明
- [开发指南](../CLAUDE.md) - 完整的开发文档
- [故障排查](../CLAUDE.md#故障排查) - 常见问题解决

---

**最后更新**: 2026-03-18
**文档版本**: 1.0.0