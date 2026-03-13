# NE301 Model Converter

PyTorch 模型转换为 NE301 设备可用 .bin 文件的 Web 工具。

## 项目概述

NE301 Model Converter 是一个零代码的端到端模型转换平台，支持将 PyTorch 模型自动转换为 NE301 边缘设备可用的 .bin 格式。通过 Web 界面操作，无需理解底层转换流程。

**核心特性**:
- ✅ 零代码操作 - 界面化操作，无需理解底层流程
- ✅ 端到端自动化 - PyTorch → 量化 → NE301 .bin 全自动
- ✅ 实时反馈 - WebSocket 推送转换进度
- ✅ 跨平台支持 - macOS / Linux / Windows

**技术栈**:
- **前端**: Preact 10 + TypeScript + Tailwind CSS + Vite
- **后端**: Python 3.11/3.12 + FastAPI + WebSocket + Docker
- **ML 工具**:
  - PyTorch 2.4.0（模型导出）
  - Ultralytics 8.3.0（YOLO 模型处理）
  - TensorFlow 2.16.2（TFLite 转换与量化）
  - Hydra 1.3.0（配置管理）
  - OpenCV 4.8.0（图像处理）
- **ST 量化**: STMicroelectronics 官方 TFLite 量化脚本
- **测试**:
  - pytest 8.3.4（后端单元测试）
  - Playwright（E2E 测试）
  - httpx 0.27.0（异步 HTTP 测试）

---

## 开发环境设置

### 前置要求

- **Python**: 3.11 或 3.12（不支持 3.14）
- **Node.js**: 18+ (推荐 20+)
- **Docker Desktop**: 必须运行中
- **Git**: 版本控制

### 环境准备

```bash
# 1. 克隆仓库
git clone <repository-url>
cd model-converter

# 2. 创建并激活 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装后端依赖
pip install -r backend/requirements.txt

# 4. 配置环境变量（可选）
cp backend/.env.example backend/.env
# 编辑 backend/.env 设置自定义配置

# 5. 安装前端依赖
cd frontend
npm install
cd ..

# 6. 验证 Docker 运行
docker --version
docker ps
```

### 环境变量配置

创建 `backend/.env` 文件（可选）：

```env
# Docker 配置
NE301_DOCKER_IMAGE=camthink/ne301-dev:latest
NE301_PROJECT_PATH=/app/ne301
CONTAINER_NAME=model-converter-api

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=False

# 日志配置
LOG_LEVEL=INFO

# 文件路径配置
UPLOAD_DIR=./uploads
TEMP_DIR=./temp
OUTPUT_DIR=./outputs
MAX_UPLOAD_SIZE=524288000  # 500MB
```

### 启动开发服务器

**后端**:
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

**前端**:
```bash
cd frontend
npm run dev
```

**访问应用**: http://localhost:8000

---

## 项目结构

