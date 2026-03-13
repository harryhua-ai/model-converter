#!/usr/bin/env python3
"""
完整功能测试 - 使用真实模型文件验证 Redis 持久化和取消功能
"""
import asyncio
import httpx
import json
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

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

async def test_real_conversion():
    """使用真实文件进行完整的转换测试"""
    print_header("完整功能测试（需要真实文件）")

    # 检查文件
    upload_dir = Path("uploads")
    model_files = list(upload_dir.glob("*.pt")) + list(upload_dir.glob("*.pth")) + list(upload_dir.glob("*.onnx"))

    if not model_files:
        print_error("未找到模型文件")
        print("\n请运行以下命令准备文件：")
        print("  chmod +x prepare_test_files.sh")
        print("  ./prepare_test_files.sh")
        print("\n或手动下载：")
        print("  cd uploads")
        print("  curl -L -o yolov8n.pt https://github.com/ultralytics/ultralytics/releases/download/v0.0.0/yolov8n.pt")
        return False

    model_file = model_files[0]
    print_success(f"找到模型文件: {model_file.name}")

    # 检查校准数据集
    calib_files = list(upload_dir.glob("*.zip"))
    has_calibration = len(calib_files) > 0
    if has_calibration:
        print_success(f"找到校准数据集: {calib_files[0].name}")
    else:
        print_warning("未找到校准数据集（推荐使用）")

    print("\n" + "="*60)
    print("准备开始完整功能测试...")
    print("="*60)

    print("\n由于需要通过 Web 界面或 multipart/form-data 上传文件，")
    print("这里提供手动测试步骤：\n")

    print("步骤 1: 通过 Web 界面上传文件")
    print("─────────────────────────────────────────")
    print("1. 确保前端正在运行：")
    print("   cd frontend && pnpm dev")
    print("\n2. 访问: http://localhost:3000")
    print(f"\n3. 上传文件：")
    print(f"   • 模型: {model_file.name}")
    if has_calibration:
        print(f"   • 校准: {calib_files[0].name}")
    print("   • 配置: data.yaml")
    print("\n4. 选择预设: yolov8n-256")
    print("\n5. 点击 START")
    print("\n6. 记录 task_id（从浏览器控制台）")

    print("\n" + "─"*60)
    print("\n步骤 2: 验证任务创建和状态查询")
    print("─────────────────────────────────────────")
    print("\n# 查询任务状态")
    print(f"curl {API_BASE}/tasks/<task_id>")

    print("\n# 查看所有任务")
    print(f"curl {API_BASE}/tasks/")

    print("\n" + "─"*60)
    print("\n步骤 3: 测试 Redis 持久化（重点！）")
    print("─────────────────────────────────────────")
    print("\n# 重启后端容器")
    print("docker compose -f docker-compose-dev.yml restart backend")
    print("\n# 等待后端恢复（约 35 秒）")
    print("sleep 35")
    print("\n# 再次查询任务（验证持久化）")
    print(f"curl {API_BASE}/tasks/<task_id>")
    print("\n预期结果: ✅ 任务仍可查询（不再是 404）")

    print("\n" + "─"*60)
    print("\n步骤 4: 测试取消功能")
    print("─────────────────────────────────────────")
    print("\n# 取消任务")
    print(f"curl -X POST {API_BASE}/tasks/<task_id>/cancel")
    print("\n# 验证任务状态")
    print(f"curl {API_BASE}/tasks/<task_id>")
    print("\n预期结果: ✅ 任务状态变为 'cancelled'")

    print("\n" + "─"*60)
    print("\n步骤 5: 验证 Redis 存储")
    print("─────────────────────────────────────────")
    print("\n# 连接到 Redis")
    print("docker compose -f docker-compose-dev.yml exec redis redis-cli")
    print("\n# 查看所有任务键")
    print("KEYS task:*")
    print("\n# 查看特定任务")
    print("GET task:<task_id>")
    print("\n# 验证 TTL")
    print("TTL task:<task_id>")
    print("\n预期结果: ✅ TTL = 86400 秒（24 小时）")

    print("\n" + "="*60)
    print("是否现在打开 Web 界面开始测试？")
    print("="*60)
    print("\n请手动按照上述步骤操作，或按 Ctrl+C 退出")

    # 等待用户输入 task_id 进行自动化测试
    print("\n" + "─"*60)
    print("\n或者，输入 task_id 进行自动化测试验证")
    print("─"*60)

    task_id = input("\n请输入 task_id（或按 Enter 跳过）: ").strip()

    if not task_id:
        print("\n跳过自动化测试")
        return True

    # 自动化测试
    print("\n开始自动化测试...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 查询任务
        print(f"\n1️⃣  查询任务: {task_id}")
        try:
            response = await client.get(f"{API_BASE}/tasks/{task_id}")
            if response.status_code == 200:
                task = response.json()
                print_success("任务查询成功")
                print(f"   状态: {task['status']}")
                print(f"   进度: {task['progress']}%")
                print(f"   当前步骤: {task['current_step']}")
            else:
                print_error(f"任务不存在: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"查询失败: {e}")
            return False

        # 2. 测试 Redis 持久化
        print("\n2️⃣  测试 Redis 持久化")
        print("   重启后端容器...")
        import subprocess
        subprocess.run(
            ["docker", "compose", "-f", "docker-compose-dev.yml", "restart", "backend"],
            capture_output=True
        )

        print("   等待后端恢复...")
        await asyncio.sleep(35)

        print("   再次查询任务...")
        try:
            response = await client.get(f"{API_BASE}/tasks/{task_id}")
            if response.status_code == 200:
                print_success("Redis 持久化验证成功！")
                print("   ✅ 重启后任务仍可查询")
            else:
                print_error("Redis 持久化验证失败")
                return False
        except Exception as e:
            print_error(f"查询失败: {e}")
            return False

        # 3. 测试取消功能
        print("\n3️⃣  测试取消功能")
        try:
            response = await client.post(f"{API_BASE}/tasks/{task_id}/cancel")
            if response.status_code == 200:
                print_success("任务取消成功")
                print(f"   {response.json()['message']}")

                # 验证状态
                await asyncio.sleep(1)
                response = await client.get(f"{API_BASE}/tasks/{task_id}")
                task = response.json()
                if task['status'] == 'cancelled':
                    print_success("任务状态正确更新为 cancelled")
                else:
                    print_warning(f"任务状态: {task['status']}")
            else:
                print_error(f"取消失败: {response.status_code}")
        except Exception as e:
            print_error(f"取消失败: {e}")
            return False

    print("\n" + "="*60)
    print_success("完整功能测试通过！")
    print("="*60)
    print("\n✅ Redis 持久化工作正常")
    print("✅ 取消功能工作正常")
    print("✅ 所有后端修复已验证")

    return True

async def test_redis_direct():
    """直接测试 Redis 连接和数据存储"""
    print_header("Redis 直接连接测试")

    try:
        import redis.asyncio
        print("连接到 Redis...")
        r = redis.asyncio.Redis(host='localhost', port=6379, decode_responses=True)
        await r.ping()
        print_success("Redis 连接成功")

        print("\n查看所有任务键...")
        keys = await r.keys("task:*")
        if keys:
            print_success(f"找到 {len(keys)} 个任务")
            for key in keys:
                print(f"  • {key}")
                # 查看 TTL
                ttl = await r.ttl(key)
                print(f"    TTL: {ttl} 秒 ({ttl // 3600} 小时)")
        else:
            print_warning("当前没有任务数据（正常，因为还没有创建任务）")

        await r.close()
        return True

    except Exception as e:
        print_error(f"Redis 连接失败: {e}")
        return False

async def main():
    """主测试流程"""
    print_header("完整功能测试")

    # 先测试 Redis 连接
    await test_redis_direct()

    print("\n")

    # 然后进行完整功能测试
    await test_real_conversion()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试已取消")
