#!/bin/bash
# NE301 修复部署脚本
# 部署输入尺寸验证和版本号修复

set -e

echo "============================================================"
echo "NE301 修复部署"
echo "============================================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/Users/harryhua/Documents/GitHub/model-converter"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "📁 项目目录: $PROJECT_ROOT"
echo "📁 后端目录: $BACKEND_DIR"
echo ""

# 步骤 1: 验证修复代码
echo "============================================================"
echo "步骤 1: 验证修复代码"
echo "============================================================"
echo ""

echo "1.1 检查版本号修复..."
if grep -q "MODEL_VERSION_OVERRIDE" "$BACKEND_DIR/app/core/ne301_config.py"; then
    echo -e "${GREEN}✅ 版本号修复已应用${NC}"
else
    echo -e "${RED}❌ 版本号修复未找到${NC}"
    exit 1
fi

echo ""
echo "1.2 检查输入尺寸验证..."
if grep -q "_extract_input_size_from_tflite" "$BACKEND_DIR/app/core/docker_adapter.py"; then
    echo -e "${GREEN}✅ 输入尺寸验证已添加${NC}"
else
    echo -e "${RED}❌ 输入尺寸验证未找到${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ 所有修复代码验证通过${NC}"
echo ""

# 步骤 2: 重启服务
echo "============================================================"
echo "步骤 2: 重启 Docker 服务"
echo "============================================================"
echo ""

echo "2.1 停止现有容器..."
docker-compose -f "$PROJECT_ROOT/docker-compose.yml" stop model-converter-api || true

echo ""
echo "2.2 重新构建镜像（如果需要）..."
read -p "是否需要重新构建镜像? (y/N): " rebuild_choice

if [[ "$rebuild_choice" =~ ^[Yy]$ ]]; then
    echo "重新构建镜像..."
    docker-compose -f "$PROJECT_ROOT/docker-compose.yml" build --no-cache model-converter-api
else
    echo "跳过重新构建（使用现有镜像）"
fi

echo ""
echo "2.3 启动容器..."
docker-compose -f "$PROJECT_ROOT/docker-compose.yml" up -d model-converter-api

echo ""
echo "2.4 等待服务启动..."
sleep 5

# 步骤 3: 验证服务
echo ""
echo "============================================================"
echo "步骤 3: 验证服务状态"
echo "============================================================"
echo ""

echo "3.1 检查容器状态..."
if docker ps | grep -q "model-converter-api"; then
    echo -e "${GREEN}✅ 容器正在运行${NC}"
else
    echo -e "${RED}❌ 容器未运行${NC}"
    docker-compose -f "$PROJECT_ROOT/docker-compose.yml" logs model-converter-api
    exit 1
fi

echo ""
echo "3.2 检查健康状态..."
sleep 3
if curl -s http://localhost:8000/api/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ 服务健康${NC}"
else
    echo -e "${YELLOW}⚠️  服务可能还在启动中${NC}"
fi

echo ""
echo "3.3 查看最近日志..."
docker-compose -f "$PROJECT_ROOT/docker-compose.yml" logs --tail=20 model-converter-api

# 步骤 4: 测试建议
echo ""
echo "============================================================"
echo "步骤 4: 测试建议"
echo "============================================================"
echo ""

echo "现在可以进行以下测试："
echo ""
echo "1. 测试转换（使用 256x256 模型）"
echo "   - 访问: http://localhost:8000"
echo "   - 上传模型 + YAML + 校准数据集"
echo "   - 选择 256x256 输入尺寸"
echo "   - 观察日志中的输入尺寸验证"
echo ""
echo "2. 查看日志"
echo "   docker-compose logs -f model-converter-api"
echo ""
echo "3. 验证 bin 文件大小"
echo "   ls -lh ne301/build/*_pkg.bin"
echo "   期望: ~4.5 MB（而不是之前的 5.9 MB）"
echo ""
echo "4. 检查 JSON 配置"
echo "   cat ne301/Model/weights/model_*.json | grep -A 5 'input_spec'"
echo "   期望: \"width\": 256, \"height\": 256"
echo ""

echo "============================================================"
echo -e "${GREEN}✅ 部署完成！${NC}"
echo "============================================================"
