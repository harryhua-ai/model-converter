# Docker 架构问题 - 最终方案

## 📊 问题诊断总结

### 根本原因

基础镜像 `camthink/ne301-dev:latest` **仅支持 AMD64 架构**：

```bash
$ docker inspect camthink/ne301-dev:latest --format '{{.Architecture}}'
amd64
```

### 导致的问题

1. **Apple Silicon 开发者**：
   - AMD64 镜像通过 Rosetta 2 运行
   - PyTorch 量化时遇到 **SIGILL (非法指令)** 错误
   - 无法完成完整的模型转换流程

2. **AMD64 用户**：
   - 原生 AMD64 镜像，所有功能正常
   - 无任何问题

---

## ✅ 最终方案：统一配置 + 明确限制

### 配置文件

**单一配置文件**：`docker-compose.yml`
- 无平台约束
- 自动使用基础镜像（AMD64）
- 适用于所有环境

### 使用说明

**用户（AMD64 Linux）**：
```bash
docker-compose up -d
# 所有功能完全可用 ✅
```

**开发者（Apple Silicon）**：
```bash
# 选项 A：前端/UI 开发
docker-compose up -d backend redis
cd frontend && pnpm dev

# 选项 B：API 测试
docker-compose up -d
# 可以测试上传、下载、状态管理
# 但无法完成模型转换 ❌
```

---

## 📝 已创建的文档

1. **ARCHITECTURE_LIMITATIONS.md** - 详细的限制说明和替代方案
2. **README.md** - 更新了架构说明，明确标注限制
3. **DOCKER_QUICKSTART.md** - 保持原有快速开始指南

---

## 🔧 配置变更总结

### docker-compose.yml

**移除的内容**：
- ❌ 所有平台相关的环境变量（`ATEN_CPU_CAPABILITY` 等）
- ❌ 多余的配置文件（`docker-compose-dev.yml`）

**保留的内容**：
- ✅ 简洁的统一配置
- ✅ 健康检查
- ✅ 资源限制
- ✅ 数据卷挂载

---

## 🎯 开发者工作流

### 前端开发（推荐）

```bash
# 1. 启动后端 API（Docker）
docker-compose up -d backend redis

# 2. 本地运行前端（避开 Docker）
cd frontend
pnpm install
pnpm dev

# 3. 访问 http://localhost:8080
```

**优势**：
- ✅ 前端热重载
- ✅ 调试方便
- ✅ 避免架构问题

### API 测试

```bash
# 启动所有服务
docker-compose up -d

# 测试功能
# ✅ 文件上传
# ✅ API 响应
# ✅ 状态管理
# ❌ 模型转换（会失败）
```

### 模型转换测试

**需要在 AMD64 环境中运行**：
- 云服务器
- 虚拟机（VMware/Parallels）
- AMD64 主机

---

## 🚀 未来改进路径

### 短期（临时方案）

无需改动，接受当前限制：
- 开发者专注于前端和 API
- 用户（AMD64）测试完整功能

### 长期（根本解决）

**需要 `camthink/ne301-dev` 基础镜像支持 ARM64**：

```bash
# 由 camthink 团队执行
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t camthink/ne301-dev:latest \
  --push \
  .
```

**好处**：
- ✅ Apple Silicon 100% 原生性能
- ✅ 所有功能在开发环境可用
- ✅ 统一的开发和生产体验

---

## 📋 验证清单

- [x] 服务正常启动（所有容器 healthy）
- [x] 前端可访问（http://localhost:3000）
- [x] API 可访问（http://localhost:8000）
- [x] 文档已更新（README.md, ARCHITECTURE_LIMITATIONS.md）
- [x] 配置已简化（移除无用的环境变量）

---

## 💡 快速参考

### 当前可用功能（Apple Silicon）

✅ **可用**：
- 前端 UI 开发和调试
- API 接口开发和测试
- 文件上传/下载
- 任务状态查询
- WebSocket 连接

❌ **不可用**：
- PyTorch 模型量化（SIGILL 错误）
- 完整的端到端转换测试

### 推荐开发流程

1. **本地开发前端**：`cd frontend && pnpm dev`
2. **Docker 运行后端**：`docker-compose up -d backend redis`
3. **测试 API**：通过 Swagger (http://localhost:8000/docs)
4. **完整测试**：在 AMD64 环境（云服务器/虚拟机）

---

**实施状态**: ✅ 完成
**最后更新**: 2026-03-12
**基础镜像**: camthink/ne301-dev:latest (AMD64 only)