```
model-converter/
├── backend/                    # 后端代码
│   ├── app/                    # FastAPI 应用
│   │   ├── main.py            # 应用入口（生命周期管理）
│   │   ├── api/               # API 路由
│   │   │   ├── convert.py     # 转换 API（支持校准数据集）
│   │   │   ├── tasks.py       # 任务管理 API
│   │   │   ├── setup.py       # 设置 API
│   │   │   └── websocket.py   # WebSocket 通信
│   │   ├── core/              # 核心业务逻辑
│   │   │   ├── config.py           # 配置管理（pydantic-settings）
│   │   │   ├── converter.py       # 模型转换器编排
│   │   │   ├── docker_adapter.py  # Docker 工具链适配器
│   │   │   ├── task_manager.py    # 任务管理器（单例模式）
│   │   │   └── environment.py     # 环境检测
│   │   └── models/            # 数据模型
│   │       └── schemas.py     # Pydantic 模型
│   ├── tools/                 # ST 量化工具
│   │   └── quantization/      # TFLite 量化脚本
│   │       ├── tflite_quant.py       # ST 官方量化脚本
│   │       └── user_config_quant.yaml # Hydra 配置
│   ├── tests/                 # 测试代码
│   │   ├── test_convert_api.py      # 转换 API 测试
│   │   ├── test_converter.py        # 转换器测试
│   │   ├── test_docker_adapter.py   # Docker 适配器测试
│   │   ├── test_task_manager.py     # 任务管理器测试
│   │   ├── test_websocket.py        # WebSocket 测试
│   │   ├── test_setup_api.py        # 设置 API 测试
│   │   └── integration/             # 集成测试
│   │       └── test_real_conversion.py # 真实转换流程测试
│   ├── Dockerfile              # 容器化部署
│   ├── requirements.txt        # Python 依赖
│   ├── pytest.ini             # Pytest 配置
│   └── .env.example           # 环境变量示例
├── frontend/                  # 前端代码
│   ├── src/
│   │   ├── main.tsx          # 应用入口
│   │   ├── App.tsx           # 根组件
│   │   ├── pages/            # 页面组件
│   │   ├── components/       # UI 组件
│   │   │   └── upload/       # 上传组件模块
│   │   │       ├── index.ts           # 组件导出
│   │   │       ├── ModelUploadArea.tsx     # 模型上传
│   │   │       ├── ClassYamlUploadArea.tsx # YAML 上传
│   │   │       └── CalibrationUploadArea.tsx # 校准数据上传
│   │   ├── services/         # API 服务
│   │   ├── hooks/            # 自定义 Hooks
│   │   ├── store/            # 状态管理 (Zustand)
│   │   ├── types/            # TypeScript 类型
│   │   └── utils/            # 工具函数
│   ├── package.json
│   ├── vite.config.ts        # Vite 配置
│   └── tailwind.config.js    # Tailwind 配置
├── tests/                     # E2E 测试
│   └── e2e/                  # Playwright E2E 测试
│       ├── conversion.spec.ts        # 转换流程测试
│       └── screenshots/              # 测试截图
├── scripts/                   # 部署脚本
│   ├── start.sh              # Linux/macOS 启动
│   ├── start.bat             # Windows 启动
│   └── init-ne301.sh         # NE301 项目初始化
├── ne301/                     # NE301 相关资源
├── docs/                      # 项目文档
├── .archive/                  # 归档代码
├── docker-compose.yml         # 生产环境部署
├── docker-compose.dev.yml     # 开发环境部署
├── deploy.sh                  # 一键部署脚本
├── playwright.config.ts       # Playwright 配置
├── CLAUDE.md                  # 项目文档（本文件）
├── README.md                  # 项目说明
├── README.docker.md           # Docker 部署指南
└── CACHE_CLEAR_GUIDE.md       # 缓存清除指南
```

---

## 技术架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Preact)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │  Pages   │  │Components│  │ Services │  │  Store   │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/WebSocket
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ API Layer│  │WebSocket │  │Task Mgr  │  │ Converter│    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└────────────────────┬────────────────────────────────────────┘
                     │ Docker SDK
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Docker Container (NE301)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ PyTorch  │→│  ONNX    │→│ TFLite   │→│ NE301 .bin │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 后端架构

**分层设计**:
- **API 层** (`app/api/`): RESTful API 和 WebSocket 端点
- **业务逻辑层** (`app/core/`): 核心业务逻辑
  - `config.py`: 使用 pydantic-settings 管理配置
  - `converter.py`: 模型转换流程编排
  - `docker_adapter.py`: Docker 工具链适配器（参考 AIToolStack）
  - `task_manager.py`: 异步任务管理（单例模式）
- **数据模型层** (`app/models/`): Pydantic 数据验证模型
- **量化工具层** (`tools/quantization/`): ST 官方 TFLite 量化脚本

**关键设计模式**:
- **异步处理**: 使用 `asyncio` 处理长时间运行的转换任务
- **WebSocket 推送**: 实时推送转换进度和日志
- **任务队列**: 基于内存的任务管理器（单例模式）
- **Docker 化架构**: 完全容器化的转换流程
  - API 容器：FastAPI + PyTorch → TFLite → TFLite 量化
  - NE301 容器：量化 TFLite → NE301 .bin
