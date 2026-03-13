#!/bin/bash

# Model Converter 完整启动脚本（前后端）
# 同时启动前端和后端服务

set -e

echo "🚀 启动 Model Converter 完整服务..."
echo ""

# 检查 Docker 是否运行
echo "📋 检查 Docker 状态..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker Desktop"
    exit 1
fi
echo "✅ Docker 正在运行"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行: python3 -m venv venv"
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
echo ""

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p backend/uploads backend/outputs backend/temp backend/ne301 backend/logs

# 启动后端服务（后台）
echo "🔧 启动后端服务（后台）..."
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..
echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 3

# 检查后端是否成功启动
if ! curl -s http://localhost:8000/api/health > /dev/null; then
    echo "❌ 后端服务启动失败，请检查日志: logs/backend.log"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo "✅ 后端服务启动成功"
echo ""

# 启动前端开发服务器（后台）
echo "🎨 启动前端开发服务器..."
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "✅ 前端服务已启动 (PID: $FRONTEND_PID)"

# 等待前端启动
echo "⏳ 等待前端服务启动..."
sleep 5

echo ""
echo "=================================================="
echo "🎉 服务启动成功！"
echo "=================================================="
echo ""
echo "📍 访问地址:"
echo "   前端: http://localhost:5173"
echo "   后端: http://localhost:8000"
echo "   API 文档: http://localhost:8000/docs"
echo "   健康检查: http://localhost:8000/api/health"
echo ""
echo "📋 日志位置:"
echo "   后端日志: logs/backend.log"
echo "   前端日志: logs/frontend.log"
echo ""
echo "🛑 停止服务:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   或运行: ./stop-services.sh"
echo ""
echo "💡 提示:"
echo "   - 使用 'tail -f logs/backend.log' 查看后端日志"
echo "   - 使用 'tail -f logs/frontend.log' 查看前端日志"
echo "   - 文件上传位置: backend/uploads/"
echo "   - 文件输出位置: backend/outputs/"
echo ""
echo "=================================================="

# 保存 PID 到文件，方便后续停止
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

echo "✅ PID 已保存到 .backend.pid 和 .frontend.pid"
