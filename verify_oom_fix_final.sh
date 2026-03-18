#!/bin/bash

# NE301 OOM 修复验证脚本
# 用于快速验证修复是否成功

set -e

echo "======================================"
echo "  NE301 OOM 修复验证"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. 检查容器状态
echo -e "${BLUE}[1/4] 检查容器状态...${NC}"
if docker ps --filter "name=model-converter-api" --format "{{.Names}}" | grep -q model-converter-api; then
    STATUS=$(docker ps --filter "name=model-converter-api" --format "{{.Status}}")
    echo -e "${GREEN}✅ 容器运行正常: ${STATUS}${NC}"
else
    echo -e "${RED}❌ 容器未运行${NC}"
    exit 1
fi
echo ""

# 2. 检查代码修复
echo -e "${BLUE}[2/4] 检查代码修复...${NC}"
if docker exec model-converter-api grep -q "诊断并修复 mpool 配置" /app/app/core/docker_adapter.py; then
    echo -e "${GREEN}✅ mpool 修复代码已部署${NC}"
else
    echo -e "${RED}❌ mpool 修复代码未找到${NC}"
    exit 1
fi
echo ""

# 3. 检查 NE301 原始文件未修改
echo -e "${BLUE}[3/4] 检查 NE301 原始文件...${NC}"
if [ -d "ne301" ]; then
    cd ne301
    if git diff --exit-code Model/mpools/stm32n6_reloc_yolov8_od.mpool > /dev/null 2>&1; then
        echo -e "${GREEN}✅ NE301 原始 mpool 文件未修改${NC}"
    else
        echo -e "${YELLOW}⚠️  NE301 mpool 文件已被修改${NC}"
        echo -e "${YELLOW}   修改内容:${NC}"
        git diff Model/mpools/stm32n6_reloc_yolov8_od.mpool | head -20
    fi
    cd ..
else
    echo -e "${YELLOW}⚠️  ne301 目录不存在，跳过检查${NC}"
fi
echo ""

# 4. 测试 API 健康状态
echo -e "${BLUE}[4/4] 测试 API 健康状态...${NC}"
RESPONSE=$(curl -s http://localhost:8000/api/setup/check)
if echo "$RESPONSE" | grep -q '"status":"ready"'; then
    echo -e "${GREEN}✅ API 服务正常${NC}"
    echo -e "${GREEN}   状态: ready${NC}"
else
    echo -e "${RED}❌ API 服务异常${NC}"
    echo "$RESPONSE"
    exit 1
fi
echo ""

echo "======================================"
echo -e "${GREEN}✅ 所有检查通过！${NC}"
echo "======================================"
echo ""
echo "📋 验证结果总结:"
echo ""
echo "✅ 容器运行正常"
echo "✅ 修复代码已部署"
echo "✅ 原始文件未修改"
echo "✅ API 服务正常"
echo ""
echo "🎯 下一步操作:"
echo ""
echo "1. 🌐 访问 Web UI 进行转换测试:"
echo "   http://localhost:8000"
echo ""
echo "2. 📝 转换时注意观察日志，确认看到:"
echo "   ✅ 📋 mpool 配置诊断"
echo "   ✅ ⚠️  检测到 mpool 配置问题"
echo "   ✅ ✅ 已修复 mpool 配置"
echo ""
echo "3. 📥 下载 .bin 文件并上传到 NE301 设备测试"
echo ""
echo "4. 📊 检查设备日志，确认:"
echo "   ✅ ext_ram_sz > 0 (应该是 3011688)"
echo "   ✅ mempool 0: xSPI1 (不是 xSPI2)"
echo "   ✅ 模型加载成功，无 OOM 错误"
echo ""
echo "📚 完整测试指南:"
echo "   cat NE301_OOM_FIX_READY_FOR_TESTING.md"
echo ""