- **配置管理**: 使用 pydantic-settings 从环境变量加载
- **参考 AIToolStack**: 基于成熟的 camthink-ai/AIToolStack 架构

### 前端架构

**技术栈**:
- **Preact 10**: 轻量级 React 替代方案
- **TypeScript**: 类型安全
- **Tailwind CSS**: 原子化 CSS
- **Zustand**: 轻量级状态管理
- **@preact/signals**: 响应式状态

**状态管理**:
- 使用 Zustand 管理全局状态
- 使用 Signals 管理组件级响应式状态
- 通过 WebSocket 实时更新转换状态

---

## 开发工作流

### 后端开发

```bash
cd backend

# 激活虚拟环境
source ../venv/bin/activate

# 运行测试
pytest

# 运行测试（带覆盖率）
pytest --cov=app --cov-report=term-missing

# 启动开发服务器
python -m uvicorn app.main:app --reload --port 8000

# 代码格式化
black app/
isort app/

# 类型检查
mypy app/
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览构建结果
npm run preview

# 类型检查
npm run type-check
```

### Git 工作流

**分支策略**:
- `main`: 主分支，生产代码
- `feature/*`: 功能分支
- `bugfix/*`: 修复分支

**提交规范**:
```
<type>: <description>

Types: feat, fix, refactor, docs, test, chore, perf, ci
```

**创建 PR**:
1. 从 `main` 创建功能分支
2. 开发并测试
3. 提交 PR
4. 代码审查通过后合并

---

## 编码规范

### Python (后端)

**遵循标准**:
- PEP 8 代码风格
- 使用 type annotations
- 不可变数据结构 (dataclass frozen=True)
- 错误处理：明确包装错误并提供上下文

**工具**:
- **black**: 代码格式化
- **isort**: 导入排序
- **ruff**: 代码检查
- **mypy**: 类型检查

**示例**:
```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class ConversionTask:
    """转换任务数据模型"""
    task_id: str
    model_name: str
    status: str
    progress: int = 0
    error: Optional[str] = None

def convert_model(task_id: str) -> ConversionResult:
    """转换模型到 NE301 格式"""
    try:
        # 业务逻辑
        result = _do_conversion(task_id)
        return result
    except Exception as e:
        raise RuntimeError(f"转换失败: {task_id}") from e
```

### TypeScript (前端)

**遵循标准**:
- 不可变更新（使用 spread operator）
- Zod 进行输入验证
- 避免在 production 代码中使用 console.log
- 使用 async/await 处理异步操作

**示例**:
```typescript
// 不可变更新
function updateTask(task: Task, progress: number): Task {
  return {
    ...task,
    progress,
    updatedAt: Date.now()
  }
}

// 输入验证
import { z } from 'zod'

const TaskSchema = z.object({
  taskId: z.string().uuid(),
  modelName: z.string().min(1),
  status: z.enum(['pending', 'running', 'completed', 'failed'])
})

// API 调用
async function fetchTask(taskId: string): Promise<Task> {
  try {
    const response = await axios.get(`/api/tasks/${taskId}`)
    return TaskSchema.parse(response.data)
  } catch (error) {
    throw new Error(`获取任务失败: ${taskId}`)
  }
}
```

---

## API 文档

### REST API

**基础 URL**: `http://localhost:8000/api`

**端点**:

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/convert` | 上传并转换模型（支持校准数据集） |
| GET | `/tasks` | 获取所有任务列表 |
| GET | `/tasks/{task_id}` | 获取任务详情 |
| DELETE | `/tasks/{task_id}` | 删除任务 |
| GET | `/setup/check` | 检查环境状态 |
| GET | `/health` | 健康检查 |

**示例请求**:

```bash
# 上传模型（包含校准数据集）
curl -X POST http://localhost:8000/api/convert \
  -F "model=@model.pt" \
  -F 'config={"model_type": "yolov8", "input_size": 640, "num_classes": 80}' \
  -F "yaml_file=@classes.yaml" \
  -F "calibration_dataset=@calibration.zip"

