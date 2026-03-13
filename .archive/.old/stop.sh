#!/bin/bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "停止 NE301 模型转换工具..."
echo ""

# 进入脚本所在目录
cd "$(dirname "$0")"

# 读取 PID
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID 2>/dev/null && echo -e "${GREEN}✓${NC} 后端已停止 (PID: $BACKEND_PID)"
    else
        echo -e "${YELLOW}⚠${NC} 后端进程不存在 (PID: $BACKEND_PID)"
    fi
    rm -f .backend.pid
fi

if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID 2>/dev/null && echo -e "${GREEN}✓${NC} 前端已停止 (PID: $FRONTEND_PID)"
    else
        echo -e "${YELLOW}⚠${NC} 前端进程不存在 (PID: $FRONTEND_PID)"
    fi
    rm -f .frontend.pid
fi

# 清理可能的残留进程
pkill -f "backend/main.py" 2>/dev/null
pkill -f "vite.*frontend" 2>/dev/null

echo ""
echo -e "${GREEN}服务已停止${NC}"
