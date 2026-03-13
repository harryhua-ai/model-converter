# Docker 快速启动指南

## 🚀 一键启动

```bash
# 1. 进入项目目录
cd model-converter

# 2. 启动所有服务（首次运行需要 10-20 分钟构建镜像）
docker-compose up -d --build

# 3. 查看服务状态
docker-compose ps

# 4. 查看日志（可选）
docker-compose logs -f
```

## 🌐 访问服务

启动成功后，访问以下地址：

- **前端界面**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## 🔍 验证架构

```bash
# 检查所有容器的架构
./verify-arch.sh

# 或手动检查
docker ps --format "table {{.Names}}\t{{.Architecture}}"
```

### 预期输出

**Apple Silicon Mac**:
```
NAMES                              ARCH
model-converter-frontend-1        arm64
model-converter-backend-1         arm64
model-converter-redis-1           arm64
model-converter-celery-worker-1   arm64
```

**AMD64 Linux**:
```
NAMES                              ARCH
model-converter-frontend-1        amd64
model-converter-backend-1         amd64
model-converter-redis-1           amd64
model-converter-celery-worker-1   amd64
```

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

# 查看服务日志
docker-compose logs -f [service_name]
```

### 镜像管理

```bash
# 重新构建镜像
docker-compose build

# 强制重新构建（无缓存）
docker-compose build --no-cache

# 查看镜像列表
docker images | grep ne301-model-converter
```

### 故障排查

```bash
# 查看所有容器状态
docker ps -a

# 查看特定服务日志
docker-compose logs backend
docker-compose logs celery-worker

# 进入容器调试
docker-compose exec backend bash
docker-compose exec celery-worker bash
```

## 📊 性能说明

### Apple Silicon 开发环境

- **架构**: ARM64 原生
- **性能**: 100% 原生
- **说明**: Docker 自动使用 ARM64，无需 Rosetta 2

### AMD64 生产环境

- **架构**: AMD64 原生
- **性能**: 100% 原生
- **说明**: Docker 自动使用 AMD64

### 模型转换时间

| 模型 | 预计时间 | 说明 |
|------|----------|------|
| YOLOv8n-256 | 10-15 分钟 | 小模型 |
| YOLOv8n-480 | 15-20 分钟 | 中等模型 |
| YOLOv8n-640 | 20-25 分钟 | 大模型 |

## 🔧 故障排查

### 问题1: 端口已被占用

**错误信息**: `port is already allocated`

**解决方案**:
```bash
# 查看占用端口的进程
lsof -i :3000
lsof -i :8000

# 停止占用端口的进程
kill -9 <PID>

# 或修改 docker-compose.yml 中的端口映射
```

### 问题2: 容器启动失败

**解决方案**:
```bash
# 查看详细错误日志
docker-compose logs [service_name]

# 重新构建镜像
docker-compose build --no-cache [service_name]

# 清理并重启
docker-compose down
docker-compose up -d --build
```

### 问题3: 模型转换失败

**解决方案**:
```bash
# 检查 Celery Worker 状态
docker-compose logs celery-worker

# 验证 Model 目录挂载
docker-compose exec backend ls -la /workspace/Model

# 验证 Script 目录挂载
docker-compose exec backend ls -la /workspace/Script
```

## 📚 更多信息

- **完整文档**: [README.md](README.md)
- **架构说明**: [DOCKER_ARCHITECTURE.md](DOCKER_ARCHITECTURE.md)
- **实施报告**: [IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md)

## 💡 提示

1. **首次启动**：构建镜像需要 10-20 分钟，请耐心等待
2. **后续启动**：镜像已缓存，启动时间 < 1 分钟
3. **资源要求**：建议 8GB RAM，10GB 磁盘空间
4. **架构自动适配**：无需手动配置，Docker 自动选择最优架构
