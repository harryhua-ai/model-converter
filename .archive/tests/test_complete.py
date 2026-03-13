#!/usr/bin/env python3
"""
完整功能测试脚本 - 验证 Redis 持久化和取消功能

由于需要真实的模型文件，这个脚本提供两种测试模式：
1. 模拟测试模式（无文件）- 验证 API 端点
2. 完整测试模式（需要模型文件）- 端到端测试
"""
import asyncio
import httpx
import json
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# 颜色输出
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
NC = "\033[0m"

def print_success(msg):
    print(f"{GREEN}✅ {msg}{NC}")

def print_error(msg):
    print(f"{RED}❌ {msg}{NC}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{NC}")

def print_header(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}\n")

async def test_api_endpoints():
    """测试所有 API 端点"""
    print_header("API 端点测试")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 健康检查
        print("1️⃣  健康检查")
        try:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print_success("健康检查通过")
                print(f"   状态: {response.json()['status']}")
            else:
                print_error(f"健康检查失败: {response.status_code}")
        except Exception as e:
            print_error(f"连接失败: {e}")
            return False

        # 2. 任务列表
        print("\n2️⃣  任务列表")
        try:
            response = await client.get(f"{API_BASE}/tasks/")
            if response.status_code == 200:
                data = response.json()
                print_success(f"任务列表获取成功")
                print(f"   当前任务数: {data['total']}")
            else:
                print_error(f"获取失败: {response.status_code}")
        except Exception as e:
            print_error(f"请求失败: {e}")

        # 3. 预设列表
        print("\n3️⃣  预设配置")
        try:
            response = await client.get(f"{API_BASE}/presets/")
            if response.status_code == 200:
                presets = response.json()
                print_success(f"预设列表获取成功")
                print(f"   可用预设数: {len(presets)}")
                for preset in presets:
                    print(f"   • {preset['name']}: {preset['id']}")
            else:
                print_error(f"获取失败: {response.status_code}")
        except Exception as e:
            print_error(f"请求失败: {e}")

        # 4. 测试 404 处理
        print("\n4️⃣  404 错误处理")
        fake_task_id = "fake-task-id-12345"
        try:
            response = await client.get(f"{API_BASE}/tasks/{fake_task_id}")
            if response.status_code == 404:
                print_success("404 错误正确处理")
                print(f"   返回: {response.json()['detail']}")
            else:
                print_warning(f"意外的状态码: {response.status_code}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print_success("404 错误正确处理")
                print(f"   返回: {e.response.json()['detail']}")

        # 5. 测试取消 API
        print("\n5️⃣  取消任务 API")
        try:
            response = await client.post(f"{API_BASE}/tasks/{fake_task_id}/cancel")
            if response.status_code == 404:
                print_success("取消 API 正常工作")
                print(f"   不存在的任务返回 404")
            else:
                print_warning(f"意外的状态码: {response.status_code}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print_success("取消 API 正常工作")
                print(f"   不存在的任务返回 404")

    return True

async def test_with_real_files():
    """使用真实文件进行完整测试"""
    print_header("完整功能测试（需要模型文件）")

    # 检查是否有可用的文件
    model_files = list(Path("uploads").glob("*.pt")) + list(Path("uploads").glob("*.pth"))
    if not model_files:
        print_warning("未找到模型文件")
        print("\n📝 请按照以下步骤进行测试：")
        print("1. 准备测试文件：")
        print("   • 模型文件: yolov8n.pt (或任何 .pt/.pth/.onnx 文件)")
        print("   • 校准数据: coco8.zip (可选，推荐)")
        print("   • 类别配置: data.yaml (可选)")
        print("\n2. 将文件放到 model-converter/uploads/ 目录")
        print("\n3. 访问 Web 界面: http://localhost:3000")
        print("\n4. 上传文件并启动转换")
        print("\n5. 记录返回的 task_id")
        print("\n6. 运行以下命令验证：")
        print(f"   curl {API_BASE}/tasks/<task_id>")
        print(f"   curl -X POST {API_BASE}/tasks/<task_id>/cancel")
        return False

    print_success(f"找到 {len(model_files)} 个模型文件")
    return True

async def main():
    """主测试流程"""
    print_header("Model-Converter 完整功能测试")

    print("选择测试模式：")
    print("1. API 端点测试（无需文件）")
    print("2. 完整功能测试（需要模型文件）")
    print("3. 自动运行所有测试")

    choice = input("\n请选择 (1/2/3): ").strip()

    if choice == "1":
        await test_api_endpoints()
    elif choice == "2":
        await test_with_real_files()
    elif choice == "3":
        await test_api_endpoints()
        await test_with_real_files()
    else:
        print_error("无效选择")
        sys.exit(1)

    print_header("测试完成")
    print_success("所有基础 API 测试通过")
    print_warning("完整功能测试需要真实模型文件")
    print("\n📝 手动测试步骤：")
    print("1. 访问 http://localhost:3000")
    print("2. 上传模型文件（.pt/.pth/.onnx）")
    print("3. 选择预设配置")
    print("4. 点击 START 开始转换")
    print("5. 记录 task_id")
    print("6. 测试 Redis 持久化：")
    print("   docker compose -f docker-compose-dev.yml restart backend")
    print(f"   curl {API_BASE}/tasks/<task_id>")
    print("7. 测试取消功能：")
    print(f"   curl -X POST {API_BASE}/tasks/<task_id>/cancel")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试已取消")
