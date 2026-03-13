#!/bin/bash
# 监控 Docker 构建进度

echo "=== Docker 构建监控 ==="
echo ""

while true; do
  clear
  echo "=== 构建状态 $(date '+%H:%M:%S') ==="
  echo ""

  # 检查构建进程
  BUILD_COUNT=$(ps aux | grep "docker-compose.*build" | grep -v grep | wc -l | tr -d ' ')
  echo "🔨 构建进程数: $BUILD_COUNT"
  echo ""

  # 检查镜像
  echo "📦 已构建的镜像:"
  docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" | grep -E "(REPOSITORY|ne301-model-converter)" || echo "  (暂无)"
  echo ""

  # 检查容器
  echo "🐳 容器状态:"
  docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep model-converter || echo "  (暂无)"
  echo ""

  # 检查 Docker Compose 进程
  if pgrep -f "docker-compose" > /dev/null; then
    echo "✅ Docker Compose 正在运行"
    echo ""

    # 尝试获取日志
    echo "📋 最近的构建日志:"
    docker-compose -f docker-compose-rosetta.yml logs --tail=10 2>&1 | grep -E "(Downloading|Installing|Building|Sending|Step)" || echo "  (等待日志...)"
  else
    echo "⚠️  Docker Compose 未运行"
  fi

  echo ""
  echo "按 Ctrl+C 退出监控"
  echo ""
  sleep 5
done
