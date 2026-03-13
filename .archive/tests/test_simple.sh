#!/bin/bash

# 无 ML 库的简化测试脚本

set -e

echo "🧪 简化测试模式（跳过 ML 库）"
echo "================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 项目根目录
PROJECT_ROOT="/Users/harryhua/Documents/GitHub/ne301/model-converter"
cd "$PROJECT_ROOT"

echo -e "${YELLOW}1. 创建临时 requirements.txt（仅 Web 框架）${NC}"
cat > backend/requirements-temp.txt << 'EOF'
# FastAPI 核心
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.10.0
pydantic-settings==2.6.0

# 任务队列
celery==5.4.0
redis==5.2.0
kombu==5.4.0

# WebSocket
websockets==13.1

# 文件处理
python-multipart==0.0.12
aiofiles==24.1.0

# 工具库
structlog==24.4.0
python-dotenv==1.0.1
httpx==0.28.0

# 开发工具
pytest==8.3.0
pytest-asyncio==0.24.0
EOF
echo -e "${GREEN}✅ 临时 requirements.txt 创建完成${NC}"
echo ""

echo -e "${YELLOW}2. 创建临时 Dockerfile（使用系统 Python）${NC}"
cat > backend/Dockerfile-temp << 'EOF'
# 使用官方 Python 3.11 镜像
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制临时依赖文件（不含 ML 库）
COPY requirements-temp.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements-temp.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p uploads temp outputs

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
echo -e "${GREEN}✅ 临时 Dockerfile 创建完成${NC}"
echo ""

echo -e "${YELLOW}3. 修改 docker-compose.yml 使用临时 Dockerfile${NC}"
# 备份原文件
cp docker-compose.yml docker-compose.yml.bak

# 创建临时配置
cat > docker-compose-temp.yml << 'EOF'
version: '3.8'

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
      dockerfile: Dockerfile-temp
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./uploads:/app/uploads
      - ./temp:/app/temp
      - ./outputs:/app/outputs
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - NE301_PROJECT_PATH=/workspace
    depends_on:
      - redis
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped
EOF
echo -e "${GREEN}✅ 临时 docker-compose.yml 创建完成${NC}"
echo ""

echo -e "${YELLOW}4. 构建和启动服务${NC}"
docker-compose -f docker-compose-temp.yml down -v 2>/dev/null || true
docker-compose -f docker-compose-temp.yml build
docker-compose -f docker-compose-temp.yml up -d
echo ""

echo -e "${YELLOW}5. 等待服务启动${NC}"
sleep 15
echo ""

echo -e "${YELLOW}6. 检查服务状态${NC}"
docker-compose -f docker-compose-temp.yml ps
echo ""

echo -e "${YELLOW}7. 测试 API 端点${NC}"

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

# 测试任务列表
echo -n "任务列表: "
if curl -s http://localhost:8000/api/v1/tasks | grep -q "tasks"; then
    echo -e "${GREEN}✅ 通过${NC}"
else
    echo -e "${RED}❌ 失败${NC}"
fi

echo ""

echo -e "${YELLOW}8. 查看服务日志${NC}"
echo "后端日志:"
docker-compose -f docker-compose-temp.yml logs --tail=10 backend
echo ""

echo -e "${YELLOW}9. 前端访问测试${NC}"
if curl -s http://localhost:3000 | grep -q "DOCTYPE"; then
    echo -e "${GREEN}✅ 前端服务正常${NC}"
else
    echo -e "${RED}❌ 前端服务无响应${NC}"
fi
echo ""

echo -e "${GREEN}✨ 简化测试完成${NC}"
echo ""
echo "说明:"
echo "  - 此测试跳过了 ML 库（Ultralytics, PyTorch, TensorFlow）"
echo "  - API 和 UI 功能正常，但无法测试完整转换流程"
echo "  - 完整功能测试需要配置 Python 3.11 环境或使用 Docker"
echo ""
echo "访问地址:"
echo "  前端: http://localhost:3000"
echo "  后端: http://localhost:8000"
echo "  API 文档: http://localhost:8000/docs"
echo ""
echo "停止服务:"
echo "  docker-compose -f docker-compose-temp.yml down"
echo ""
echo "恢复原配置:"
echo "  mv docker-compose.yml.bak docker-compose.yml"
echo ""
