# CLAUDE.md - model-converter Backend

NE301 模型转换工具后端服务 - 基于 FastAPI 的异步 Web 服务

## 项目概述

这是一个异步 Python Web 服务，负责处理模型上传、转换任务管理、进度监控和结果下载。核心功能是将 PyTorch YOLO 模型转换为 NE301 设备可用的 .bin 固件格式。

### 核心功能

- 模型文件上传和验证
- 异步模型转换（PyTorch → TFLite → C 模型 → .bin）
- 实时进度推送（WebSocket）
- 任务状态管理（内存存储 + 磁盘持久化）
- 转换结果下载

---

## 技术栈

### Web 框架
- **FastAPI 0.115** - 现代、高性能的 Web 框架
- **Uvicorn** - ASGI 服务器
- **Pydantic 2.10** - 数据验证和序列化

### 异步处理
- **asyncio** - 异步 I/O 和任务管理
- **BackgroundTasks** - 后台任务执行

### AI/ML 库
- **Ultralytics 8.3+** - YOLO 模型处理
- **PyTorch 2.4+** - 深度学习框架
- **TensorFlow 2.17+** - TFLite 转换
- **ONNX** - 模型格式支持

### 工具库
- **structlog** - 结构化日志
- **python-dotenv** - 环境变量管理
- **PyYAML** - YAML 配置解析
- **httpx** - 异步 HTTP 客户端

### 开发工具
- **pytest** - 测试框架
- **pytest-asyncio** - 异步测试支持
- **black** - 代码格式化
- **ruff** - 快速 Python linter
- **mypy** - 类型检查

---

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── api/                    # API 路由层
│   │   ├── __init__.py         # 路由聚合
│   │   ├── models.py           # 模型上传和下载 API
│   │   ├── tasks.py            # 任务查询和管理 API
│   │   └── presets.py          # 配置预设 API
│   ├── core/                   # 核心配置
│   │   ├── config.py           # 应用配置（Pydantic Settings）
│   │   └── logging.py          # 日志配置
│   ├── models/                 # 数据模型
│   │   └── schemas.py          # Pydantic 模型定义
│   ├── services/               # 业务逻辑层
│   │   ├── conversion.py      # 模型转换服务
│   │   └── task_manager.py    # 任务管理服务
│   └── workers/                # 后台任务（已弃用 Celery）
│       └── celery_app.py      # Celery 应用配置
├── tests/                      # 测试目录
│   ├── conftest.py             # pytest 配置
│   ├── test_api.py             # API 测试
│   └── test_conversion.py      # 转换服务测试
├── main.py                     # 应用入口
├── Dockerfile                  # Docker 镜像构建
├── requirements.txt            # Python 依赖
├── .env.example                # 环境变量模板
└── CLAUDE.md                   # 本文档
```

---

## 快速开始

### 环境要求

- Python 3.11+ (推荐 3.11)
- ST Edge AI 工具链（用于完整转换功能）
- NE301 项目路径（Model/ 和 Script/ 目录）

### 本地开发

```bash
# 1. 创建虚拟环境
cd backend
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置 NE301_PROJECT_PATH

# 4. 启动服务
python3 main.py
# 或使用 uvicorn：
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000

### Docker 运行

```bash
# 从项目根目录
cd model-converter

# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f backend
```

---

## 开发指南

### API 端点规范

所有 API 遵循 RESTful 规范：

```python
from fastapi import APIRouter, HTTPException
from app.services.task_manager import get_task_manager
from app.models.schemas import ConversionTask

router = APIRouter()
task_manager = get_task_manager()

@router.get("/{task_id}", response_model=ConversionTask)
async def get_task(task_id: str) -> ConversionTask:
    """
    获取任务详情

    Args:
        task_id: 任务 ID

    Returns:
        ConversionTask: 任务详情

    Raises:
        HTTPException: 任务不存在时返回 404
    """
    task = await task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task
```

### 使用全局单例

**重要**：服务层必须使用全局单例，避免数据不一致：

```python
# ❌ 错误：每个模块创建独立实例
from app.services.task_manager import TaskManager
task_manager = TaskManager()

# ✅ 正确：使用全局单例
from app.services.task_manager import get_task_manager
task_manager = get_task_manager()
```

### 异步编程规范

所有 I/O 操作必须使用异步：

```python
# ❌ 错误：同步 I/O
def get_task(task_id: str):
    task = db.query(task_id)  # 阻塞
    return task

# ✅ 正确：异步 I/O
async def get_task(task_id: str):
    task = await async_db.query(task_id)
    return task
```

### 错误处理

使用 HTTPException 返回错误：

```python
from fastapi import HTTPException

if not task:
    raise HTTPException(
        status_code=404,
        detail="任务不存在"
    )
```

### 日志记录

使用 structlog 记录结构化日志：

```python
import structlog

logger = structlog.get_logger(__name__)

logger.info(
    "任务创建",
    task_id=task_id,
    filename=file.filename,
    file_size=file.size
)
```

---

## 架构说明

### 分层架构