# 获取任务状态
curl http://localhost:8000/api/tasks/{task_id}

# 检查环境
curl http://localhost:8000/api/setup/check
```

### WebSocket API

**连接**: `ws://localhost:8000/api/ws`

**消息格式**:
```typescript
{
  type: 'progress' | 'log' | 'status' | 'error',
  taskId: string,
  data: any
}
```

**示例**:
```typescript
const ws = new WebSocket('ws://localhost:8000/api/ws')

ws.onmessage = (event) => {
  const message = JSON.parse(event.data)

  if (message.type === 'progress') {
    console.log(`进度: ${message.data.progress}%`)
  }
}
```

---

## 测试指南

### 测试策略

**测试类型**:
1. **单元测试**: 测试独立函数和类（标记：`@pytest.mark.unit`）
2. **集成测试**: 测试 API 端点和组件交互（标记：`@pytest.mark.integration`）
3. **E2E 测试**: 测试完整的转换流程（Playwright）

**覆盖率要求**: 80%+

### 运行测试

```bash
# 后端测试
cd backend
pytest                                    # 运行所有测试
pytest --cov=app --cov-report=html       # 生成覆盖率报告
pytest tests/integration/                 # 只运行集成测试
pytest -m unit                            # 只运行单元测试
pytest -v                                 # 详细输出

# E2E 测试
cd model-converter
npm run test:e2e                          # 运行 Playwright E2E 测试

# 前端测试（如果配置）
cd frontend
npm run test
```

### 测试组织

**后端测试结构**:
```
backend/tests/
├── test_convert_api.py          # 转换 API 测试
├── test_converter.py            # 转换器测试
├── test_docker_adapter.py       # Docker 适配器测试
├── test_task_manager.py         # 任务管理器测试
├── test_websocket.py            # WebSocket 测试
├── test_setup_api.py            # 设置 API 测试
└── integration/
    └── test_real_conversion.py  # 真实转换流程测试
```

**E2E 测试结构**:
```
tests/e2e/
├── conversion.spec.ts           # 转换流程测试
└── screenshots/                 # 测试截图
```

### 测试示例

**后端单元测试**:
```python
# tests/test_converter.py
import pytest
from app.core.converter import ModelConverter

def test_converter_initialization():
    """测试转换器初始化"""
    converter = ModelConverter()
    assert converter is not None

@pytest.mark.asyncio
async def test_conversion_task():
    """测试转换任务创建"""
    task_id = await create_conversion_task(
        model_path="test.pt",
        preset="balanced"
    )
    assert task_id is not None
```

**集成测试**:
```python
# tests/integration/test_real_conversion.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_convert_endpoint():
    """测试转换 API 端点"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        with open("test_model.pt", "rb") as f:
            response = await client.post(
                "/api/convert",
                files={"model": f},
                data={"preset": "balanced"}
            )
        assert response.status_code == 200
```

---

## 部署指南

### Docker 容器化部署（推荐）

**架构说明**:
- **单容器部署**: 前端和后端集成在一个 Docker 镜像中
- **多阶段构建**: 使用 Docker 多阶段构建优化镜像大小
  - 阶段 1: node:20-slim（构建前端）
  - 阶段 2: python:3.10-slim（运行后端）
- **静态文件服务**: 后端 FastAPI 直接提供前端静态文件
- **镜像大小**: 约 1.01 GB
- **构建时间**: 约 15-20 分钟（含 Docker 层缓存）

**一键部署**:
```bash
chmod +x deploy.sh
./deploy.sh
```

**手动部署**:
```bash
# 1. 拉取 NE301 镜像
docker pull camthink/ne301-dev:latest

# 2. 构建并启动服务（包含前端构建）
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 停止服务
docker-compose down
```

