#!/bin/bash
# NE301 转换日志监控脚本（简化版）
# 实时监控转换过程中的关键信息

echo "============================================================"
echo "NE301 转换日志监控"
echo "============================================================"
echo ""
echo "监控内容:"
echo "  - 📏 输入尺寸验证"
echo "  - 🔢 版本号读取"
echo "  - 📊 转换进度"
echo "  - 📦 bin 文件大小"
echo "  - ⚠️  错误和警告"
echo ""
echo "按 Ctrl+C 停止监控"
echo "============================================================"
echo ""

# 实时监控日志，过滤关键信息
docker-compose logs -f api 2>&1 | grep --line-buffered -E \
    "输入尺寸|版本号|MODEL_VERSION|验证|步骤|完成|失败|ERROR|WARNING|bin|MB|ne301_Model" \
    | while IFS= read -r line; do
        # 根据内容添加颜色
        if echo "$line" | grep -q "✅\|完成\|成功\|passed"; then
            echo -e "\033[0;32m$line\033[0m"
        elif echo "$line" | grep -q "❌\|ERROR\|失败"; then
            echo -e "\033[0;31m$line\033[0m"
        elif echo "$line" | grep -q "⚠️\|WARNING\|警告"; then
            echo -e "\033[1;33m$line\033[0m"
        elif echo "$line" | grep -q "输入尺寸\|验证\|TFLite"; then
            echo -e "\033[0;36m$line\033[0m"
        elif echo "$line" | grep -q "版本\|MODEL_VERSION"; then
            echo -e "\033[0;35m$line\033[0m"
        elif echo "$line" | grep -q "步骤"; then
            echo -e "\033[0;34m$line\033[0m"
        else
            echo "$line"
        fi
    done
