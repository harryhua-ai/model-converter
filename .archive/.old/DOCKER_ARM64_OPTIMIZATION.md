# Docker 虚拟化性能优化指南

## 问题根源

当前使用的基础镜像 `camthink/ne301-dev:latest` 是 **x86_64 架构**，在 ARM64 Mac (M1/M2/M3/M4) 上运行需要模拟。

**性能对比**：
- 原生 x86_64: ~2-3 分钟
- ARM64 + QEMU: ~20-30 分钟
- ARM64 + Rosetta: ~10-15 分钟
- **ARM64 原生: ~2-3 分钟** ⭐

---

## 立即可行的优化

### 1. 使用 Apple Virtualization Framework (VZ)

**步骤**：

1. 打开 Docker Desktop
2. 进入 **Settings** → **General**
3. 在 **Virtualization backend** 部分：
   ```
   选择: Use Apple Virtualization Framework
   ```
4. 确保 **Use Rosetta for x86_64/amd64 emulation on Apple Silicon** 已勾选
5. 点击 **Apply & Restart**

**效果**：相比纯 QEMU 模拟，性能提升约 2-3x。

---

### 2. 启用 Rosetta 加速（已启用）

您已经启用了这个选项，这是正确的配置。

**验证 Rosetta 是否生效**：
```bash
# 在容器内检查
docker exec model-converter-backend-1 uname -m
# 输出: x86_64（说明正在使用 Rosetta）

# 检查是否使用 VZ 后端
docker exec model-converter-backend-1 sysctl -n machdep.cpu.brand_string
```

---

### 3. 限制 Docker 资源（反直觉但有效）

**为什么**：模拟器在资源受限时反而更高效（减少上下文切换）

**步骤**：
1. Docker Desktop → **Settings** → **Resources** → **Advanced**
2. 设置：
   ```
   CPUs: 4 cores（而不是全部）
   Memory: 4 GB（而不是 8GB+）
   ```
3. 点击 **Apply & Restart**

---

## 🚀 最佳解决方案：构建 ARM64 原生镜像

### 方案 A：使用多架构构建（推荐）

**目标**：同时支持 x86_64 和 ARM64，消除模拟开销。

**修改 Dockerfile**：

```dockerfile
# 多架构支持
FROM --platform=$BUILDPLATFORM ubuntu:22.04 AS base

# 安装基础依赖
RUN apt-get update && apt-get install -y \
    python3.11 python3.11-dev python3.11-distutils \
    python3-pip wget curl git \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 安装 PyTorch（根据架构自动选择）
RUN python3 -m pip install --no-cache-dir pip torch torchvision

# 安装 Ultralytics 和其他依赖
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# 如果是 ARM64，下载 ARM 版本的 ST Edge AI
ARG TARGETPLATFORM
RUN if [ "$TARGETPLATFORM" = "linux/arm64" ]; then \
       echo "安装 ARM64 版本的 ST Edge AI..."; \
       # 下载并安装 ARM64 版本
       wget -q https://example.com/stedgeai-arm64.tar.gz -O /tmp/stedgeai.tar.gz \
       && tar -xzf /tmp/stedgeai.tar.gz -C /opt/; \
    else \
       echo "使用 x86_64 版本的 ST Edge AI（从基础镜像）"; \
    fi

WORKDIR /app
COPY . .

RUN mkdir -p uploads temp outputs

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**构建命令**：
```bash
# 使用 buildx 构建多架构镜像
docker buildx create --use
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ne301-backend:multi \
  --push \
  .
```

---

### 方案 B：纯 ARM64 构建（最简单）

**修改 Dockerfile**：

```dockerfile
# 明确指定 ARM64 平台
FROM --platform=linux/arm64 ubuntu:22.04

