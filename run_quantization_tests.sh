#!/bin/bash
# 量化流程测试执行脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  NE301 量化流程测试${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${RED}错误: 虚拟环境不存在${NC}"
    echo "请先运行: python3 -m venv venv"
    exit 1
fi

# 激活虚拟环境
echo -e "${YELLOW}激活虚拟环境...${NC}"
source venv/bin/activate

# 进入 backend 目录
cd backend

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  运行量化流程测试${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 解析命令行参数
TEST_TYPE="${1:-all}"

case $TEST_TYPE in
    unit)
        echo -e "${YELLOW}运行单元测试...${NC}"
        pytest tests/test_quantization_flow.py -m unit -v --tb=short
        ;;
    integration)
        echo -e "${YELLOW}运行集成测试...${NC}"
        pytest tests/test_quantization_flow.py -m integration -v --tb=short
        ;;
    coverage)
        echo -e "${YELLOW}生成覆盖率报告...${NC}"
        pytest tests/test_quantization_flow.py --cov=app.core.docker_adapter --cov-report=html --cov-report=term
        echo ""
        echo -e "${GREEN}覆盖率报告已生成: backend/htmlcov/index.html${NC}"
        ;;
    specific)
        if [ -z "$2" ]; then
            echo -e "${RED}错误: 请指定测试名称${NC}"
            echo "示例: ./run_quantization_tests.sh specific TestExportToSavedModel::test_export_to_saved_model_success"
            exit 1
        fi
        echo -e "${YELLOW}运行特定测试: $2${NC}"
        pytest tests/test_quantization_flow.py::$2 -v --tb=short
        ;;
    all)
        echo -e "${YELLOW}运行所有测试...${NC}"
        pytest tests/test_quantization_flow.py -v --tb=short
        ;;
    *)
        echo -e "${RED}错误: 未知的测试类型 '$TEST_TYPE'${NC}"
        echo ""
        echo "用法: $0 [unit|integration|coverage|specific|all] [test_name]"
        echo ""
        echo "示例:"
        echo "  $0                    # 运行所有测试"
        echo "  $0 unit               # 只运行单元测试"
        echo "  $0 integration        # 只运行集成测试"
        echo "  $0 coverage           # 生成覆盖率报告"
        echo "  $0 specific TestExportToSavedModel::test_export_to_saved_model_success"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  测试完成${NC}"
echo -e "${GREEN}========================================${NC}"