```
┌─────────────────────────────────────────┐
│         API Layer (FastAPI)             │
│  ┌──────────┐    ┌──────────────────┐    │
│  |  Routes  │───▶│  Pydantic Models │    │
│  └──────────┘    └──────────────────┘    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│       Service Layer (Business Logic)    │
│  ┌────────────────┐  ┌────────────────┐ │
│  │ TaskManager    │  │ ConversionService│ │
│  │ - 任务 CRUD     │  │ - 模型转换      │ │
│  │ - 进度更新      │  │ - 文件处理      │ │
│  │ - 订阅管理      │  │ - 打包下载      │ │
│  └────────────────┘  └────────────────┘ │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         Storage Layer                  │
│  ┌───────────────────────────────────┐  │
│  │  Memory (dict) + Disk (JSON)      │  │
│  │  - tasks.json                    │  │
│  │  - uploads/                      │  │
│  │  - temp/                         │  │
│  │  - outputs/                      │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### 数据流

**上传和转换流程**：

```
用户上传 → API (models.py)
    ↓
TaskManager.create_task()
    ↓
保存到内存和磁盘 (tasks.json)
    ↓
启动后台任务 (BackgroundTasks)
    ↓
ConversionService.convert_model()
    ├─ 验证模型 (5%)
    ├─ PyTorch → TFLite (10-30%)
    ├─ TFLite → C 模型 (30-60%)
    ├─ 生成配置 (60-80%)
    └─ 打包 ZIP (80-100%)
    ↓
更新任务状态
    ↓
WebSocket 推送进度
    ↓
前端显示实时进度
```

---

## 核心 API 端点

### 模型管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/models/upload` | POST | 上传模型并创建转换任务 |
| `/api/v1/models/download/{task_id}` | GET | 下载转换结果 |
| `/api/v1/presets` | GET | 获取配置预设列表 |

### 任务管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/tasks` | GET | 获取任务列表 |
| `/api/v1/tasks/{task_id}` | GET | 获取任务详情 |
| `/api/v1/tasks/{task_id}/cancel` | POST | 取消任务 |
| `/api/v1/tasks/{task_id}` | DELETE | 删除任务 |

### WebSocket

| 端点 | 说明 |
|------|------|
| `/ws/tasks/{task_id}/progress` | 实时进度推送 |

---

## 服务层详解

### TaskManager

任务管理器，负责任务的 CRUD 和状态管理：

```python
from app.services.task_manager import get_task_manager

task_manager = get_task_manager()

# 创建任务
task = await task_manager.create_task(
    task_id=task_id,
    config=config,
    filename=file.filename
)

# 更新进度
await task_manager.update_task(
    task_id=task_id,
    progress=50,
    current_step="PyTorch → TFLite 转换中..."
)

# 获取任务
task = await task_manager.get_task(task_id)
```

**存储策略**：
- 内存：快速访问
- 磁盘：持久化（`temp/tasks.json`）
- 启动时自动从磁盘恢复

### ConversionService

模型转换服务，执行完整的转换流程：

```python
from app.services.conversion import ConversionService

service = ConversionService()

await service.convert_model(
    task_id=task_id,
    input_path="/path/to/model.pt",
    calibration_dataset_path="/path/to/coco8.zip",
    class_yaml_path="/path/to/data.yaml",
    config=conversion_config
)
```

**转换流程**：
1. 验证模型文件
2. PyTorch → TFLite (Ultralytics)
3. TFLite → network_rel.bin (ST Edge AI)
4. 生成 model_config.json
5. 打包为 ZIP 文件

---

## 配置管理

### 环境变量

在 `.env` 文件中配置：

```bash
# API 配置
API_PREFIX=/api/v1
HOST=0.0.0.0
PORT=8000
DEBUG=true

# 文件存储
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=524288000  # 500MB
TEMP_DIR=./temp
OUTPUT_DIR=./outputs

# NE301 项目路径
NE301_PROJECT_PATH=/workspace  # Docker
# NE301_PROJECT_PATH=/path/to/ne301  # 本地

# ST Edge AI
STEDGEAI_PATH=/opt/stedgeai

# 日志
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Pydantic Settings

使用 `pydantic-settings` 管理配置：

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # model_config = SettingsConfigDict(env_file=".env")

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 数据模型

### ConversionTask

任务模型定义：

```python
from app.models.schemas import ConversionTask, TaskStatus

task = ConversionTask(
    task_id="uuid",
    status=TaskStatus.PROCESSING,
    progress=50,
    current_step="TFLite → C 模型",
    config=ConversionConfig(...),
    error_message=None,
    output_filename=None,
    created_at="2026-03-11T14:00:00",
    updated_at="2026-03-11T14:05:00"
)
```

### ConversionConfig

转换配置模型：

```python
from app.models.schemas import ConversionConfig, ModelType

config = ConversionConfig(
    model_name="yolov8n_480",
    model_type=ModelType.YOLO_DETECTION,
    input_width=480,
    input_height=480,
    quantization_type="int8",
    postprocess_type="pp_od_yolo_v8_ui",
    num_classes=80,
    class_names=["person", "car", ...],
    confidence_threshold=0.25,
    iou_threshold=0.45
)
```

---

## 测试

### 运行测试

```bash
# 所有测试
pytest

