#!/bin/bash

# Docker 快速部署脚本

set -e

echo "🐳 Docker 部署脚本"
echo "=================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_ROOT="/Users/harryhua/Documents/GitHub/ne301/model-converter"
cd "$PROJECT_ROOT"

echo -e "${YELLOW}1. 清理旧容器${NC}"
docker-compose down -v 2>/dev/null || true
docker system prune -f
echo -e "${GREEN}✅ 清理完成${NC}"
echo ""

echo -e "${YELLOW}2. 仅启动后端和 Redis${NC}"
echo "创建简化配置..."

# 创建简化配置（仅启动后端和Redis，前端本地运行）
cat > docker-compose-dev.yml << 'EOF'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./uploads:/app/uploads
      - ./temp:/app/temp
      - ./outputs:/app/outputs
      - ../Model:/workspace/Model
      - ../Script:/workspace/Script
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - NE301_PROJECT_PATH=/workspace
    depends_on:
      - redis
    restart: unless-stopped
EOF

echo -e "${GREEN}✅ 配置创建完成${NC}"
echo ""

echo -e "${YELLOW}3. 构建 Docker 镜像${NC}"
if docker-compose -f docker-compose-dev.yml build backend; then
    echo -e "${GREEN}✅ 后端镜像构建成功${NC}"
else
    echo -e "${RED}❌ 后端镜像构建失败${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}4. 启动服务${NC}"
if docker-compose -f docker-compose-dev.yml up -d; then
    echo -e "${GREEN}✅ 服务启动成功${NC}"
else
    echo -e "${RED}❌ 服务启动失败${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}5. 等待服务就绪${NC}"
sleep 10
echo ""

echo -e "${YELLOW}6. 检查服务状态${NC}"
docker-compose -f docker-compose-dev.yml ps
echo ""

echo -e "${YELLOW}7. 测试 API 端点${NC}"

# 测试根路径
echo -n "根路径: "
if curl -s http://localhost:8000/ | head -1; then
    echo -e " ${GREEN}✅${NC}"
else
    echo -e " ${RED}❌${NC}"
fi

# 测试健康检查
echo -n "健康检查: "
if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo -e "${GREEN}✅ 通过${NC}"
else
    echo -e "${RED}❌ 失败${NC}"
fi

# 测试预设端点
echo -n "预设列表: "
if curl -s http://localhost:8000/api/v1/presets | grep -q "yolov8n-256"; then
    echo -e "${GREEN}✅ 通过${NC}"
else
    echo -e "${RED}❌ 失败${NC}"
fi

# 测试任务端点
echo -n "任务列表: "
if curl -s http://localhost:8000/api/v1/tasks | grep -q "tasks"; then
    echo -e "${GREEN}✅ 通过${NC}"
else
    echo -e "${RED}❌ 失败${NC}"
fi

echo ""

echo -e "${YELLOW}8. 查看服务日志${NC}"
docker-compose -f docker-compose-dev.yml logs --tail=15 backend
echo ""

echo -e "${GREEN}✨ Docker 部署完成${NC}"
echo ""
echo "服务访问:"
echo "  后端 API: http://localhost:8000"
echo "  API 文档: http://localhost:8000/docs"
echo "  Redis: localhost:6379"
echo ""
echo "前端启动（本地）:"
echo "  cd frontend"
echo "  pnpm install"
echo "  pnpm dev"
echo ""
echo "停止服务:"
echo "  docker-compose -f docker-compose-dev.yml down"
echo ""
