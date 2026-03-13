#!/bin/bash
# 切换到 ARM64 原生镜像

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== 切换到 ARM64 原生镜像 ===${NC}"
echo ""

# 检查 ARM64 镜像是否存在
if ! docker images | grep -q "ne301-backend-arm64.*latest"; then
    echo -e "${YELLOW}ARM64 镜像不存在，请先运行:${NC}"
    echo "  ./build-arm64.sh"
    exit 1
fi

# 备份原配置
cp docker-compose.yml docker-compose.yml.backup-$(date +%Y%m%d-%H%M%S)

# 修改 docker-compose.yml
echo -e "${GREEN}修改 docker-compose.yml...${NC}"

# 使用 sed 替换 backend 镜像
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' 's|image: ne301-model-converter-backend:v2|image: ne301-backend-arm64:latest|g' docker-compose.yml
else
    # Linux
    sed -i 's|image: ne301-model-converter-backend:v2|image: ne301-backend-arm64:latest|g' docker-compose.yml
fi

echo -e "${GREEN}✅ 配置已更新${NC}"
echo ""
echo -e "${YELLOW}下一步:${NC}"
echo "1. 停止当前服务: docker-compose down"
echo "2. 启动新服务: docker-compose up -d"
echo "3. 查看日志: docker-compose logs -f backend"
echo ""
echo "如需回滚:"
echo "  cp docker-compose.yml.backup-* docker-compose.yml"
