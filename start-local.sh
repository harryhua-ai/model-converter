#!/bin/bash

# Model Converter 服务启动脚本
# 使用本地虚拟环境，不依赖 Docker

set -e

echo "🚀 启动 Model Converter 服务..."

# 检查 Docker 是否运行
echo "📋 检查 Docker 状态..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker Desktop"
    echo "   macOS: 打开 Applications 文件夹中的 Docker"
    echo "   等待 Docker 启动后重新运行此脚本"
    exit 1
fi

echo "✅ Docker 正在运行"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行: python -m venv venv"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查 NE301 镜像
echo "📋 检查 NE301 Docker 镜像..."
if ! docker images | grep -q "camthink/ne301-dev"; then
    echo "⚠️  NE301 镜像不存在，正在拉取..."
    docker pull camthink/ne301-dev:latest
fi

echo "✅ NE301 镜像已就绪"

# 拉取最新的前端和后端镜像（可选）
# echo "📋 拉取最新镜像..."
# docker-compose pull

# 启动服务
echo "🚀 启动后端服务..."
cd backend

# 创建必要的目录
mkdir -p uploads outputs temp ne301 logs

# 启动后端（开发模式）
echo "✅ 启动 FastAPI 后端（开发模式）..."
echo "📍 API 地址: http://localhost:8000"
echo "📍 API 文档: http://localhost:8000/docs"
echo ""
echo "💡 提示："
echo "   - 使用 Ctrl+C 停止服务"
echo "   - 日志将输出到终端"
echo "   - 文件将保存到: backend/uploads, backend/outputs"
echo ""

# 启动服务
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
