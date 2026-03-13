#!/bin/bash

# Docker 测试脚本

set -e

echo "🐳 Docker 环境测试"
echo "===================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 项目根目录
PROJECT_ROOT="/Users/harryhua/Documents/GitHub/ne301/model-converter"
cd "$PROJECT_ROOT"

echo -e "${YELLOW}1. 检查 Docker 环境${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker 已安装: $(docker --version)${NC}"

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose 已安装: $(docker-compose --version)${NC}"
echo ""

echo -e "${YELLOW}2. 清理旧容器和镜像${NC}"
docker-compose down -v 2>/dev/null || true
echo -e "${GREEN}✅ 清理完成${NC}"
echo ""

echo -e "${YELLOW}3. 检查配置文件${NC}"
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ docker-compose.yml 不存在${NC}"
    exit 1
fi
echo -e "${GREEN}✅ docker-compose.yml 存在${NC}"

if [ ! -f "backend/Dockerfile" ]; then
    echo -e "${RED}❌ backend/Dockerfile 不存在${NC}"
    exit 1
fi
echo -e "${GREEN}✅ backend/Dockerfile 存在${NC}"

if [ ! -f "frontend/Dockerfile" ]; then
    echo -e "${RED}❌ frontend/Dockerfile 不存在${NC}"
    exit 1
fi
echo -e "${GREEN}✅ frontend/Dockerfile 存在${NC}"
echo ""

echo -e "${YELLOW}4. 构建后端镜像${NC}"
if docker-compose build backend; then
    echo -e "${GREEN}✅ 后端镜像构建成功${NC}"
else
    echo -e "${RED}❌ 后端镜像构建失败${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}5. 构建前端镜像${NC}"
if docker-compose build frontend; then
    echo -e "${GREEN}✅ 前端镜像构建成功${NC}"
else
    echo -e "${RED}❌ 前端镜像构建失败${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}6. 启动服务${NC}"
if docker-compose up -d; then
    echo -e "${GREEN}✅ 服务启动成功${NC}"
else
    echo -e "${RED}❌ 服务启动失败${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}7. 等待服务就绪${NC}"
sleep 10
echo ""

echo -e "${YELLOW}8. 检查服务状态${NC}"
docker-compose ps
echo ""

echo -e "${YELLOW}9. 检查后端健康状态${NC}"
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ 后端服务正常${NC}"
else
    echo -e "${RED}❌ 后端服务无响应${NC}"
fi
echo ""

echo -e "${YELLOW}10. 检查前端服务${NC}"
if curl -s http://localhost:3000 > /dev/null; then
    echo -e "${GREEN}✅ 前端服务正常${NC}"
else
    echo -e "${RED}❌ 前端服务无响应${NC}"
fi
echo ""

echo -e "${YELLOW}11. 查看服务日志${NC}"
echo "后端日志:"
docker-compose logs --tail=10 backend
echo ""
echo "前端日志:"
docker-compose logs --tail=10 frontend
echo ""

echo -e "${GREEN}✨ Docker 测试完成${NC}"
echo ""
echo "访问地址:"
echo "  前端: http://localhost:3000"
echo "  后端: http://localhost:8000"
echo "  API 文档: http://localhost:8000/docs"
echo ""
echo "停止服务:"
echo "  docker-compose down"
echo ""
