#!/bin/bash
# 智能启动脚本 - 自动选择最佳架构

set -e

echo "=== NE301 Model Converter ==="
echo ""

# 检测宿主机架构
ARCH=$(uname -m)

if [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then
    echo "🖥️  检测到 Apple Silicon Mac"
    echo ""
    echo "请选择启动模式："
    echo "  1) 统一 AMD64 (Rosetta 2) - 与生产环境完全一致，性能 ~80%"
    echo "  2) 混合架构 (推荐)      - Backend/Frontend ARM64 原生，性能 ~95%"
    echo "  3) 前端本地 + 后端Docker - 最快开发体验"
    echo ""
    read -p "请输入选择 [1-3，默认 2]: " choice
    choice=${choice:-2}

    case $choice in
        1)
            echo ""
            echo "🚀 启动统一 AMD64 模式..."
            COMPOSE_FILE="docker-compose-rosetta.yml"
            ;;
        2)
            echo ""
            echo "🚀 启动混合架构模式（推荐）..."
            COMPOSE_FILE="docker-compose-mixed.yml"
            ;;
        3)
            echo ""
            echo "🚀 启动前端本地模式..."
            COMPOSE_FILE="docker-compose-dev.yml"
            ;;
        *)
            echo "❌ 无效选择，使用默认混合架构"
            COMPOSE_FILE="docker-compose-mixed.yml"
            ;;
    esac
elif [ "$ARCH" = "x86_64" ]; then
    echo "🖥️  检测到 Intel/AMD 系统"
    echo "🚀 启动统一 AMD64 模式（原生性能）..."
    COMPOSE_FILE="docker-compose.yml"
else
    echo "⚠️  未知架构: $ARCH"
    echo "使用默认配置..."
    COMPOSE_FILE="docker-compose.yml"
fi

echo ""
echo "使用配置: $COMPOSE_FILE"
echo ""

# 检查配置文件是否存在
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ 错误: 配置文件 $COMPOSE_FILE 不存在"
    echo ""
    echo "可用配置:"
    ls -1 docker-compose*.yml 2>/dev/null || echo "  (无)"
    exit 1
fi

# 停止旧服务
echo "🛑 停止旧服务..."
docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true

# 启动新服务
echo "🚀 启动服务..."
docker-compose -f "$COMPOSE_FILE" up -d --build

echo ""
echo "✅ 服务启动完成！"
echo ""
echo "访问地址:"
echo "  前端:     http://localhost:3000"
echo "  后端 API: http://localhost:8000"
echo "  API 文档: http://localhost:8000/docs"
echo ""

# 等待服务就绪
echo "⏳ 等待服务就绪..."
sleep 5

# 验证服务状态
echo ""
echo "📊 服务状态:"
docker-compose -f "$COMPOSE_FILE" ps

echo ""
echo "🔍 验证架构:"
./verify-arch.sh 2>/dev/null || echo "  (跳过架构验证)"
