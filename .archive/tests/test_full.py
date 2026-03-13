#!/usr/bin/env python3
"""
完整功能测试 - 使用真实文件
自动上传文件、创建任务、验证 Redis 持久化
"""
import asyncio
import httpx
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"

UPLOAD_DIR = Path("uploads")
MODEL_FILE = UPLOAD_DIR / "best.pt"
CALIB_FILE = UPLOAD_DIR / "calibration.zip"
CONFIG_FILE = UPLOAD_DIR / "data.yaml"

def print_success(msg):
    print(f"{GREEN}✅ {msg}{NC}")

def print_error(msg):
    print(f"{RED}❌ {msg}{NC}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{NC}")

def print_info(msg):
    print(f"{BLUE}ℹ️  {msg}{NC}")

def print_header(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}\n")

async def create_conversion_task():
    """创建转换任务"""
    print_header("步骤 1: 创建转换任务")

    # 检查文件
    if not MODEL_FILE.exists():
        print_error(f"模型文件不存在: {MODEL_FILE}")
        return None

    print_success(f"模型文件: {MODEL_FILE} ({MODEL_FILE.stat().st_size / 1024 / 1024:.1f} MB)")
    if CALIB_FILE.exists():
        print_success(f"校准数据: {CALIB_FILE} ({CALIB_FILE.stat().st_size / 1024 / 1024:.1f} MB)")
    if CONFIG_FILE.exists():
        print_success(f"配置文件: {CONFIG_FILE}")

    # 准备上传
    print_info("准备上传文件...")

    async with httpx.AsyncClient(timeout=300.0) as client:
        # 读取配置
        with open(CONFIG_FILE, 'r') as f:
            yaml_content = f.read()

        # 读取类别信息
        import yaml
        yaml_data = yaml.safe_load(yaml_content)
        num_classes = yaml_data.get('nc', 80)
        class_names = yaml_data.get('names', [])

        print_info(f"类别数量: {num_classes}")
        print_info(f"类别名称: {class_names[:3]}..." if len(class_names) > 3 else f"类别名称: {class_names}")

        # 构建配置 JSON
        config_json = json.dumps({
            "model_name": "yolov8n_256",
            "model_type": "YOLOv8",
            "model_version": "1.0.0",
            "input_width": 256,
            "input_height": 256,
            "input_data_type": "uint8",
            "color_format": "RGB888_YUV444_1",
            "quantization_type": "int8",
            "quantization_mode": "per_channel",
            "postprocess_type": "pp_od_yolo_v8_ui",
            "num_classes": num_classes,
            "class_names": class_names,
            "confidence_threshold": 0.25,
            "iou_threshold": 0.45,
            "max_detections": 100,
            "total_boxes": 1344,
            "mean": [0.0, 0.0, 0.0],
            "std": [255.0, 255.0, 255.0],
            "use_custom_calibration": True,
            "calibration_dataset_filename": "calibration.zip"
        })

        # 准备 multipart 上传
        files = {
            'file': open(MODEL_FILE, 'rb'),
        }

        data = {
            'config': config_json,
        }

        if CALIB_FILE.exists():
            files['calibration_dataset'] = open(CALIB_FILE, 'rb')

        if CONFIG_FILE.exists():
            files['class_yaml'] = open(CONFIG_FILE, 'rb')

        print_info("上传文件到后端...")

        try:
            # 发送请求
            response = await client.post(
                f"{API_BASE}/models/upload",  # 修复：使用 /models/upload
                files=files,
                data={'config': config_json}
            )

            if response.status_code == 200:
                result = response.json()
                task_id = result['task_id']
                print_success(f"任务创建成功！")
                print_info(f"Task ID: {task_id}")
                print_info(f"文件名: {result['filename']}")
                print_info(f"文件大小: {result['file_size'] / 1024 / 1024:.1f} MB")
                return task_id
            else:
                print_error(f"上传失败: {response.status_code}")
                print_error(f"错误: {response.text}")
                return None

        except Exception as e:
            print_error(f"上传异常: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            # 关闭文件
            for f in files.values():
                if hasattr(f, 'close'):
                    f.close()

async def verify_task_creation(task_id):
    """验证任务创建和状态查询"""
    print_header("步骤 2: 验证任务创建")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 查询任务
        try:
            response = await client.get(f"{API_BASE}/tasks/{task_id}")
            if response.status_code == 200:
                task = response.json()
                print_success("任务查询成功")
                print_info(f"状态: {task['status']}")
                print_info(f"进度: {task['progress']}%")
                print_info(f"当前步骤: {task['current_step']}")
                return True
            else:
                print_error(f"查询失败: {response.status_code}")
                print_error(f"错误: {response.text}")
                return False
        except Exception as e:
            print_error(f"查询异常: {e}")
            return False

async def test_redis_persistence(task_id):
    """测试 Redis 持久化（核心测试）"""
    print_header("步骤 3: 测试 Redis 持久化")

    import subprocess

    # 第一次查询
    print_info("第一次查询任务...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{API_BASE}/tasks/{task_id}")
            if response.status_code == 200:
                print_success("✓ 任务存在")
            else:
                print_error(f"✗ 任务不存在: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"查询失败: {e}")
            return False

    # 重启后端容器
    print_warning("重启后端容器...")
    print_info("这可能需要 30-40 秒...")

    result = subprocess.run(
        ["docker", "compose", "-f", "docker-compose-dev.yml", "restart", "backend"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print_error(f"重启失败: {result.stderr}")
        return False

    # 等待后端恢复
    print_info("等待后端恢复健康状态...")
    await asyncio.sleep(35)

    # 检查后端状态
    result = subprocess.run(
        ["docker", "compose", "-f", "docker-compose-dev.yml", "ps", "backend"],
        capture_output=True,
        text=True
    )

    if "healthy" not in result.stdout:
        print_warning("后端可能还未完全就绪")
        await asyncio.sleep(10)

    # 第二次查询（验证持久化）
    print_info("第二次查询任务（验证 Redis 持久化）...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{API_BASE}/tasks/{task_id}")
            if response.status_code == 200:
                task = response.json()
                print_success("✅ Redis 持久化验证成功！")
                print_success("✓ 重启后任务仍可查询（不再是 404！）")
                print_info(f"任务状态: {task['status']}")
                print_info(f"任务进度: {task['progress']}%")
                return True
            else:
                print_error(f"✗ 查询失败: {response.status_code}")
                print_error(f"这表示 Redis 持久化可能有问题")
                return False
        except Exception as e:
            print_error(f"查询异常: {e}")
            return False

async def test_cancel_task(task_id):
    """测试取消功能"""
    print_header("步骤 4: 测试取消功能")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 取消任务
        print_info("取消任务...")
        try:
            response = await client.post(f"{API_BASE}/tasks/{task_id}/cancel")
            if response.status_code == 200:
                result = response.json()
                print_success(f"✓ {result['message']}")
            else:
                print_error(f"取消失败: {response.status_code}")
                print_error(f"错误: {response.text}")
                return False
        except Exception as e:
            print_error(f"取消异常: {e}")
            return False

        # 验证状态
        await asyncio.sleep(1)
        print_info("验证任务状态...")
        try:
            response = await client.get(f"{API_BASE}/tasks/{task_id}")
            if response.status_code == 200:
                task = response.json()
                if task['status'] == 'cancelled':
                    print_success("✅ 任务状态正确更新为 'cancelled'")
                    return True
                else:
                    print_warning(f"任务状态: {task['status']}")
                    return False
        except Exception as e:
            print_error(f"查询失败: {e}")
            return False

async def verify_redis_storage(task_id):
    """验证 Redis 存储"""
    print_header("步骤 5: 验证 Redis 存储")

    try:
        import redis.asyncio
        print_info("连接到 Redis...")
        r = redis.asyncio.Redis(host='localhost', port=6379, decode_responses=True)
        await r.ping()
        print_success("✓ Redis 连接成功")

        # 查看任务数据
        print_info("查看任务数据...")
        task_key = f"task:{task_id}"
        task_data = await r.get(task_key)

        if task_data:
            print_success("✓ 任务数据存储在 Redis 中")
            task_dict = json.loads(task_data)
            print_info(f"Task ID: {task_dict.get('task_id')}")
            print_info(f"Status: {task_dict.get('status')}")
            print_info(f"Progress: {task_dict.get('progress')}%")

            # 查看 TTL
            ttl = await r.ttl(task_key)
            hours = ttl // 3600
            print_success(f"✓ TTL = {ttl} 秒 ({hours} 小时)")

            if ttl > 86000:  # 接近 24 小时
                print_success("✅ TTL 设置正确（24 小时）")
            else:
                print_warning(f"TTL 可能不是预期的 24 小时")

            await r.close()
            return True
        else:
            print_error("✗ 任务数据未找到")
            await r.close()
            return False

    except Exception as e:
        print_error(f"Redis 连接失败: {e}")
        return False

async def main():
    """主测试流程"""
    print_header("完整功能测试 - 使用真实文件")

    print(f"测试文件:")
    print(f"  • 模型: {MODEL_FILE}")
    print(f"  • 校准: {CALIB_FILE}")
    print(f"  • 配置: {CONFIG_FILE}")
    print()

    # 创建任务
    task_id = await create_conversion_task()

    if not task_id:
        print_error("任务创建失败，无法继续测试")
        return

    print(f"\n{BLUE}═══ 获取 task_id: {task_id} ═══{NC}\n")

    # 等待一下，让任务开始处理
    await asyncio.sleep(2)

    # 验证任务创建
    if not await verify_task_creation(task_id):
        print_error("任务验证失败")
        return

    # 测试 Redis 持久化
    if not await test_redis_persistence(task_id):
        print_error("Redis 持久化测试失败")
        return

    # 测试取消功能
    if not await test_cancel_task(task_id):
        print_error("取消功能测试失败")
        return

    # 验证 Redis 存储
    if not await verify_redis_storage(task_id):
        print_error("Redis 存储验证失败")
        return

    # 所有测试通过
    print_header("✨ 测试完成")
    print_success("✅ 任务创建成功")
    print_success("✅ 任务查询成功")
    print_success("✅ Redis 持久化验证通过（重启后任务仍存在）")
    print_success("✅ 取消功能正常")
    print_success("✅ Redis 存储验证通过")
    print()
    print("="*60)
    print_success("所有测试通过！后端修复已完全验证")
    print("="*60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试已取消")
    except Exception as e:
        print_error(f"测试异常: {e}")
        import traceback
        traceback.print_exc()
