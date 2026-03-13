# Docker 快速入门指南

本文档介绍如何使用 Docker 运行 NE301 模型转换工具。

## 📋 前置检查

### 1. 安装 Docker

**macOS**：
```bash
# 下载并安装 Docker Desktop
# https://www.docker.com/products/docker-desktop/

# 验证安装
docker --version
docker-compose version
```

**Linux**：
```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 安装 Docker Compose
sudo apt-get install docker-compose

# 验证安装
docker --version
docker-compose version
```

**Windows**：
```bash
# 下载并安装 Docker Desktop
# https://www.docker.com/products/docker-desktop/
```

### 2. 检查系统资源

```bash
# 检查可用内存
# macOS: 打开"活动监视器"
# Linux: free -h

# 建议：
# - RAM: 至少 8 GB
# - 磁盘: 至少 10 GB 可用空间
```

---

## 🚀 快速开始

### 步骤 1：克隆项目

```bash
git clone <your-repo>
cd ne301/model-converter
```

### 步骤 2：配置环境变量（可选）

```bash
# 复制环境变量模板
cp backend/.env.example backend/.env

# 根据需要编辑配置
vim backend/.env
```

### 步骤 3：构建并启动服务

```bash
# 方式 1: 使用 Docker Compose（推荐）
docker-compose up -d --build

# 方式 2: 使用 Makefile
make docker-build  # 构建镜像
make docker-up     # 启动服务
```

**首次运行说明**：
- 下载基础镜像：`camthink/ne301-dev:latest` (~7GB)
- 构建后端镜像：安装 Python 依赖 (~2GB)
- 构建前端镜像：打包静态文件
- **预计时间**：10-20 分钟（取决于网络速度）

**后续启动**：
```bash
docker-compose up -d  # < 1 分钟
```

### 步骤 4：验证服务

```bash
# 检查服务状态
docker-compose ps

# 应该看到：
# NAME                  STATUS         PORTS
# backend-1             Up             0.0.0.0:8000->8000/tcp
# frontend-1            Up             0.0.0.0:3000->80/tcp

# 测试后端健康检查
curl http://localhost:8000/health

# 应该返回：
# {"status":"healthy","service":"YOLO 模型转换工具","version":"2.0.0"}
```

### 步骤 5：访问服务

- **Web 界面**: http://localhost:3000
- **API 文档**: http://localhost:8000/docs

---

## 🛠️ 常用命令

### 服务管理

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看服务状态
docker-compose ps

# 查看资源使用
docker stats
```

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs

# 查看后端日志
docker-compose logs -f backend

# 查看前端日志
docker-compose logs -f frontend

# 查看最近 100 行日志
docker-compose logs --tail=100 backend
```

### 进入容器

```bash
# 进入后端容器
docker-compose exec backend bash

# 在容器中执行命令
docker-compose exec backend python3 --version

# 查看容器环境变量
docker-compose exec backend env
```

### 重新构建

```bash
# 重新构建并启动
docker-compose up -d --build

# 仅重新构建后端
docker-compose build backend

# 强制重新构建（无缓存）
docker-compose build --no-cache
```

---

## 📂 数据持久化

### 挂载目录

```yaml
volumes:
  - ./uploads:/app/uploads      # 上传的模型文件
  - ./temp:/app/temp            # 临时转换文件
  - ./outputs:/app/outputs      # 转换结果
  - ../Model:/workspace/Model   # NE301 Model 目录（只读）
  - ../Script:/workspace/Script # NE301 Script 目录（只读）
```

### 备份和恢复

```bash
# 备份转换结果
docker cp backend-1:/app/outputs ./backup/

# 恢复转换结果
docker cp ./backup/ backend-1:/app/outputs/
```

---

## 🔧 故障排查

### 问题 1：端口被占用

```bash
# 检查端口占用
lsof -i :8000
lsof -i :3000

# 解决方法 1: 停止占用端口的进程
kill -9 <PID>

# 解决方法 2: 修改端口映射
# 编辑 docker-compose.yml:
# ports:
#   - "8888:8000"  # 使用 8888 端口
```

### 问题 2：镜像构建失败

```bash
# 清理 Docker 缓存
docker system prune -a

# 重新构建
docker-compose build --no-cache

# 使用国内镜像源（如果网络问题）
# 编辑 /etc/docker/daemon.json:
{
  "registry-mirrors": ["https://docker.mirrors.ustc.edu.cn"]
}
```

### 问题 3：容器启动失败

```bash
# 查看详细日志
docker-compose logs backend

# 检查容器状态
docker-compose ps -a

# 进入容器检查
docker-compose run --rm backend bash
```

### 问题 4：内存不足

```bash
# 增加 Docker 内存限制（Docker Desktop）
# Settings -> Resources -> Memory -> 8GB+

# 或限制容器内存
# 编辑 docker-compose.yml:
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G
```

### 问题 5：转换失败

```bash
# 检查 ST Edge AI 是否可用
docker-compose exec backend bash -c "which stedgeai"

# 检查 NE301 项目路径
docker-compose exec backend ls -la /workspace/Model

# 查看转换日志
docker-compose logs backend | grep -i error
```

---

## 🔐 安全建议

### 生产环境部署

1. **修改默认端口**
2. **启用 HTTPS**
3. **限制访问 IP**
4. **定期更新镜像**

```yaml
# docker-compose.prod.yml
services:
  backend:
    ports:
      - "127.0.0.1:8000:8000"  # 仅本地访问
    environment:
      - DEBUG=false
```

---

## 📊 性能优化

### 加速构建

```bash
# 使用 BuildKit
export DOCKER_BUILDKIT=1
docker-compose build

# 并行构建
docker-compose build --parallel
```

### 减小镜像大小

```dockerfile
# 多阶段构建
FROM camthink/ne301-dev:latest AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
```

---

## 🆚 Docker vs 本地运行

| 特性 | Docker | 本地运行 |
|------|--------|----------|
| 环境一致性 | ✅ 完全一致 | ⚠️ 依赖系统 |
| 启动速度 | ⚠️ 首次慢 | ✅ 快速 |
| 资源占用 | ❌ 较高 | ✅ 较低 |
| 调试难度 | ⚠️ 需要进入容器 | ✅ 直接调试 |
| 依赖管理 | ✅ 自动 | ⚠️ 手动 |
| 迁移性 | ✅ 容易 | ❌ 困难 |

---

## 📚 更多资源

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [NE301 项目文档](../README.md)

---

**最后更新**: 2026-03-11
