#!/bin/bash

# 手动量化测试脚本
# 测试 fraction 参数和 fake 量化逻辑

set -e

echo "========================================="
echo "🧪 NE301 量化功能手动测试"
echo "========================================="
echo ""

BASE_URL="http://localhost:8000"
MODEL_PATH="demo/best.pt"
YAML_PATH="demo/household_trash.yaml"
CALIB_PATH="demo/calibration.zip"

# 测试 1: 无校准数据集（fake 量化）
echo "📝 测试 1: 无校准数据集（fake 量化）"
echo "-----------------------------------------"
echo "预期行为:"
echo "  - 使用 fake 量化模式"
echo "  - fraction 参数不生效"
echo "  - 日志显示: '量化模式: 假量化（fake=True，精度可能下降）'"
echo ""

RESPONSE=$(curl -s -X POST "${BASE_URL}/api/convert" \
  -F "model_file=@${MODEL_PATH}" \
  -F "yaml_file=@${YAML_PATH}" \
  -F 'config={"model_type": "YOLOv8", "input_size": 640, "num_classes": 6}')

TASK_ID=$(echo "$RESPONSE" | jq -r '.task_id')

if [ "$TASK_ID" = "null" ] || [ -z "$TASK_ID" ]; then
  echo "❌ 创建任务失败"
  echo "$RESPONSE" | jq .
  exit 1
fi

echo "✅ 任务已创建: $TASK_ID"
echo ""

# 监控任务进度
echo "📊 监控任务进度..."
echo ""

for i in {1..60}; do
  sleep 5
  STATUS=$(curl -s "${BASE_URL}/api/tasks/${TASK_ID}" | jq -r '.status')
  PROGRESS=$(curl -s "${BASE_URL}/api/tasks/${TASK_ID}" | jq -r '.progress')

  echo "[$i/60] 状态: $STATUS | 进度: $PROGRESS%"

  if [ "$STATUS" = "completed" ]; then
    echo ""
    echo "✅ 测试 1 完成!"
    echo ""

    # 检查日志
    echo "📋 任务日志（查找 fake 量化关键词）:"
    curl -s "${BASE_URL}/api/tasks/${TASK_ID}" | jq -r '.logs[]' | grep -E "fake|假量化|量化模式" || echo "未找到相关日志"
    echo ""
    break
  fi

  if [ "$STATUS" = "failed" ]; then
    echo ""
    echo "❌ 测试 1 失败!"
    curl -s "${BASE_URL}/api/tasks/${TASK_ID}" | jq .
    exit 1
  fi
done

echo ""
echo "按 Enter 继续测试 2..."
read

# 测试 2: 有校准数据集（真实量化，fraction=0.2）
echo ""
echo "📝 测试 2: 有校准数据集（真实量化，fraction=0.2）"
echo "-----------------------------------------"
echo "预期行为:"
echo "  - 使用真实量化模式"
echo "  - fraction=0.2（采样 20% 校准数据）"
echo "  - 日志显示: '量化模式: 真实量化（fake=False）'"
echo "  - 日志显示: '校准数据采样比例: 0.2'"
echo ""

RESPONSE=$(curl -s -X POST "${BASE_URL}/api/convert" \
  -F "model_file=@${MODEL_PATH}" \
  -F "yaml_file=@${YAML_PATH}" \
  -F "calibration_dataset=@${CALIB_PATH}" \
  -F 'config={"model_type": "yolov8", "input_size": 640, "num_classes": 6, "fraction": 0.2}')

TASK_ID=$(echo "$RESPONSE" | jq -r '.task_id')

if [ "$TASK_ID" = "null" ] || [ -z "$TASK_ID" ]; then
  echo "❌ 创建任务失败"
  echo "$RESPONSE" | jq .
  exit 1
fi

echo "✅ 任务已创建: $TASK_ID"
echo ""

# 监控任务进度
echo "📊 监控任务进度..."
echo ""

for i in {1..60}; do
  sleep 5
  STATUS=$(curl -s "${BASE_URL}/api/tasks/${TASK_ID}" | jq -r '.status')
  PROGRESS=$(curl -s "${BASE_URL}/api/tasks/${TASK_ID}" | jq -r '.progress')

  echo "[$i/60] 状态: $STATUS | 进度: $PROGRESS%"

  if [ "$STATUS" = "completed" ]; then
    echo ""
    echo "✅ 测试 2 完成!"
    echo ""

    # 检查日志
    echo "📋 任务日志（查找真实量化关键词）:"
    curl -s "${BASE_URL}/api/tasks/${TASK_ID}" | jq -r '.logs[]' | grep -E "fraction|真实量化|校准数据采样|量化模式" || echo "未找到相关日志"
    echo ""
    break
  fi

  if [ "$STATUS" = "failed" ]; then
    echo ""
    echo "❌ 测试 2 失败!"
    curl -s "${BASE_URL}/api/tasks/${TASK_ID}" | jq .
    exit 1
  fi
done

echo ""
echo "========================================="
echo "🎉 所有测试完成!"
echo "========================================="