# 安装 Python 3.11
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.11 python3.11-dev python3.11-distutils python3-pip \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    curl wget git \
    && rm -rf /var/lib/apt/lists/* \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# 安装 PyTorch（ARM64 版本）
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir \
    torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cpu

# 安装项目依赖
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY . .
RUN mkdir -p uploads temp outputs

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**构建和运行**：
```bash
# 构建 ARM64 镜像
docker build --platform linux/arm64 -t ne301-backend:arm64 .

# 修改 docker-compose.yml
services:
  backend:
    image: ne301-backend:arm64
    # ... 其他配置

# 启动
docker-compose up -d --build backend
```

**预期效果**：转换时间从 20-30 分钟降至 **2-3 分钟**！ 🚀

---

### 方案 C：本地运行（最快，绕过 Docker）

**步骤**：

1. **安装本地 Python 环境**：
```bash
# 使用 pyenv 安装 Python 3.11
brew install pyenv
pyenv install 3.11
pyenv global 3.11

# 或使用 conda
conda create -n ne301 python=3.11
conda activate ne301
```

2. **安装依赖**：
```bash
cd backend
pip install -r requirements.txt

# 如果是 ARM64 Mac，安装 ARM 版本的 PyTorch
pip install torch torchvision torchaudio
```

3. **配置环境变量**：
```bash
cp .env.example .env
# 编辑 .env，设置 NE301_PROJECT_PATH=/path/to/ne301
```

4. **启动服务**：
```bash
python3 main.py
# 或
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

5. **修改 docker-compose.yml**（仅启动 Redis 和 Frontend）：
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      backend:  # 指向本地服务
        condition: service_started
    environment:
      - API_URL=http://host.docker.internal:8000

  # backend 服务注释掉，在本地运行
```

**预期效果**：转换时间 **1-2 分钟**（最快）。

---

## 📊 性能对比总结

| 方案 | 平台 | 转换时间 | 设置难度 | 备注 |
|------|------|---------|---------|------|
| 当前（QEMU） | x86_64 模拟 | 20-30 分钟 | ⭐ | 太慢！ |
| Rosetta + VZ | x86_64 模拟 | 10-15 分钟 | ⭐ | **立即可用** |
| ARM64 原生镜像 | ARM64 原生 | 2-3 分钟 | ⭐⭐⭐ | **推荐** |
| 本地运行 | ARM64 原生 | 1-2 分钟 | ⭐⭐ | 最快 |

---

## 🔧 实施步骤

### 步骤 1：立即优化（5 分钟）

1. 确认 Docker Desktop 设置：
   - ✅ 使用 Apple Virtualization Framework
   - ✅ 启用 Rosetta
   - 限制资源：4 CPU, 4GB RAM

2. 重启 Docker：
```bash
docker-compose down
docker-compose up -d
```

3. 重启转换任务（如果还在运行很慢）。

---

### 步骤 2：构建 ARM64 镜像（30 分钟）

创建新的 Dockerfile（见方案 B）：
```bash
cd backend
# 创建 Dockerfile.arm64
# ...（复制上面的 ARM64 Dockerfile）

# 构建
docker build --platform linux/arm64 -f Dockerfile.arm64 -t ne301-backend:arm64 .

# 测试
docker run --rm -p 8000:8000 ne301-backend:arm64
```

---

### 步骤 3：本地开发环境（1 小时）

如果需要频繁开发和测试，建议设置本地环境（方案 C）。

---

## 🎯 推荐策略

**对于开发和测试**：
- 使用 **本地运行（方案 C）**，最快最灵活

**对于生产部署**：
- 构建 **ARM64 原生镜像（方案 B）**
- 或使用 **多架构镜像（方案 A）**，支持跨平台

**临时快速优化**：
- 启用 **VZ + Rosetta**，性能提升 2-3x

---

## 📝 注意事项

1. **ST Edge AI 工具链**：
   - 官方可能没有 ARM64 版本
   - 如果需要，可能需要从源码编译
   - 或者仅在 x86_64 环境中使用 ST Edge AI 部分

2. **PyTorch ARM64 版本**：
   - PyTorch 从 2.0 版本开始原生支持 ARM64
   - 使用官方 pip 安装即可
   - 不要使用 conda（可能有问题）

3. **模型兼容性**：
   - PyTorch → TFLite 转换在 ARM64 上完全兼容
   - 生成的 .bin 文件与平台无关

---

## 🔍 验证 ARM64 性能

构建 ARM64 镜像后，验证是否使用了原生架构：

```bash
# 检查镜像架构
docker image inspect ne301-backend:arm64 | grep Architecture

# 应该输出:
# "Architecture": "arm64"

# 在容器内验证
docker run --rm ne301-backend:arm64 uname -m
# 应该输出: aarch64

# 测试 PyTorch 是否正常工作
docker run --rm ne301-backend:arm64 python3 -c "import torch; print(torch.__version__, torch.get_default_device())"
```

---

**最后更新**: 2026-03-12
**相关文档**:
- [Docker Desktop Apple Silicon Guide](https://docs.docker.com/desktop/install/mac-install/)
- [Apple Virtualization Framework](https://developer.apple.com/documentation/virtualization)
- [PyTorch ARM64 Installation](https://pytorch.org/get-started/locally/)