**重新构建镜像**:
```bash
# 当前端代码修改后，需要重新构建镜像
docker-compose build

# 或者清除缓存强制重建
docker-compose build --no-cache
```

**开发模式**:
```bash
# 支持代码热重载
docker-compose -f docker-compose.dev.yml up --build
```

### 生产环境配置

**环境变量** (创建 `backend/.env`):
```env
# Docker 配置
NE301_DOCKER_IMAGE=camthink/ne301-dev:latest

# 服务器配置
HOST=0.0.0.0
PORT=8000

# 日志级别
LOG_LEVEL=INFO

# 环境
ENVIRONMENT=production
```

### 传统部署方式

**1. 构建前端**:
```bash
cd frontend
npm run build
# 构建结果在 frontend/dist/
```

**2. 启动后端**:
```bash
cd backend
source ../venv/bin/activate

# 生产模式启动
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

**3. 使用 PM2 管理进程** (推荐):
```bash
# 安装 PM2
npm install -g pm2

# 启动服务
pm2 start ecosystem.config.js

# 查看日志
pm2 logs model-converter

# 重启服务
pm2 restart model-converter
```

### 前端 Docker 化注意事项

**构建优化**:
- Dockerfile 使用 `npm install` 而非 `npm ci`（避免 lock file 同步问题）
- 前端构建产物自动优化（gzip 压缩、Tree-shaking）
- 使用 Docker Build Cache 加速重复构建

**静态文件路径**:
- 容器内路径: `/app/frontend/dist`
- FastAPI 挂载配置: `app.mount("/", StaticFiles(...), html=True)`
- 支持 SPA 路由（前端路由直接返回 index.html）

**性能指标**:
- 前端构建时间: ~1.7 秒
- npm 依赖安装: ~3.3 秒
- 静态资源大小:
  - HTML: 0.73 kB (gzip: 0.43 kB)
  - CSS: 42.50 kB (gzip: 6.66 kB)
  - JS: 167.94 kB (gzip: 58.30 kB)

**验证清单**:
```bash
# 1. 验证镜像构建
docker images | grep model-converter-api

# 2. 验证容器内前端文件
docker exec model-converter-api ls -la /app/frontend/dist

# 3. 验证前端访问
curl -I http://localhost:8000/

# 4. 验证 API 访问
curl http://localhost:8000/api/setup/check
```

---

## 故障排查

### 常见问题

#### 1. Docker 相关

**问题**: Docker 未安装或未运行
```
解决:
1. 访问 https://www.docker.com/products/docker-desktop/ 下载安装
2. 启动 Docker Desktop
3. 验证: docker ps
```

**问题**: 镜像拉取失败
```
解决:
1. 检查网络连接
2. 配置 Docker 镜像加速器
3. 手动拉取: docker pull camthink/ne301-dev:latest
```

#### 2. 转换相关

**问题**: ML 库导入错误
```
错误: No module named 'ultralytics' 或 'tensorflow'

解决:
1. 确认使用 Python 3.11/3.12（不支持 3.14）
2. 安装 ML 依赖: pip install ultralytics tensorflow hydra-core opencv-python
3. 重新启动服务
```

**问题**: 转换失败
```
解决:
1. 检查上传的模型格式是否正确（.pt/.pth）
2. 查看实时日志了解详细错误信息
3. 确认模型输入尺寸符合要求
4. 检查 Docker 日志: docker logs <container_id>
```

**问题**: 量化失败
```
解决:
1. 检查校准数据集格式（必须是包含 .jpg/.png 的 ZIP 文件）
2. 确保校准数据至少包含 32 张图片
3. 查看 ST 量化脚本输出日志（backend/tools/quantization/tflite_quant.py）
4. 检查 Hydra 配置文件路径是否正确
```

#### 3. 网络相关

**问题**: WebSocket 连接失败
```
解决:
1. 检查后端是否正常运行
2. 确认防火墙未阻止 WebSocket 连接
3. 查看浏览器控制台错误信息
4. 验证 WebSocket URL: ws://localhost:8000/api/ws
```

**问题**: CORS 错误
```
解决:
1. 检查 FastAPI CORS 配置（main.py）
2. 确认前端请求的 origin 在 allow_origins 列表中
3. 生产环境应限制具体域名
```

### 调试技巧

**后端调试**:
```bash
# 查看详细日志
LOG_LEVEL=DEBUG python -m uvicorn app.main:app --reload