# 单个文件
pytest tests/test_api.py

# 带覆盖率
pytest --cov=app --cov-report=html

# 查看详细输出
pytest -v
```

### 编写测试

```python
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_upload_model():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 准备测试数据
        files = {"file": open("test.pt", "rb")}
        data = {"config": json.dumps({...})}

        # 发送请求
        response = await client.post("/api/v1/models/upload", files=files, data=data)

        # 验证结果
        assert response.status_code == 200
        assert "task_id" in response.json()
```

---

## 部署

### Docker 部署

使用 Dockerfile 构建镜像：

```bash
# 构建镜像
docker build -t ne301-backend:latest .

# 运行容器
docker run -p 8000:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/outputs:/app/outputs \
  -v /path/to/ne301/Model:/workspace/Model:ro \
  -v /path/to/ne301/Script:/workspace/Script:ro \
  -e NE301_PROJECT_PATH=/workspace \
  ne301-backend:latest
```

### 生产环境配置

```bash
# 使用 gunicorn + uvicorn workers
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### 健康检查

```bash
curl http://localhost:8000/health

# 返回
# {"status":"healthy","service":"YOLO 模型转换工具","version":"2.0.0"}
```

---

## 常见任务

### 添加新 API 端点

1. 在 `app/api/` 创建或编辑路由文件
2. 定义路由函数：
```python
from fastapi import APIRouter
from app.services.task_manager import get_task_manager

router = APIRouter()
task_manager = get_task_manager()

@router.get("/custom")
async def custom_endpoint():
    # 实现逻辑
    pass
```
3. 在 `app/api/__init__.py` 注册路由：
```python
from app.api import custom_router
api_router.include_router(custom_router, prefix="/custom")
```

### 添加新转换配置

1. 在 `app/api/presets.py` 添加预设：
```python
PRESETS = {
    "yolov8n-256": {...},
    "yolov8n-480": {...},
    "custom-model": {
        "name": "Custom Model",
        "input_width": 320,
        "input_height": 320,
        ...
    }
}
```

### 修改转换流程

编辑 `app/services/conversion.py` 中的 `ConversionService`：

```python
async def _convert_to_tflite(self, ...):
    # 自定义 TFLite 转换逻辑
    pass
```

---

## 故障排查

### 常见问题

**Q: 转换失败，提示 "ML 库未安装"**
```bash
# 确认依赖已安装
pip list | grep -E "torch|tensorflow|ultralytics"
```

**Q: ST Edge AI 相关错误**
```bash
# 检查环境变量
echo $STEDGEAI_PATH

# 验证工具可用
which stedgeai
```

**Q: 任务查询返回 404**
```python
# 确认使用 get_task_manager() 单例
# 而不是 TaskManager()
```

**Q: WebSocket 连接失败**
```bash
# 检查代理配置（开发环境）
# vite.config.ts 应包含：
proxy: {
  '/ws': {
    target: 'ws://localhost:8000',
    ws: true
  }
}
```

### 调试技巧

```python
# 启用调试日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 使用 structlog
logger.info("调试信息", task_id=task_id, data={...})

# 使用 pdb 断点
import pdb; pdb.set_trace()
```

---

## 性能优化

### 异步并发

```python
import asyncio

async def process_multiple_tasks(task_ids):
    tasks = [convert_model(tid) for tid in task_ids]
    await asyncio.gather(*tasks)
```

### 内存管理

```python
# 及时清理临时文件
import shutil

shutil.rmtree(work_dir)

# 使用上下文管理器
async with aiofiles.open(path, 'wb') as f:
    await f.write(data)
```

---

## 安全注意事项

### 文件上传验证

```python
# 验证文件扩展名
file_ext = os.path.splitext(filename)[1].lower()
if file_ext not in settings.ALLOWED_MODEL_EXTENSIONS:
    raise HTTPException(status_code=400, detail="不支持的文件格式")

# 验证文件大小
file_size = os.path.getsize(upload_path)
if file_size > settings.MAX_UPLOAD_SIZE:
    os.remove(upload_path)
    raise HTTPException(status_code=400, detail="文件过大")
```

### 路径遍历防护

```python
# 验证任务 ID 格式
import uuid
try:
    uuid.UUID(task_id)
except ValueError:
    raise HTTPException(status_code=400, detail="无效的任务 ID")

# 安全地处理文件路径
safe_path = os.path.normpath(user_path)
if not safe_path.startswith(settings.UPLOAD_DIR):
    raise HTTPException(status_code=400, detail="非法的路径")
```

---

## 相关资源

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Pydantic 文档](https://docs.pydantic.dev/)
- [Ultralytics 文档](https://docs.ultralytics.com/)
- [ST Edge AI 文档](https://www.st.com/en/development-tools/stedgeai-core.html)

---

**最后更新**: 2026-03-11
**版本**: 2.0.0 (简化版 - 无 Redis/Celery)
