#!/bin/bash
# NE301 模型转换工具 Shell 封装

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# 检查参数
if [ $# -lt 1 ]; then
    echo "用法: $0 <model.pt> --preset <yolov8n-256|yolov8n-480|yolov8n-640> [选项]"
    echo ""
    echo "示例:"
    echo "  $0 yolov8n.pt --preset yolov8n-480"
    echo "  $0 model.pt -p yolov8n-480 --num-classes 10"
    echo ""
    echo "选项:"
    echo "  --output, -o       输出目录 (默认: ./outputs)"
    echo "  --num-classes, -n  类别数量"
    echo "  --class-names      类别名称列表"
    echo "  --calibration, -c  校准数据集 ZIP 文件"
    echo "  --data-yaml, -d    data.yaml 配置文件"
    exit 1
fi

# 进入脚本所在目录
cd "$(dirname "$0")"

# 检查虚拟环境
if [ ! -d "backend/venv" ]; then
    echo -e "${RED}错误: 虚拟环境不存在，请先运行 ./start.sh${NC}"
    exit 1
fi

# 激活虚拟环境
source backend/venv/bin/activate

# 运行转换
python3 convert.py "$@"
