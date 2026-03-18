#!/bin/bash
# 快速验证修复效果

echo "============================================================"
echo "NE301 修复验证"
echo "============================================================"
echo ""

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. 检查服务健康
echo "1. 检查服务健康状态..."
if curl -s http://localhost:8000/api/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ 服务健康${NC}"
else
    echo "❌ 服务不健康"
    exit 1
fi

echo ""

# 2. 检查环境状态
echo "2. 检查环境状态..."
ENV_STATUS=$(curl -s http://localhost:8000/api/setup/check | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
if [ "$ENV_STATUS" == "ready" ]; then
    echo -e "${GREEN}✅ 环境就绪${NC}"
else
    echo "❌ 环境未就绪: $ENV_STATUS"
    exit 1
fi

echo ""
echo "============================================================"
echo -e "${GREEN}✅ 验证通过！服务已准备好进行转换测试${NC}"
echo "============================================================"
echo ""
echo "下一步:"
echo "  1. 访问 http://localhost:8000"
echo "  2. 上传 256x256 模型 + YAML + 校准数据集"
echo "  3. 观察日志中的输入尺寸验证:"
echo "     docker-compose logs -f api | grep -A 5 '输入尺寸验证'"
echo ""
echo "  4. 转换完成后检查:"
echo "     - bin 文件大小: ls -lh ne301/build/*.bin"
echo "     - JSON 配置: cat ne301/Model/weights/*.json | grep -A 5 'input_spec'"
echo ""
