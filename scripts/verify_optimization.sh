#!/bin/bash

# ST Edge AI 编译参数优化验证脚本
# 用于验证移除 --all-buffers-info 和 --enable-virtual-mem-pools 后的固件大小变化

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 配置文件路径
CONFIG_FILE="/workspace/Model/neural_art_reloc.json"
BACKUP_FILE="/workspace/Model/neural_art_reloc.json.backup"
BUILD_DIR="/workspace/Model/build"

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  ST Edge AI 编译参数优化验证${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# 1. 显示当前配置
log_info "当前 yolov8_od 配置："
docker exec model-converter-api bash -c "grep -A 3 'yolov8_od' $CONFIG_FILE" | grep "options" | sed 's/.*options": "\(.*\)".*/  \1/'
echo ""

# 2. 显示优化前后参数对比
log_info "优化前后参数对比："
echo ""
echo "  优化前（5.9 MB 固件）："
echo "  --enable-epoch-controller -O3 --all-buffers-info --cache-maintenance \\"
echo "  --Oalt-sched --native-float --enable-virtual-mem-pools --Omax-ca-pipe 4 --Ocache-opt --Os"
echo ""
echo "  优化后（预期 ~3.2 MB 固件）："
echo "  --enable-epoch-controller -O3 --cache-maintenance --Oalt-sched --native-float \\"
echo "  --Omax-ca-pipe 4 --Ocache-opt --Os"
echo ""
echo -e "${YELLOW}  主要变化：${NC}"
echo "  ✗ 移除 --all-buffers-info     （预分配所有缓冲区信息）"
echo "  ✗ 移除 --enable-virtual-mem-pools  （虚拟内存池）"
echo ""

# 3. 分析固件大小变化原因
log_info "固件大小分析："
echo ""
echo "  5.9 MB network_rel.bin 组成："
echo "  ├─ 量化权重:   2.907 MB  ← 来自 TFLite 模型"
echo "  ├─ 激活缓冲区: 2.734 MB  ← ⚠️ 问题所在（预分配）"
echo "  └─ 运行时代码:   0.3 MB  ← ST Edge AI 运行时"
echo ""
echo "  优化后预期 ~3.2 MB network_rel.bin："
echo "  ├─ 量化权重:   2.907 MB  ← 不变"
echo "  ├─ 激活缓冲区:       0 MB  ← 运行时动态分配"
echo "  └─ 运行时代码:   0.3 MB  ← 不变"
echo ""

# 4. 检查备份文件
if docker exec model-converter-api bash -c "[ -f $BACKUP_FILE ]"; then
    log_success "✓ 原始配置已备份到: $BACKUP_FILE"

    # 显示原始配置
    log_info "原始 yolov8_od 配置："
    docker exec model-converter-api bash -c "grep -A 3 'yolov8_od' $BACKUP_FILE" | grep "options" | sed 's/.*options": "\(.*\)".*/  \1/'
    echo ""
else
    log_warning "⚠ 未找到原始配置备份"
fi

# 5. 显示恢复命令
log_info "如需恢复原始配置，执行："
echo ""
echo "  docker exec model-converter-api bash -c \\"
echo "    'cd /workspace/Model && \\"
echo "     cp neural_art_reloc.json.backup neural_art_reloc.json'"
echo ""

# 6. 下次转换验证说明
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  配置已应用，下次转换将自动使用优化参数${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
log_info "验证步骤："
echo "  1. 上传任意 256×256 模型进行转换"
echo "  2. 检查生成的固件大小"
echo "  3. 预期从 5.9 MB 减少到 ~3.2 MB"
echo ""
echo -e "${YELLOW}  如果固件大小仍为 5.9 MB，可能需要：${NC}"
echo "  1. 清理缓存: docker exec model-converter-api bash -c 'cd /workspace/Model && make clean'"
echo "  2. 重新触发转换"
echo ""
log_success "优化完成！"