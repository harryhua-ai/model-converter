#!/bin/bash

# 前端修复验证脚本
# 使用方法: ./scripts/verify-frontend-fix.sh

echo "🔍 开始验证前端修复..."
echo ""

# 1. 检查 vite.config.ts 配置
echo "1️⃣ 检查 vite.config.ts 配置..."
if grep -q "jsx: 'automatic'" frontend/vite.config.ts; then
    echo "❌ 配置错误: 仍然包含 esbuild jsx 配置"
    echo "请确保移除了以下配置:"
    echo "  esbuild:"
    echo "    jsx: 'automatic'"
    echo "    jsxImportSource: 'preact'"
    exit 1
else
    echo "✅ vite.config.ts 配置正确"
fi
echo ""

# 2. 检查构建产物
echo "2️⃣ 检查构建产物..."
if [ ! -f "frontend/dist/index.html" ]; then
    echo "❌ 构建产物不存在: frontend/dist/index.html"
    echo "请先运行: cd frontend && npm run build"
    exit 1
fi

if [ ! -f "frontend/dist/assets/index-6KA3L6WJ.js" ]; then
    echo "❌ JavaScript 文件不存在"
    exit 1
fi

echo "✅ 构建产物存在"
JS_SIZE=$(du -h frontend/dist/assets/index-6KA3L6WJ.js | cut -f1)
echo "   文件大小: $JS_SIZE"
echo ""

# 3. 检查 Docker 容器
echo "3️⃣ 检查 Docker 容器状态..."
if ! docker ps | grep -q "model-converter-api"; then
    echo "❌ Docker 容器未运行"
    echo "请先启动: docker-compose up -d"
    exit 1
fi
echo "✅ Docker 容器正在运行"
echo ""

# 4. 测试 HTTP 访问
echo "4️⃣ 测试 HTTP 访问..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/)
if [ "$HTTP_CODE" -ne 200 ]; then
    echo "❌ HTTP 访问失败: 状态码 $HTTP_CODE"
    exit 1
fi
echo "✅ HTTP 访问正常: 状态码 200"
echo ""

# 5. 检查 JavaScript 文件加载
echo "5️⃣ 检查 JavaScript 文件可访问性..."
JS_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/assets/index-6KA3L6WJ.js)
if [ "$JS_HTTP_CODE" -ne 200 ]; then
    echo "❌ JavaScript 文件无法访问: 状态码 $JS_HTTP_CODE"
    exit 1
fi
echo "✅ JavaScript 文件可访问"
echo ""

# 6. 验证完成
echo "✅ 验证完成！"
echo ""
echo "📋 下一步操作:"
echo "   1. 在浏览器中访问: http://localhost:8000/"
echo "   2. 打开开发者工具（F12）"
echo "   3. 检查 Console 标签是否有错误"
echo "   4. 检查 Elements 标签中的 <div id=\"app\"> 是否有内容"
echo ""
echo "🔧 如果仍然空白，请:"
echo "   1. 清除浏览器缓存（Ctrl+Shift+Delete / Cmd+Shift+Delete）"
echo "   2. 使用无痕模式重新访问"
echo "   3. 查看 docs/FRONTEND_DEBUG_REPORT.md 获取详细诊断信息"
echo ""
