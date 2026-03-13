#!/bin/bash
# 一键部署脚本

set -e

echo "================================"
echo "Model Converter - 容器化部署"
echo "================================"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

echo "✅ Docker 环境检查通过"

# 拉取 NE301 镜像
echo "📦 拉取 NE301 Docker 镜像..."
docker pull camthink/ne301-dev:latest

# 构建镜像
echo "🔨 构建 API 容器镜像..."
docker-compose build

# 初始化 NE301 项目
echo "🔧 初始化 NE301 项目..."
chmod +x scripts/init-ne301.sh
./scripts/init-ne301.sh

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 健康检查
echo "🔍 健康检查..."
if curl -f http://localhost:8000/health &> /dev/null; then
    echo "✅ 服务启动成功!"
    echo ""
    echo "📝 API 地址: http://localhost:8000"
    echo "📖 API 文档: http://localhost:8000/docs"
    echo ""
    echo "查看日志: docker-compose logs -f"
    echo "停止服务: docker-compose down"
else
    echo "❌ 服务启动失败，请检查日志:"
    echo "docker-compose logs"
    exit 1
fi
