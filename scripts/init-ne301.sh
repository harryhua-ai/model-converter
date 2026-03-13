#!/bin/bash
set -e

NE301_HOST_DIR="${NE301_PROJECT_PATH:-/workspace/ne301}"
NE301_DOCKER_IMAGE="${NE301_DOCKER_IMAGE:-camthink/ne301-dev:latest}"

echo "[NE301 Init] Starting..."

# 检测是否在容器中
if [ -f "/.dockerenv" ]; then
    echo "[NE301 Init] Running inside container"

    # 检查 NE301 目录是否存在
    if [ -d "$NE301_HOST_DIR" ]; then
        # 检查目录是否为空或缺少关键文件
        if [ ! "$(ls -A $NE301_HOST_DIR 2>/dev/null)" ] || [ ! -d "$NE301_HOST_DIR/Model" ]; then
            echo "[NE301 Init] NE301 project not found, cloning..."

            # 清空目录（如果不为空）
            if [ "$(ls -A $NE301_HOST_DIR 2>/dev/null)" ]; then
                echo "[NE301 Init] Cleaning existing directory..."
                rm -rf "$NE301_HOST_DIR"/*
            fi

            # 克隆 NE301 项目
            git clone --depth 1 https://github.com/camthink-ai/ne301.git "$NE301_HOST_DIR"

            echo "[NE301 Init] ✓ NE301 project cloned"
        else
            echo "[NE301 Init] ✓ NE301 project exists"
        fi
    else
        echo "[NE301 Init] ✗ NE301 directory not found: $NE301_HOST_DIR"
        exit 1
    fi
else
    echo "[NE301 Init] Not in container, skipping NE301 initialization"
fi

# 拉取 NE301 Docker 镜像
echo "[NE301 Init] Pulling NE301 Docker image..."
if docker pull "$NE301_DOCKER_IMAGE"; then
    echo "[NE301 Init] ✓ Docker image ready: $NE301_DOCKER_IMAGE"
else
    echo "[NE301 Init] ⚠ Failed to pull Docker image (may already exist)"
fi

echo "[NE301 Init] ✓ Complete"
