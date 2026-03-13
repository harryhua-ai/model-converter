#!/bin/bash
# E2E 测试脚本 - 完整转换流程测试

set -e

TASK_ID=""
MODEL_FILE="demo/best.pt"
CONFIG='{"model_type": "YOLOv8", "input_size": 640, "num_classes": 30, "quantization": "int8"}'
YAML_FILE="demo/household_trash.yaml"
CALIBRATION_DATASET="demo/calibration.zip"

echo "=================================="
echo "E2E 测试 - 端到端转换流程"
echo "=================================="

# 1. 提交转换任务
echo ""
echo "📤 [1/6] 提交转换任务..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/convert \
  -F "model_file=@${MODEL_FILE}" \
  -F "config=${CONFIG}" \
  -F "yaml_file=@${YAML_FILE}" \
  -F "calibration_dataset=@${CALIBRATION_DATASET}")

echo "响应: ${RESPONSE}"

# 提取 task_id
TASK_ID=$(echo ${RESPONSE} | python3 -c "import sys, json; print(json.load(sys.stdin).get('task_id', ''))" 2>/dev/null || echo "")

if [ -z "$TASK_ID" ]; then
    echo "❌ 提交任务失败"
    exit 1
fi

echo "✅ 任务已创建: ${TASK_ID}"

# 2. 等待任务开始
echo ""
echo "⏳ [2/6] 等待任务启动..."
sleep 5

# 3. 监控转换进度
echo ""
echo "📊 [3/6] 监控转换进度..."
MAX_WAIT=600  # 最多等待 10 分钟
WAIT_TIME=0
PROGRESS=0

while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    STATUS_RESPONSE=$(curl -s http://localhost:8000/api/tasks/${TASK_ID})
    STATUS=$(echo ${STATUS_RESPONSE} | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "unknown")
    PROGRESS=$(echo ${STATUS_RESPONSE} | python3 -c "import sys, json; print(json.load(sys.stdin).get('progress', 0))" 2>/dev/null || echo "0")
    CURRENT_STEP=$(echo ${STATUS_RESPONSE} | python3 -c "import sys, json; print(json.load(sys.stdin).get('current_step', ''))" 2>/dev/null || echo "")

    printf "\r进度: %d%% | 状态: %s | 步骤: %s" "${PROGRESS}" "${STATUS}" "${CURRENT_STEP}"

    if [ "${STATUS}" = "completed" ]; then
        echo ""
        echo "✅ 转换成功！"
        break
    fi

    if [ "${STATUS}" = "failed" ]; then
        echo ""
        ERROR=$(echo ${STATUS_RESPONSE} | python3 -c "import sys, json; print(json.load(sys.stdin).get('error_message', 'Unknown error'))" 2>/dev/null || echo "Unknown error")
        echo "❌ 转换失败: ${ERROR}"
        exit 1
    fi

    sleep 5
    WAIT_TIME=$((WAIT_TIME + 5))
done

if [ $WAIT_TIME -ge $MAX_WAIT ]; then
    echo ""
    echo "⏰ 超时：任务未在 ${MAX_WAIT} 秒内完成"
    exit 1
fi

# 4. 验证输出文件
echo ""
echo "📁 [4/6] 验证输出文件..."
TASK_DETAIL=$(curl -s http://localhost:8000/api/tasks/${TASK_ID})
OUTPUT_FILE=$(echo ${TASK_DETAIL} | python3 -c "import sys, json; print(json.load(sys.stdin).get('output_filename', ''))" 2>/dev/null || echo "")

if [ -z "$OUTPUT_FILE" ]; then
    echo "⚠️  未找到输出文件名"
else
    echo "✅ 输出文件: ${OUTPUT_FILE}"

    # 尝试下载文件
    echo ""
    echo "📥 [5/6] 下载输出文件..."
    curl -s http://localhost:8000/api/tasks/${TASK_ID}/download -o e2e_test_output.bin

    if [ -f "e2e_test_output.bin" ]; then
        FILE_SIZE=$(ls -lh e2e_test_output.bin | awk '{print $5}')
        echo "✅ 文件已下载: e2e_test_output.bin (${FILE_SIZE})"

        # 验证文件类型
        FILE_TYPE=$(file e2e_test_output.bin | awk '{print $2}')
        echo "📄 文件类型: ${FILE_TYPE}"
    else
        echo "⚠️  文件下载失败"
    fi
fi

# 5. 显示完整任务信息
echo ""
echo "📋 [6/6] 完整任务信息："
echo ${TASK_DETAIL} | python3 -m json.tool

echo ""
echo "=================================="
echo "✅ E2E 测试完成！"
echo "=================================="
echo ""
echo "任务 ID: ${TASK_ID}"
echo "查看详情: curl http://localhost:8000/api/tasks/${TASK_ID}"
echo "下载文件: curl http://localhost:8000/api/tasks/${TASK_ID}/download -o output.bin"
