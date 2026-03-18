#!/bin/bash

# NE301 OOM 修复验证脚本
# 用于快速验证修复是否成功

set -e

echo "======================================"
echo "  NE301 OOM 修复验证脚本"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 检查代码修改
echo -e "${YELLOW}[1/5] 检查代码修改...${NC}"
if grep -q "压缩二进制大小：修改内存池配置" backend/app/core/docker_adapter.py; then
    echo -e "${RED}❌ 错误: mpool 修改代码仍然存在${NC}"
    exit 1
else
    echo -e "${GREEN}✅ mpool 修改代码已删除${NC}"
fi
echo ""

# 2. 检查 Docker 服务
echo -e "${YELLOW}[2/5] 检查 Docker 服务...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ 错误: Docker 未运行${NC}"
    echo "请先启动 Docker Desktop"
    exit 1
else
    echo -e "${GREEN}✅ Docker 运行正常${NC}"
fi
echo ""

# 3. 重启服务
echo -e "${YELLOW}[3/5] 重启 API 服务...${NC}"
if docker ps | grep -q model-converter-api; then
    docker-compose restart api
    echo -e "${GREEN}✅ API 服务已重启${NC}"
else
    echo -e "${YELLOW}⚠️  API 容器未运行，尝试启动...${NC}"
    docker-compose up -d
    echo -e "${GREEN}✅ 服务已启动${NC}"
fi
echo ""

# 4. 等待服务就绪
echo -e "${YELLOW}[4/5] 等待服务就绪...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health > /dev/null; then
        echo -e "${GREEN}✅ 服务已就绪${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ 服务启动超时${NC}"
        exit 1
    fi
    sleep 1
done
echo ""

# 5. 检查环境配置
echo -e "${YELLOW}[5/5] 检查环境配置...${NC}"
RESPONSE=$(curl -s http://localhost:8000/api/setup/check)
if echo "$RESPONSE" | grep -q '"docker_running":true'; then
    echo -e "${GREEN}✅ Docker 环境正常${NC}"
else
    echo -e "${RED}❌ Docker 环境异常${NC}"
    echo "$RESPONSE"
    exit 1
fi
echo ""

echo "======================================"
echo -e "${GREEN}✅ 所有检查通过！${NC}"
echo "======================================"
echo ""
echo "下一步操作："
echo ""
echo "1. 通过 Web UI 上传测试模型："
echo "   http://localhost:8000"
echo ""
echo "2. 或使用 API 转换模型："
echo "   curl -X POST http://localhost:8000/api/convert \\"
echo "     -F 'model=@your_model.pt' \\"
echo "     -F 'config={\"model_type\":\"yolov8\",\"input_size\":640,\"num_classes\":80}'"
echo ""
echo "3. 检查转换日志，确认："
echo "   - ✅ 不再出现 '已成功优化内存池配置'"
echo "   - ✅ ext ram sz > 0"
echo "   - ✅ mempool 0 在 xSPI1"
echo ""
echo "4. 在 NE301 设备上测试加载 .bin 文件"
echo ""
echo "详细报告: NE301_OOM_FIX_REPORT.md"
echo ""
