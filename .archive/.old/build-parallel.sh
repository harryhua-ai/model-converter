#!/bin/bash
set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 创建日志目录
mkdir -p logs

# 清理旧日志
rm -f logs/build-*.log

# 并行构建函数
build_service() {
  local service=$1
  local log_file="logs/build-${service}.log"

  echo -e "${YELLOW}[$(date '+%H:%M:%S')]${NC} 开始构建 ${service}..."

  if docker-compose build "${service}" > "${log_file}" 2>&1; then
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} ✅ ${service} 构建成功"
    return 0
  else
    echo -e "${RED}[$(date '+%H:%M:%S')]${NC} ❌ ${service} 构建失败"
    echo -e "${RED}查看日志: ${log_file}${NC}"
    return 1
  fi
}

# 单个服务构建（用于重试）
build_single() {
  local service=$1
  if [ -z "$service" ]; then
    echo "用法: $0 <service>"
    echo "可用的服务: frontend, backend"
    exit 1
  fi

  mkdir -p logs
  local log_file="logs/build-${service}.log"

  echo -e "${YELLOW}[$(date '+%H:%M:%S')]${NC} 重新构建 ${service}..."
  echo -e "${YELLOW}[$(date '+%H:%M:%S')]${NC} 日志文件: ${log_file}"
  echo ""

  if docker-compose build "${service}" 2>&1 | tee "${log_file}"; then
    echo ""
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} ✅ ${service} 构建成功"
    docker images | grep "ne301-model-converter-${service}"

    # 如果是 backend，也标记 celery
    if [ "$service" = "backend" ]; then
      echo ""
      echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} ✅ 标记 Celery Worker 镜像..."
      docker tag ne301-model-converter-backend:v2 ne301-model-converter-celery:v2
      echo -e "${GREEN}✅ Celery Worker (复用 Backend 镜像)${NC}"
    fi

    exit 0
  else
    echo ""
    echo -e "${RED}[$(date '+%H:%M:%S')]${NC} ❌ ${service} 构建失败"
    echo -e "${RED}查看日志: ${log_file}${NC}"
    exit 1
  fi
}

# 如果传入了服务名参数，仅构建该服务
if [ -n "$1" ]; then
  build_single "$1"
fi

# 并行构建独立服务
echo "=== 开始并行构建 ==="
echo "正在构建: frontend, backend (独立并行)"
echo ""

# 使用后台任务并行构建
build_service frontend &
PID_FRONTEND=$!

build_service backend &
PID_BACKEND=$!

# 等待所有构建完成
wait $PID_FRONTEND || FRONTEND_FAILED=true
wait $PID_BACKEND || BACKEND_FAILED=true

# 检查结果
echo ""
echo "=== 构建结果 ==="

if [ -z "$FRONTEND_FAILED" ]; then
  echo -e "${GREEN}✅ Frontend 构建成功${NC}"
  docker images | grep ne301-model-converter-frontend
else
  echo -e "${RED}❌ Frontend 构建失败${NC}"
  echo "查看日志: logs/build-frontend.log"
fi

echo ""

if [ -z "$BACKEND_FAILED" ]; then
  echo -e "${GREEN}✅ Backend 构建成功${NC}"
  docker images | grep ne301-model-converter-backend
else
  echo -e "${RED}❌ Backend 构建失败${NC}"
  echo "查看日志: logs/build-backend.log"
fi

# 如果 backend 成功，标记 celery-worker 也成功（共享镜像）
if [ -z "$BACKEND_FAILED" ]; then
  echo ""
  echo -e "${GREEN}✅ Celery Worker (复用 Backend 镜像)${NC}"
  docker tag ne301-model-converter-backend:v2 ne301-model-converter-celery:v2
  docker images | grep ne301-model-converter-celery || echo "  (镜像已标记)"
fi

# 最终总结
echo ""
echo "=== 构建总结 ==="
if [ -z "$FRONTEND_FAILED" ] && [ -z "$BACKEND_FAILED" ]; then
  echo -e "${GREEN}🎉 所有服务构建成功！${NC}"
  echo ""
  echo "下一步："
  echo "  验证构建: ./verify-build.sh"
  echo "  启动服务: make docker-up"
  exit 0
else
  echo -e "${RED}⚠️  部分服务构建失败${NC}"
  echo ""
  echo "重新构建失败的服务的命令："
  [ -n "$FRONTEND_FAILED" ] && echo "  ./build-parallel.sh frontend"
  [ -n "$BACKEND_FAILED" ] && echo "  ./build-parallel.sh backend"
  echo ""
  echo "或使用 Makefile："
  [ -n "$FRONTEND_FAILED" ] && echo "  make build-frontend"
  [ -n "$BACKEND_FAILED" ] && echo "  make build-backend"
  exit 1
fi
