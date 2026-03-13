# 并行构建快速指南

## 概述

并行构建系统允许 Frontend 和 Backend 同时构建，节省时间并提供错误隔离。

## 基本用法

### 1. 并行构建所有镜像（推荐）

```bash
# 使用 Makefile（推荐）
make build-parallel

# 或直接使用脚本
./build-parallel.sh
```

**输出示例：**
```
=== 开始并行构建 ===
正在构建: frontend, backend (独立并行)

[10:15:23] 开始构建 frontend...
[10:15:23] 开始构建 backend...

[10:16:45] ✅ Frontend 构建成功
[10:30:12] ✅ Backend 构建成功
✅ Celery Worker (复用 Backend 镜像)

=== 构建总结 ===
🎉 所有服务构建成功！
```

### 2. 仅构建特定服务

```bash
# 仅构建前端
make build-frontend

# 仅构建后端（包括 Celery Worker）
make build-backend

# 或使用脚本
./build-parallel.sh frontend
./build-parallel.sh backend
```

### 3. 验证构建结果

```bash
# 验证所有镜像
make verify

# 或
./verify-build.sh

# 查看构建状态
make build-status
```

### 4. 启动服务

```bash
# 验证通过后启动
make docker-up

# 查看服务状态
docker-compose ps
```

## 错误处理

### 场景：Frontend 成功，Backend 失败

```bash
# 1. 查看失败日志
make build-logs-backend
# 或
tail -100 logs/build-backend.log

# 2. 重新构建失败的 service（不影响已成功的）
make retry-backend
# 或
./build-parallel.sh backend

# 3. 验证所有镜像
make verify
```

### 查看构建日志

```bash
# 前端日志
make build-logs-frontend

# 后端日志
make build-logs-backend

# 直接查看
tail -f logs/build-backend.log
less logs/build-frontend.log
```

## 清理

```bash
# 清理构建日志
make build-clean-logs

# 清理 Docker 资源
make clean-docker
```

## 架构优化

### 镜像复用

- **Backend** 和 **Celery Worker** 共享同一个镜像 `ne301-model-converter-backend:v2`
- Celery Worker 不再重复构建，节省 15-20 分钟
- Frontend 独立构建，与 Backend 并行执行

### 错误隔离

- 每个服务的构建日志独立保存到 `logs/build-{service}.log`
- 某个服务构建失败不影响其他服务
- 可以单独重新构建失败的服务，无需等待全部完成

## 时间对比

| 方式 | 串行构建 | 并行构建 | 节省时间 |
|------|---------|---------|---------|
| 全部构建 | 15-20 分钟 | ~15 分钟 | ~5 分钟 |
| 失败重试 | 15-20 分钟 | 仅失败部分 | **大幅减少** |

## 故障排查

### 构建卡住

```bash
# 检查 Docker 进程
docker ps

# 查看实时日志
tail -f logs/build-backend.log

# 强制停止并重试
docker-compose down
make clean-docker
make build-parallel
```

### 镜像标签混乱

```bash
# 查看所有镜像
docker images | grep ne301-model-converter

# 清理旧镜像
docker rmi ne301-model-converter-backend:v1

# 或清理所有未使用镜像
docker image prune -a
```

### 磁盘空间不足

```bash
# 检查空间
df -h /

# 清理 Docker 资源
docker system prune -a

# 清理构建缓存
docker builder prune
```

## 所有可用命令

```bash
make help                    # 查看所有命令

# 并行构建
make build-parallel          # 并行构建所有镜像
make build-frontend          # 仅构建前端
make build-backend           # 仅构建后端
make retry-backend           # 重新构建后端（失败重试）

# 状态和验证
make build-status            # 查看构建状态
make verify                  # 验证 Docker 镜像

# 日志
make build-logs-frontend     # 查看前端构建日志
make build-logs-backend      # 查看后端构建日志
make build-clean-logs        # 清理构建日志

# Docker 操作
make docker-up               # 启动 Docker 服务
make docker-down             # 停止 Docker 服务
make docker-logs             # 查看 Docker 日志
make clean-docker            # 清理 Docker 资源
```

## 文件结构

```
model-converter/
├── build-parallel.sh       # 并行构建脚本
├── verify-build.sh         # 验证脚本
├── Makefile                # 包含新的构建命令
├── docker-compose.yml      # Celery Worker 复用 Backend 镜像
├── logs/                   # 构建日志目录（自动创建）
│   ├── build-frontend.log
│   └── build-backend.log
└── .gitignore              # 已包含 logs/ 目录
```

---

**最后更新**: 2026-03-12
**预计构建时间**: 首次 15-20 分钟（并行），失败重试仅失败部分时间
