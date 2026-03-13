# Model Converter - 快速开始

## 使用远程 Docker 镜像（推荐）

本项目使用预构建的 `camthink/ne301-dev:latest` Docker 镜像，包含：
- ST Edge AI 工具链
- ARM GCC 编译器
- Python 3.11
- 所有必需的系统库

### 一键启动

```bash
cd model-converter

# 首次使用：拉取基础镜像并构建
make dev

# 或分步执行：
# make build  # 构建后端镜像
# make dev    # 启动所有服务
```

### 服务组件

| 服务 | 说明 | 访问地址 |
|------|------|----------|
| Frontend | Preact 开发服务器 | http://localhost:3000 |
| Backend API | FastAPI 服务 | http://localhost:8000 |
| API 文档 | Swagger UI | http://localhost:8000/docs |
| Redis | 消息队列 | localhost:6379 |

### 目录结构

```
model-converter/
├── backend/          # FastAPI 后端
│   ├── Dockerfile    # 使用 camthink/ne301-dev:latest
│   ├── main.py       # 应用入口
│   └── requirements.txt
├── frontend/         # Preact 前端
│   ├── src/
│   └── package.json
├── uploads/          # 上传的模型文件
├── temp/             # 临时转换文件
└── outputs/          # 转换结果
```

### 常用命令

```bash
make dev          # 启动完整开发环境
make backend      # 仅启动后端 (Docker)
make frontend     # 仅启动前端 (本地)
make stop         # 停止所有服务
make logs         # 查看后端日志
make build        # 构建/更新后端镜像
make clean        # 清理容器和资源
```

### 首次构建说明

首次运行 `make dev` 时会：

1. **拉取基础镜像** (~7GB)
   ```bash
   docker pull camthink/ne301-dev:latest
   ```
   预计时间：5-15 分钟（取决于网络）

2. **安装 Python 依赖**
   - Python 3.11
   - OpenGL 库
   - PyTorch, TensorFlow, Ultralytics
   预计时间：15-30 分钟

3. **启动服务**
   - Redis + Backend (Docker)
   - Frontend (本地 Vite)

### 故障排查

**问题**: 端口被占用
```bash
# 检查端口占用
lsof -i :8000
lsof -i :3000

# 停止占用端口的进程
kill -9 <PID>
```

**问题**: 后端无法启动
```bash
# 查看后端日志
make logs

# 或使用 docker-compose
docker compose -f docker-compose-dev.yml logs -f backend
```

**问题**: 镜像拉取失败
```bash
# 手动拉取镜像
docker pull camthink/ne301-dev:latest

# 检查网络连接
ping hub.docker.com
```

**问题**: ML 库导入失败
```bash
# 重新构建镜像
make build
```

### 开发模式

**前端本地开发**（推荐）：
```bash
# 后端 Docker + 前端本地
make backend    # 启动后端
cd frontend
pnpm install
pnpm dev        # 启动前端
```

**全 Docker 模式**：
```bash
# 修改 docker-compose-dev.yml，添加前端服务
docker compose -f docker-compose-dev.yml up
```

### 技术栈

- **前端**: Preact 10 + TypeScript + Vite + Tailwind CSS
- **后端**: FastAPI + Python 3.11 + Celery + Redis
- **ML 库**: PyTorch 2.10, TensorFlow 2.21, Ultralytics 8.4
- **基础镜像**: camthink/ne301-dev:latest (7.4GB)

### 资源占用

- **Docker 镜像**: ~23 GB
- **运行内存**: ~2-4 GB
- **磁盘空间**: 至少 30 GB 可用

### 相关链接

- [项目 README](../README.md)
- [CLAUDE.md](../CLAUDE.md)
- [Docker Hub](https://hub.docker.com/r/camthink/ne301-dev)
