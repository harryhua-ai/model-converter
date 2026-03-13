#!/bin/bash
# 验证 Docker 架构配置

echo "=== Docker 架构验证 ==="
echo ""

echo "1️⃣  检查 docker-compose 配置..."
docker-compose -f docker-compose-rosetta.yml config 2>/dev/null | grep -A 2 "platform:" || echo "⚠️  未找到 platform 配置"
echo ""

echo "2️⃣  检查运行中容器的架构..."
docker ps --format "table {{.Names}}\t{{.Architecture}}"
echo ""

echo "3️⃣  检查镜像架构..."
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Architecture}}" | grep -E "(REPOSITORY|ne301-model-converter|redis)"
echo ""

echo "4️⃣  测试 Redis 连接..."
if docker ps | grep -q "redis"; then
    docker-compose -f docker-compose-rosetta.yml exec -T redis redis-cli ping 2>/dev/null || echo "⚠️  Redis 未响应"
else
    echo "⚠️  Redis 容器未运行"
fi
echo ""

echo "5️⃣  测试 Backend API..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend API 正常"
    curl -s http://localhost:8000/health | jq . 2>/dev/null || curl -s http://localhost:8000/health
else
    echo "⚠️  Backend 未响应"
fi
echo ""

echo "6️⃣  测试 Frontend..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend 正常"
else
    echo "⚠️  Frontend 未响应"
fi
echo ""

echo "✅ 验证完成"