# 进入 Docker 容器调试
docker exec -it <container_id> /bin/bash

# 检查任务状态
curl http://localhost:8000/api/tasks | jq
```

**前端调试**:
```bash
# 查看构建产物
cd frontend/dist
ls -la

# 检查 API 调用
# 打开浏览器开发者工具 > Network 标签
```

**系统诊断**:
```bash
# 检查环境状态
curl http://localhost:8000/api/setup/check

# 查看系统资源
top  # 或 htop

# 检查端口占用
lsof -i :8000
```

---

## 性能优化

### 后端优化

- **异步处理**: 使用 `asyncio` 处理并发请求
- **任务队列**: 考虑使用 Redis + Celery 替代内存队列
- **缓存**: 对频繁访问的数据添加缓存层
- **连接池**: 复用数据库和 HTTP 连接

### 前端优化

- **代码分割**: 使用 Vite 的自动代码分割
- **懒加载**: 按需加载组件
- **资源压缩**: Gzip 压缩静态资源
- **CDN**: 使用 CDN 加速静态资源

---

## 安全注意事项

### 生产环境安全清单

- [ ] 修改 CORS 配置，限制具体域名
- [ ] 添加认证和授权机制
- [ ] 文件上传大小限制
- [ ] 输入验证和清理
- [ ] 使用 HTTPS
- [ ] 敏感信息使用环境变量
- [ ] 定期更新依赖包
- [ ] 启用日志审计

---

## 相关文档

- [Docker 部署指南](README.docker.md) - 容器化部署详细说明
- [缓存清除指南](CACHE_CLEAR_GUIDE.md) - 浏览器缓存问题解决方案
- [模型转换详细文档](backend/docs/MODEL_CONVERSION.md)
- [API 文档](http://localhost:8000/docs) - 启动后访问
- [项目 README](README.md)

---

## 核心架构说明

### 转换流程详解

**完整转换管道**:
```
PyTorch 模型 (.pt/.pth)
    ↓
[步骤 1] 导出为 TFLite (Ultralytics)
    ↓
TFLite 模型 (float32)
    ↓
[步骤 2] ST 量化 (Hydra + TensorFlow)
    ↓
量化 TFLite 模型 (int8)
    ↓
[步骤 3] 准备 NE301 项目结构
    ↓
[步骤 4] NE301 打包 (NE301 容器)
    ↓
NE301 .bin 文件
```

**步骤说明**:

1. **PyTorch → TFLite** (0-30%)
   - 使用 Ultralytics YOLO.export()
   - 生成 float32 TFLite 模型
   - 支持自定义输入尺寸

2. **TFLite → 量化 TFLite** (30-60%)
   - 使用 ST 官方量化脚本 (`tools/quantization/tflite_quant.py`)
   - Hydra 配置管理（`user_config_quant.yaml`）
   - 支持真实校准数据集或 fake 量化
   - 生成 int8 量化模型

3. **准备 NE301 项目** (60-70%)
   - 创建 NE301 目录结构
   - 复制量化模型和配置文件
   - 生成模型 JSON 配置

4. **NE301 打包** (70-100%)
   - 调用 NE301 容器执行 make 命令
   - 生成最终 .bin 部署包

### Docker 架构

**容器编排**:
```
docker-compose.yml
    ├── model-converter-api (主容器)
    │   ├── FastAPI 应用
    │   ├── PyTorch + Ultralytics
    │   ├── TensorFlow + ST 量化脚本
    │   └── Docker SDK (调用 NE301 容器)
    │
    └── ne301-dev (按需调用)
        └── NE301 工具链
