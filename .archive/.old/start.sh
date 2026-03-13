#!/bin/bash
set -e

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}  NE301 模型转换工具${NC}"
echo -e "${GREEN}====================================${NC}"
echo ""

# 进入脚本所在目录
cd "$(dirname "$0")"

# 环境检查
echo -e "${BLUE}[检查]${NC} 检查环境依赖..."

# Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: Python 3 未安装${NC}"
    exit 1
fi
echo -e "  ✓ Python: $(python3 --version)"

# Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}错误: Node.js 未安装${NC}"
    exit 1
fi
echo -e "  ✓ Node.js: $(node --version)"

# pnpm
if ! command -v pnpm &> /dev/null; then
    echo -e "${YELLOW}警告: pnpm 未安装，将使用 npm${NC}"
    NPM_CMD="npm"
else
    echo -e "  ✓ pnpm: $(pnpm --version)"
    NPM_CMD="pnpm"
fi

# ST Edge AI
if [ -z "$STEDGEAI_CORE_DIR" ] && [ -z "$STEDGEAI_PATH" ]; then
    echo -e "${YELLOW}  ⚠ 警告: STEDGEAI_CORE_DIR/STEDGEAI_PATH 未设置${NC}"
    echo -e "${YELLOW}    转换功能可能受限，请在 ~/.zshrc 或 ~/.bashrc 中设置：${NC}"
    echo -e "${YELLOW}    export STEDGEAI_PATH=/opt/stedgeai${NC}"
else
    if [ -n "$STEDGEAI_PATH" ]; then
        echo -e "  ✓ ST Edge AI: $STEDGEAI_PATH"
    else
        echo -e "  ✓ ST Edge AI: $STEDGEAI_CORE_DIR"
    fi
fi

# 设置环境变量
export NE301_PROJECT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo -e "  ✓ NE301 项目: $NE301_PROJECT_PATH"

# 安装后端依赖
echo ""
echo -e "${BLUE}[安装]${NC} 检查后端依赖..."
if [ ! -d "backend/venv" ]; then
    echo "  创建虚拟环境..."
    python3 -m venv backend/venv
fi

echo "  激活虚拟环境..."
source backend/venv/bin/activate

echo "  检查/安装依赖..."
if ! backend/venv/bin/pip show fastapi &> /dev/null; then
    echo "  安装 Python 依赖..."
    pip install -q -r backend/requirements.txt
else
    echo "  ✓ Python 依赖已安装"
fi

# 安装前端依赖
echo ""
echo -e "${BLUE}[安装]${NC} 检查前端依赖..."
if [ ! -d "frontend/node_modules" ]; then
    echo "  安装前端依赖..."
    cd frontend
    $NPM_CMD install
    cd ..
else
    echo "  ✓ 前端依赖已安装"
fi

# 创建必要的目录
mkdir -p uploads temp outputs

# 检查端口占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

if check_port 8000; then
    echo -e "${YELLOW}警告: 端口 8000 已被占用${NC}"
    echo "  请先停止其他服务或修改端口配置"
fi

# 启动后端
echo ""
echo -e "${BLUE}[启动]${NC} 启动后端服务..."
source backend/venv/bin/activate
cd backend
python3 main.py &
BACKEND_PID=$!
cd ..
echo "  后端 PID: $BACKEND_PID"

# 等待后端就绪
echo "  等待后端启动..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo "  ✓ 后端已就绪"
        break
    fi
    sleep 1
done

# 启动前端
echo ""
echo -e "${BLUE}[启动]${NC} 启动前端服务..."
cd frontend
$NPM_CMD dev &
FRONTEND_PID=$!
cd ..
echo "  前端 PID: $FRONTEND_PID"

# 保存 PID
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

echo ""
echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}  ✓ 服务启动成功！${NC}"
echo -e "${GREEN}====================================${NC}"
echo ""
echo -e "  ${BLUE}Web 界面:${NC}  http://localhost:3000"
echo -e "  ${BLUE}API 文档:${NC}  http://localhost:8000/docs"
echo ""
echo "  按 Ctrl+C 停止服务，或运行:"
echo "    ./stop.sh"
echo ""
echo "  日志文件:"
echo "    后端: tail -f backend/logs/app.log"
echo "    前端: 查看终端输出"
echo ""

# 等待用户中断
cleanup() {
    echo ""
    echo -e "${YELLOW}停止服务...${NC}"

    if [ -f .frontend.pid ]; then
        FRONTEND_PID=$(cat .frontend.pid)
        kill $FRONTEND_PID 2>/dev/null && echo "  ✓ 前端已停止 (PID: $FRONTEND_PID)"
        rm -f .frontend.pid
    fi

    if [ -f .backend.pid ]; then
        BACKEND_PID=$(cat .backend.pid)
        kill $BACKEND_PID 2>/dev/null && echo "  ✓ 后端已停止 (PID: $BACKEND_PID)"
        rm -f .backend.pid
    fi

    echo -e "${GREEN}服务已停止${NC}"
    exit 0
}

trap cleanup INT TERM

wait
