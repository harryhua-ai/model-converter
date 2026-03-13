#!/bin/bash
# 完整 E2E 测试 - 转换 + 下载

set -e

echo "=================================="
echo "完整 E2E 测试 - 转换 + 下载"
echo "=================================="

# 1. 提交转换任务
echo ""
echo "📤 [1/4] 提交转换任务..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/convert \
  -F "model_file=@demo/best.pt" \
  -F 'config={"model_type": "YOLOv8", "input_size": 640, "num_classes": 30}' \
  -F "yaml_file=@demo/household_trash.yaml" \
  -F "calibration_dataset=@demo/calibration.zip")

TASK_ID=$(echo ${RESPONSE} | python3 -c "import sys, json; print(json.load(sys.stdin).get('task_id', ''))" 2>/dev/null || echo "")

if [ -z "$TASK_ID" ]; then
    echo "❌ 提交任务失败"
    echo "响应: ${RESPONSE}"
    exit 1
fi

echo "✅ 任务已创建: ${TASK_ID}"

# 2. 监控转换进度
echo ""
echo "📊 [2/4] 监控转换进度..."
MAX_WAIT=600
WAIT_TIME=0

while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    STATUS_RESPONSE=$(curl -s http://localhost:8000/api/tasks/${TASK_ID})
    STATUS=$(echo ${STATUS_RESPONSE} | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "unknown")
    PROGRESS=$(echo ${STATUS_RESPONSE} | python3 -c "import sys, json; print(json.load(sys.stdin).get('progress', 0))" 2>/dev/null || echo "0")

    printf "\r进度: %d%% | 状态: %s" "${PROGRESS}" "${STATUS}"

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

# 3. 验证输出文件
echo ""
echo "📁 [3/4] 验证输出文件..."
TASK_DETAIL=$(curl -s http://localhost:8000/api/tasks/${TASK_ID})
OUTPUT_FILE=$(echo ${TASK_DETAIL} | python3 -c "import sys, json; print(json.load(sys.stdin).get('output_filename', ''))" 2>/dev/null || echo "")

if [ -z "$OUTPUT_FILE" ]; then
    echo "⚠️  未找到输出文件名"
    exit 1
fi

echo "✅ 输出文件: ${OUTPUT_FILE}"

# 4. 下载文件
echo ""
echo "📥 [4/4] 下载输出文件..."
curl -s http://localhost:8000/api/tasks/${TASK_ID}/download -o e2e_complete_output.bin

if [ -f "e2e_complete_output.bin" ]; then
    FILE_SIZE=$(ls -lh e2e_complete_output.bin | awk '{print $5}')
    FILE_TYPE=$(file e2e_complete_output.bin | awk '{print $2}')
    echo "✅ 文件已下载: e2e_complete_output.bin (${FILE_SIZE})"
    echo "📄 文件类型: ${FILE_TYPE}"

    # 验证是否是有效的 TFLite 文件
    if file e2e_complete_output.bin | grep -q "data"; then
        echo "✅ 文件格式验证通过"

        # 显示任务详情
        echo ""
        echo "📋 任务详情:"
        echo ${TASK_DETAIL} | python3 -m json.tool
    else
        echo "⚠️  文件格式可能不正确"
        file e2e_complete_output.bin
    fi
else
    echo "⚠️  文件下载失败"
    exit 1
fi

echo ""
echo "=================================="
echo "✅ 完整 E2E 测试通过！"
echo "=================================="
echo ""
echo "任务 ID: ${TASK_ID}"
echo "输出文件: e2e_complete_output.bin"