```

**关键特性**:
- **Docker-in-Docker**: API 容器通过 Docker SDK 调用 NE301 容器
- **卷挂载**: 共享上传、输出和 NE301 项目目录
- **健康检查**: 自动监控容器状态
- **开发模式**: 支持代码热重载

### 配置管理

**使用 pydantic-settings**:
```python
from app.core.config import settings

# 访问配置
settings.NE301_DOCKER_IMAGE  # Docker 镜像名称
settings.NE301_PROJECT_PATH  # NE301 项目路径
settings.LOG_LEVEL           # 日志级别
settings.MAX_UPLOAD_SIZE     # 最大上传大小
```

**环境变量优先级**:
1. 环境变量
2. .env 文件
3. 默认值

### 参考 AIToolStack

本项目的转换流程参考了 [camthink-ai/AIToolStack](https://github.com/camthink-ai/AIToolStack) 的成熟架构：

- **Docker 适配器**: 参考 `backend/utils/ne301_export.py`
- **量化脚本**: 使用 ST 官方 TFLite 量化工具
- **项目结构**: 遵循 AIToolStack 的目录组织
- **配置管理**: 使用 Hydra 管理复杂配置

---

## 性能优化建议

### 转换性能

- **校准数据集大小**: 32-100 张图片最佳
- **输入尺寸选择**: 根据实际使用场景选择（640/480/320）
- **批量转换**: 使用任务队列管理多个转换任务

### Docker 性能

- **镜像缓存**: 预先拉取 NE301 镜像
- **卷挂载优化**: 使用命名卷减少开销
- **资源限制**: 配置合理的 CPU/内存限制

### 前端性能

- **代码分割**: Vite 自动进行代码分割
- **懒加载**: 按需加载组件和页面
- **缓存策略**: 使用浏览器缓存优化加载

---

## 开发最佳实践

### 后端开发

1. **遵循 PEP 8 规范**
   - 使用 black 格式化代码
   - 使用 isort 排序导入
   - 使用 ruff 进行代码检查

2. **类型注解**
   - 所有函数签名使用类型注解
   - 使用 Pydantic 进行数据验证

3. **错误处理**
   - 明确捕获和包装异常
   - 提供详细的错误日志

4. **测试驱动**
   - 编写测试优先于实现
   - 保持 80%+ 测试覆盖率

### 前端开发

1. **组件设计**
   - 保持组件小而专注
   - 使用 TypeScript 类型安全
   - 遵循单一职责原则

2. **状态管理**
   - 全局状态使用 Zustand
   - 组件状态使用 Signals
   - 避免过度状态提升

3. **性能优化**
   - 使用 React.memo 避免不必要的渲染
   - 懒加载路由和组件
   - 优化图片和资源加载

---

## 常见问题 (FAQ)

### Q: 如何验证转换是否成功？
A: 检查以下内容：
1. 任务状态显示 "completed"
2. 输出目录存在 .bin 文件
3. 模型文件大小合理（通常几 MB）

### Q: 校准数据集是必须的吗？
A: 不是必须的。如果不提供校准数据集，系统会使用 fake 量化，但精度可能降低。

### Q: 支持哪些模型格式？
A: 目前支持：
- PyTorch 模型 (.pt, .pth)
- ONNX 模型 (.onnx)
- YOLO 系列模型 (YOLOv5/v8)

### Q: 转换需要多长时间？
A: 典型转换时间：
- 简单模型: 2-5 分钟
- 复杂模型: 5-15 分钟
- 取决于模型大小和服务器性能

### Q: 如何批量转换模型？
A: 可以：
1. 使用 API 创建多个转换任务
2. 任务队列自动管理并发
3. 通过 WebSocket 监控每个任务进度

---

## 联系方式

如有问题或建议，请通过以下方式联系：

- GitHub Issues: [项目地址](https://github.com/yourusername/model-converter)
- Email: your.email@example.com

---

**最后更新**: 2025-03-13
**文档版本**: 2.0.0
**架构版本**: Docker 化架构 (参考 AIToolStack)
