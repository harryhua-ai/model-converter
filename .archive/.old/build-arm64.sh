#!/bin/bash
# ARM64 原生镜像构建脚本
# 专为 Apple Silicon 优化，消除模拟性能开销

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== ARM64 原生镜像构建 ===${NC}"
echo ""

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}错误: Docker 未运行${NC}"
    echo "请先启动 Docker Desktop"
    exit 1
fi

# 检查架构
ARCH=$(uname -m)
if [ "$ARCH" != "arm64" ] && [ "$ARCH" != "aarch64" ]; then
    echo -e "${YELLOW}警告: 当前架构是 $ARCH，不是 ARM64${NC}"
    echo "这个 Dockerfile 是为 ARM64 优化的"
    read -p "是否继续? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 进入 backend 目录
cd "$(dirname "$0")/backend"

echo -e "${GREEN}步骤 1/4: 清理旧镜像${NC}"
docker images | grep ne301-backend-arm64 && \
    docker rmi ne301-backend-arm64:latest 2>/dev/null || true

echo -e "${GREEN}步骤 2/4: 构建 ARM64 原生镜像${NC}"
echo "这可能需要 10-15 分钟..."

docker build \
  --platform linux/arm64 \
  -f Dockerfile.arm64 \
  -t ne301-backend-arm64:latest \
  . 2>&1 | tee /tmp/arm64-build.log

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ ARM64 镜像构建成功！${NC}"
    echo ""
    echo "镜像信息:"
    docker images | grep ne301-backend-arm64
    echo ""
    echo -e "${YELLOW}下一步:${NC}"
    echo "1. 停止当前服务: docker-compose down"
    echo "2. 修改 docker-compose.yml 使用新镜像"
    echo "3. 启动服务: docker-compose up -d"
else
    echo -e "${RED}❌ 构建失败${NC}"
    echo "查看日志: cat /tmp/arm64-build.log"
    exit 1
fi

echo ""
echo -e "${GREEN}=== 验证镜像架构 ===${NC}"
docker image inspect ne301-backend-arm64:latest | grep '"Architecture"'
echo ""
echo "预期输出: \"arm64\""
