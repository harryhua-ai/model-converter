# ⚠️ 重要限制说明

## Docker 架构兼容性

### 当前状态

**基础镜像**: `camthink/ne301-dev:latest` 仅支持 **AMD64 架构**

```
camthink/ne301-dev:latest
└── Architecture: amd64 only
```

### 影响范围

| 环境 | 架构 | 模型转换 | 其他功能 | 说明 |
|------|------|----------|----------|------|
| **Apple Silicon 开发** | AMD64 (Rosetta 2) | ❌ **不可用** | ✅ 可用 | PyTorch 量化会遇到 SIGILL 错误 |
| **AMD64 用户** | AMD64 原生 | ✅ 完全可用 | ✅ 完全可用 | 所有功能正常 |

### Apple Silicon 开发者

**可以做什么**：
- ✅ 前端开发和 UI 调试
- ✅ API 接口开发和测试
- ✅ 文件上传和下载功能
- ✅ 任务状态管理

**不能做什么**：
- ❌ 模型转换（PyTorch 量化会崩溃）
- ❌ 完整的端到端测试

### 替代方案

#### 方案 1：在 AMD64 环境测试

```bash
# 在 AMD64 Linux 服务器或虚拟机中运行
docker-compose up -d
```

#### 方案 2：使用预转换的模型

跳过量化步骤，直接使用已转换好的模型进行后续测试：
```bash
# 将预转换的模型放到 outputs 目录
cp pretrained_model.bin ./outputs/
```

#### 方案 3：前端本地开发

```bash
# 后端在 Docker 中运行（仅用于 API 测试）
docker-compose up -d backend redis

# 前端本地运行（避开 Docker）
cd frontend
pnpm install
pnpm dev
```

---

## 未来改进

### 根本解决方案

需要 `camthink/ne301-dev` 基础镜像支持 **ARM64 架构**：

```bash
# 由 camthink 团队执行
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t camthink/ne301-dev:latest \
  --push \
  .
```

**好处**：
- ✅ Apple Silicon 开发者获得 100% 原生性能
- ✅ 所有功能在开发环境可用
- ✅ 统一的开发和生产环境

---

## 快速参考

### 用户（AMD64 Linux）

```bash
cd model-converter
docker-compose up -d
```

### 开发者（Apple Silicon）

**选项 A：开发前端/UI**
```bash
# 仅启动后端 API（用于开发）
docker-compose up -d backend redis

# 本地运行前端
cd frontend && pnpm dev
```

**选项 B：测试模型转换**
```bash
# 需要在 AMD64 环境中运行
# 例如：云服务器、虚拟机、或 AMD64 主机
docker-compose up -d
```

---

**最后更新**: 2026-03-12
**状态**: 限制已知，等待基础镜像支持 ARM64
