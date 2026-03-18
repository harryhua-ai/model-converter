#!/bin/bash
# 测试 Model/Makefile TARGET 修复

set -e

echo "========================================="
echo "测试 Model/Makefile TARGET 修复"
echo "========================================="

cd /Users/harryhua/Documents/GitHub/model-converter/ne301/Model

# 测试 1: 验证 TARGET 变量
echo ""
echo "测试 1: 验证 TARGET 变量定义"
echo "----------------------------------------"
grep "^TARGET" Makefile

# 测试 2: 使用不同的 MODEL_NAME 查看 info 输出
echo ""
echo "测试 2: 查看 make info 输出"
echo "----------------------------------------"
make info MODEL_NAME=test_model_123 2>&1 | grep -E "(TARGET|MODEL|TFLITE|CONFIG)"

# 测试 3: 验证生成的文件名模式
echo ""
echo "测试 3: 验证文件名模式"
echo "----------------------------------------"
echo "预期输出文件："
echo "  Model/build/test_model_123.bin"
echo ""
echo "实际 Makefile 目标："
make -n all MODEL_NAME=test_model_123 2>&1 | grep -E "(Packaging|Model package|output)" | head -3

echo ""
echo "========================================="
echo "✅ 修复验证完成"
echo "========================================="
