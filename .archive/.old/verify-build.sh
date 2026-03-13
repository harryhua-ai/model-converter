#!/bin/bash

echo "=== Docker 构建验证 ==="
echo ""

# 检查镜像是否存在
check_image() {
  local image=$1
  local expected_tag=$2

  if docker images | grep -q "^${image}.*${expected_tag}"; then
    local size=$(docker images "${image}:${expected_tag}" --format "{{.Size}}")
    echo -e "✅ ${image}:${expected_tag} - ${size}"
    return 0
  else
    echo -e "❌ ${image}:${expected_tag} - 未找到"
    return 1
  fi
}

# 验证所有必需镜像
echo "检查镜像："
check_image "ne301-model-converter-frontend" "v2" || FRONTEND_MISSING=true
check_image "ne301-model-converter-backend" "v2" || BACKEND_MISSING=true

# Celery Worker 复用 Backend 镜像
if [ -z "$BACKEND_MISSING" ]; then
  if docker images | grep -q "ne301-model-converter-celery.*v2"; then
    echo -e "✅ ne301-model-converter-celery:v2 (复用 Backend)"
  else
    echo -e "⚠️  ne301-model-converter-celery:v2 - 需要标记"
    docker tag ne301-model-converter-backend:v2 ne301-model-converter-celery:v2
    echo -e "✅ 已标记: ne301-model-converter-celery:v2"
  fi
else
  echo -e "❌ ne301-model-converter-celery:v2 (Backend 缺失)"
  CELERY_MISSING=true
fi

# 检查 Redis
if docker images | grep -q "redis.*7-alpine"; then
  echo -e "✅ redis:7-alpine (官方镜像)"
else
  echo -e "⚠️  redis:7-alpine (将自动拉取)"
fi

echo ""
echo "=== 镜像列表 ==="
docker images | grep -E "ne301-model-converter|redis|REPOSITORY"

echo ""
echo "=== 验证完成 ==="

if [ -n "$FRONTEND_MISSING" ] || [ -n "$BACKEND_MISSING" ]; then
  echo -e "\n❌ 部分镜像缺失，需要重新构建"
  echo ""
  echo "构建命令："
  [ -n "$FRONTEND_MISSING" ] && echo "  ./build-parallel.sh frontend"
  [ -n "$BACKEND_MISSING" ] && echo "  ./build-parallel.sh backend"
  echo ""
  echo "或并行构建所有："
  echo "  ./build-parallel.sh"
  exit 1
else
  echo -e "\n✅ 所有镜像准备就绪"
  echo ""
  echo "启动服务："
  echo "  make docker-up"
  echo "  或: docker-compose up -d"
  echo ""
  echo "查看服务状态："
  echo "  docker-compose ps"
  exit 0
fi
