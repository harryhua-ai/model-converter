#!/bin/bash

# 停止 Model Converter 服务

set -e

echo "🛑 停止 Model Converter 服务..."

# 读取 PID
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "停止后端服务 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        echo "✅ 后端服务已停止"
    else
        echo "⚠️  后端服务已经停止"
    fi
    rm .backend.pid
fi

if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "停止前端服务 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        echo "✅ 前端服务已停止"
    else
        echo "⚠️  前端服务已经停止"
    fi
    rm .frontend.pid
fi

# 查找并停止所有相关进程
echo "🔍 查找残留进程..."
uvicorn_pids=$(pgrep -f "uvicorn app.main:app" || true)
vite_pids=$(pgrep -f "vite" || true)

if [ ! -z "$uvicorn_pids" ]; then
    echo "停止残留的 uvicorn 进程..."
    echo "$uvicorn_pids" | xargs kill 2>/dev/null || true
fi

if [ ! -z "$vite_pids" ]; then
    echo "停止残留的 vite 进程..."
    echo "$vite_pids" | xargs kill 2>/dev/null || true
fi

echo "✅ 所有服务已停止"
