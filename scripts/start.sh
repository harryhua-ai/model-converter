#!/bin/bash
# NE301 Model Converter 启动脚本
# 支持 Linux 和 macOS

set -e  # 遇到错误立即退出

echo "🚀 Starting NE301 Model Converter..."
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    echo "   Visit: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✅ Found Python $PYTHON_VERSION"

# 检查 Node.js
if ! command -v npm &> /dev/null; then
    echo "❌ Node.js/npm not found. Please install Node.js 18+"
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version)
NPM_VERSION=$(npm --version)
echo "✅ Found Node $NODE_VERSION, npm $NPM_VERSION"
echo ""

# 安装后端依赖
echo "📦 Installing backend dependencies..."
cd "$(dirname "$0")/backend"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Backend dependencies installed"
else
    echo "⚠️  Warning: requirements.txt not found"
fi
echo ""

# 构建前端
echo "🔨 Building frontend..."
cd "$(dirname "$0")/frontend"
if [ -f "package.json" ]; then
    npm install
    npm run build
    echo "✅ Frontend built successfully"
else
    echo "⚠️  Warning: package.json not found"
fi
echo ""

# 启动服务器
echo "✅ Starting server..."
echo "🌐 Open http://localhost:8000 in your browser"
echo "📝 Press Ctrl+C to stop the server"
echo ""

cd "$(dirname "$0")/backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
