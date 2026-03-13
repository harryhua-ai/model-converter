#!/bin/bash
# 检测宿主机架构

ARCH=$(uname -m)
DOCKER_ARCH=$(docker info --format '{{.Architecture}}' 2>/dev/null || echo "unknown")

echo "=== 系统架构检测 ==="
echo "宿主机架构: $ARCH"
echo "Docker 架构: $DOCKER_ARCH"
echo ""

if [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then
    echo "✅ 检测到 Apple Silicon Mac"
    echo ""
    echo "使用统一 AMD64 配置（与生产环境一致）："
    echo "  docker-compose -f docker-compose-rosetta.yml up -d"
    echo ""
    echo "性能预估（Rosetta 2 翻译）："
    echo "  Frontend (AMD64 via Rosetta)  ← 95% 性能"
    echo "  Redis (AMD64 via Rosetta)     ← 85-90% 性能"
    echo "  Backend (AMD64 via Rosetta)   ← 75% 性能"
    echo "  Celery (AMD64 via Rosetta)    ← 70% 性能"
    echo "  总体性能: ~80-85%"
    echo ""
    echo "优势："
    echo "  ✅ 与生产环境完全一致"
    echo "  ✅ 避免架构不匹配问题"
    echo "  ✅ 用户可直接拉取镜像"
elif [ "$ARCH" = "x86_64" ]; then
    echo "✅ 检测到 Intel/AMD 系统"
    echo ""
    echo "使用统一 AMD64 配置（原生性能）："
    echo "  docker-compose -f docker-compose-rosetta.yml up -d"
    echo ""
    echo "性能预估（原生）："
    echo "  Frontend (AMD64 原生)  ← 100% 性能"
    echo "  Redis (AMD64 原生)     ← 100% 性能"
    echo "  Backend (AMD64 原生)   ← 100% 性能"
    echo "  Celery (AMD64 原生)    ← 100% 性能"
    echo "  总体性能: 100%"
else
    echo "⚠️  未知架构: $ARCH"
    echo "请使用标准配置: docker-compose up -d"
fi
