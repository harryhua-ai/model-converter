# Python 环境配置指南

## 问题说明

当前系统使用 Python 3.14，但 PyTorch 等 ML 库仅支持 Python 3.11 及以下版本。

## 解决方案

### 方案 1: 使用 pyenv 安装 Python 3.11 (推荐)

#### macOS 安装

```bash
# 1. 安装 pyenv
brew install pyenv

# 2. 安装 Python 3.11
pyenv install 3.11.9

# 3. 设置本地 Python 版本
cd /Users/harryhua/Documents/GitHub/ne301/model-converter
pyenv local 3.11.9

# 4. 验证安装
python --version
# 应输出: Python 3.11.9

# 5. 重新安装依赖
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 验证安装

```bash
# 检查 Python 版本
python --version | grep "3.11"

# 检查 PyTorch 安装
python -c "import torch; print(f'PyTorch {torch.__version__}')"

# 检查 Ultralytics 安装
python -c "from ultralytics import YOLO; print('Ultralytics OK')"
```

### 方案 2: 使用 Conda (替代方案)

```bash
# 安装 Miniconda
brew install --cask miniconda

# 创建 Python 3.11 环境
conda create -n ne310 python=3.11
conda activate ne310

# 安装依赖
pip install -r requirements.txt
```

### 方案 3: 使用 Docker (推荐用于生产)

```bash
# Docker 已配置正确的 Python 版本
# 直接使用 docker-compose

cd /Users/harryhua/Documents/GitHub/ne301/model-converter
docker-compose up -d
```

## 临时解决方案：测试模式

如果暂时无法配置 Python 3.11，可以先测试不依赖 ML 库的功能：

```bash
# 仅测试 API 和 UI
# 1. 启动 FastAPI 后端 (使用系统 Python)
cd backend
python3.14 -m pip install fastapi uvicorn httpx structlog pydantic
uvicorn main:app --reload --port 8000

# 2. 启动前端 (与 Python 版本无关)
cd frontend
pnpm install
pnpm dev
```

## 推荐配置流程

### 开发环境配置

```bash
# 1. 安装 pyenv
brew install pyenv

# 2. 配置 shell
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv &> /dev/null && eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc

# 3. 安装 Python 3.11
pyenv install 3.11.9
pyenv global 3.11.9

# 4. 安装项目依赖
cd /Users/harryhua/Documents/GitHub/ne301/model-converter/backend
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Docker 部署配置

```bash
# Docker 镜像已配置 Python 3.11
# 直接使用 docker-compose

cd /Users/harryhua/Documents/GitHub/ne301/model-converter
docker-compose up -d
```

## 常见问题

### Q: pyenv 安装失败
A: 确保安装了 Homebrew: `brew install pyenv`

### Q: Python 3.11 安装失败
A: 检查网络连接，或使用 Conda 替代

### Q: 依赖安装失败
A: 某些包可能需要编译，安装 Xcode Command Line Tools:
```bash
xcode-select --install
```

### Q: 不想配置多个 Python 版本
A: 直接使用 Docker 方案，最简单

## 验证脚本

```bash
# 创建验证脚本
cat > check_python.sh << 'EOF'
#!/bin/bash
echo "检查 Python 环境..."
echo "当前 Python: $(python3 --version)"
echo "pyenv Python: $(pyenv version 2>/dev/null || echo '未安装')"
echo ""
echo "推荐使用 Python 3.11.9"
echo ""
if python3 --version | grep -q "3.11"; then
    echo "✅ Python 版本正确"
else
    echo "⚠️  当前版本: $(python3 --version)"
    echo "建议安装 Python 3.11"
fi
EOF
chmod +x check_python.sh
./check_python.sh
```

## 下一步

1. **安装 Python 3.11** (选择一个方案)
2. **重新安装依赖**
3. **启动服务测试**
4. **验证完整功能**

---

**最后更新**: 2026-03-10
