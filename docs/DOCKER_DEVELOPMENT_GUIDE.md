# Docker 部署指南

## 开发模式 vs 生产模式

### 开发模式（代码挂载）

**用途**: 快速开发调试，代码修改立即生效

**配置**: `docker-compose.dev.yml` 或修改 `docker-compose.yml` 添加挂载:

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
  - uploads:/app/uploads:rw
  - outputs:/app/outputs:rw
  - ./ne301:/workspace/ne301:rw
  # 开发模式：挂载代码目录实现热重载
  - ./backend/app:/app/app:ro
  - ./backend/tools:/app/tools:ro
```

**何时使用**:
- ✅ 修改 Python 代码后需要立即验证
- ✅ 开发新功能，需要频繁调试
- ✅ 修复 Bug，需要快速测试

**重启方式**:
```bash
# 代码挂载模式：只需重启容器，无需重新构建
docker-compose restart api
```

### 生产模式（镜像内置）

**用途**: 生产部署，代码烘焙到镜像中

**配置**: `docker-compose.yml` (默认配置)

**何时使用**:
- ✅ 部署到生产环境
- ✅ 代码修改验证完成后，构建最终镜像

**重启方式**:
```bash
# 生产模式：需要重新构建镜像
docker-compose build api
docker-compose up -d api
```

---

## 何时需要重新构建 Docker 镜像？

### ❌ 不需要重新构建的情况

**使用开发模式（代码挂载）时**:
1. ✅ 修改了 `backend/app/` 下的 Python 代码
2. ✅ 修改了 `backend/tools/` 下的工具脚本
3. ✅ 只需要代码修改立即生效

**解决方法**: 只需重启容器
```bash
docker-compose restart api
```

### ✅ 需要重新构建的情况

**以下情况必须重新构建镜像**:

1. **修改了依赖** (`backend/requirements.txt`)
   ```bash
   docker-compose build --no-cache api
   ```

2. **修改了前端代码** (`frontend/`)
   ```bash
   # 前端构建在 Dockerfile 的第一阶段
   docker-compose build --no-cache api
   ```

3. **修改了 Dockerfile**
   ```bash
   docker-compose build --no-cache api
   ```

4. **修改了系统依赖** (Dockerfile 中的 `apt-get install`)
   ```bash
   docker-compose build --no-cache api
   ```

5. **切换到生产模式部署**
   ```bash
   # 移除代码挂载，使用内置镜像
   docker-compose down
   # 编辑 docker-compose.yml 移除代码挂载
   docker-compose build api
   docker-compose up -d
   ```

---

## 推荐工作流

### 开发阶段（使用挂载模式）

```bash
# 1. 首次启动（构建镜像）
docker-compose build api
docker-compose up -d

# 2. 修改 Python 代码后
# 只需重启容器，代码挂载会立即生效
docker-compose restart api

# 3. 查看日志验证修改
docker-compose logs -f api

# 4. 持续开发循环
# 修改代码 → 重启容器 → 验证 → 修改代码 → ...
```

### 验证完成后（切换到生产模式）

```bash
# 1. 移除 docker-compose.yml 中的代码挂载
# 删除这两行:
#   - ./backend/app:/app/app:ro
#   - ./backend/tools:/app/tools:ro

# 2. 重新构建镜像（包含所有代码）
docker-compose build --no-cache api

# 3. 启动生产容器
docker-compose up -d

# 4. 验证生产镜像
docker-compose logs -f api
```

---

## 常见问题

### Q: 我修改了代码，但容器里还是旧代码？

**A**: 检查是否使用了代码挂载:

```bash
# 查看挂载情况
docker inspect model-converter-api | grep -A 10 "Mounts"

# 如果没有挂载，添加挂载配置并重启
# 编辑 docker-compose.yml 添加:
#   - ./backend/app:/app/app:ro
#   - ./backend/tools:/app/tools:ro

# 重启容器
docker-compose down
docker-compose up -d
```

### Q: 为什么开发模式要使用 `:ro` (只读挂载)？

**A**: 防止容器意外修改宿主机代码:
- 容器只读取代码，不应修改
- 宿主机修改代码，容器立即看到
- 避免权限和同步问题

### Q: 前端代码修改后如何生效？

**A**: 前端代码在 Dockerfile 第一阶段构建，必须重新构建镜像:

```bash
# 1. 修改 frontend/ 代码

# 2. 重新构建镜像
docker-compose build --no-cache api

# 3. 重启容器
docker-compose up -d
```

或者使用 `docker-compose.dev.yml` (如果配置了前端开发服务器):
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### Q: 如何验证挂载是否生效？

**A**: 检查容器内的文件时间戳:

```bash
# 1. 修改宿主机文件
touch backend/app/core/ne301_config.py

# 2. 检查容器内文件时间戳
docker exec model-converter-api ls -l /app/app/core/ne301_config.py

# 3. 如果时间戳是最新的，说明挂载生效
```

---

## 性能对比

| 操作 | 挂载模式 | 镜像模式 |
|------|---------|---------|
| 代码修改生效时间 | ~2 秒 (重启) | ~5-10 分钟 (重建) |
| 镜像大小 | 1.01 GB | 1.01 GB |
| 适用场景 | 开发调试 | 生产部署 |
| 依赖修改 | 需要重建 | 需要重建 |
| 前端修改 | 需要重建 | 需要重建 |

---

## 最佳实践

1. **开发时始终使用挂载模式**
   - 快速迭代
   - 节省时间
   - 立即验证

2. **验证完成后切换到生产模式**
   - 确保镜像包含所有修改
   - 测试生产环境行为
   - 避免挂载相关问题

3. **修改依赖或前端时必须重建**
   - `requirements.txt` 变化
   - `frontend/` 代码变化
   - Dockerfile 变化

4. **使用版本控制**
   - `docker-compose.yml` - 生产配置
   - `docker-compose.dev.yml` - 开发配置
   - 通过 `-f` 参数切换

---

**最后更新**: 2026-03-17
**相关文档**:
- [FIX_SUMMARY.md](docs/FIX_SUMMARY.md) - 修复总结
- [README.docker.md](README.docker.md) - Docker 部署详细说明
