# NE301 Model Converter Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个个人开发工具，用于将 PyTorch (.pt) 模型量化后转换为 NE301 设备可用的 .bin 文件

**Architecture:** 混合架构 - FastAPI 后端（本地 Python 运行）调用 Docker 容器中的 NE301 工具链进行模型转换

**Tech Stack:**
- 前端: Preact 10 + TypeScript + Vite + Tailwind CSS + Zustand
- 后端: Python 3.11 + FastAPI + docker-py + WebSocket
- 工具链: Docker (camthink/ne301-dev:latest)

---

## 📁 File Structure

```
model-converter/
├── backend/                      # Python 后端（本地运行）
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI 应用入口
│   │   ├── api/                 # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── convert.py        # 转换端点
│   │   │   ├── setup.py          # 环境检测端点
│   │   │   ├── tasks.py          # 任务管理端点
│   │   │   └── websocket.py      # WebSocket 处理
│   │   ├── core/                # 核心业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── task_manager.py   # 任务管理器（单例）
│   │   │   ├── converter.py      # 转换协调器
│   │   │   ├── docker_adapter.py # Docker 工具链适配器
│   │   │   └── environment.py    # 环境检测器
│   │   └── models/             # 数据模型
│   │       ├── __init__.py
│   │       └── schemas.py       # Pydantic 模型
│   ├── tests/                   # 测试
│   │   ├── test_task_manager.py
│   │   ├── test_converter.py
│   │   ├── test_docker_adapter.py
│   │   └── test_api.py
│   ├── requirements.txt
│   ├── uploads/                 # 上传文件目录
│   └── outputs/                 # 输出文件目录
│
├── frontend/                     # Preact 前端
│   ├── src/
│   │   ├── components/         # UI 组件
│   │   │   ├── upload/         # 上传组件
│   │   │   │   ├── ModelUploadArea.tsx
│   │   │   │   ├── CalibUploadArea.tsx
│   │   │   │   └── ClassYamlUploadArea.tsx
│   │   │   ├── config/         # 配置组件
│   │   │   │   ├── PresetCard.tsx
│   │   │   │   └── CustomConfigForm.tsx
│   │   │   ├── monitor/        # 监控组件
│   │   │   │   ├── ProgressBar.tsx
│   │   │   │   ├── LogTerminal.tsx
│   │   │   │   └── CancelButton.tsx
│   │   │   └── common/         # 通用组件
│   │   │       ├── Button.tsx
│   │   │       └── Card.tsx
│   │   ├── pages/              # 页面
│   │   │   ├── SetupPage.tsx   # 设置引导页
│   │   │   └── HomePage.tsx    # 主转换页
│   │   ├── services/           # API 服务
│   │   │   └── api.ts
│   │   ├── store/              # Zustand 状态
│   │   │   └── app.ts
│   │   ├── types/              # TypeScript 类型
│   │   │   └── index.ts
│   │   ├── hooks/              # 自定义 Hooks
│   │   │   ├── useWebSocket.ts
│   │   │   └── useConversion.ts
│   │   ├── utils/              # 工具函数
│   │   │   └── helpers.ts
│   │   ├── App.tsx             # 根组件
│   │   └── main.tsx            # 入口文件
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── package.json
│   └── tsconfig.json
│
├── scripts/                      # 工具脚本
│   ├── start.sh                 # 启动脚本
│   ├── check-docker.sh          # Docker 检查
│   └── install-docker.sh        # Docker 安装引导
│
└── docs/
    └── superpowers/
        └── plans/
            └── 2026-03-12-ne301-model-converter.md  # 本文档
```

---

## Chunk 1: 项目初始化和环境配置

### Task 1.1: 创建后端项目结构

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/schemas.py`
- Create: `backend/requirements.txt`
- Create: `backend/tests/__init__.py`

- [ ] **Step 1: 创建 Python 包结构**

```bash
cd backend
mkdir -p app/api app/core app/models tests uploads outputs
touch app/__init__.py app/api/__init__.py app/core/__init__.py app/models/__init__.py tests/__init__.py
```

- [ ] **Step 2: 创建数据模型**

```python
# backend/app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class ConversionConfig(BaseModel):
    """转换配置"""
    model_type: Literal["YOLOv8", "YOLOX"] = "YOLOv8"
    input_size: Literal[256, 480, 640] = 480
    num_classes: int = Field(default=80, ge=1, le=1000)
    confidence_threshold: float = Field(default=0.25, ge=0.01, le=0.99)
    quantization: Literal["int8"] = "int8"
    use_calibration: bool = False

class ClassDefinition(BaseModel):
    """类别定义"""
    classes: list[dict]  # [{"name": "person", "id": 0, "color": [255, 0, 0]}]

class ConversionTask(BaseModel):
    """转换任务"""
    task_id: str
    status: Literal["pending", "running", "completed", "failed"]
    progress: int = Field(default=0, ge=0, le=100)
    current_step: str = ""
    config: ConversionConfig
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    output_filename: Optional[str] = None

class EnvironmentStatus(BaseModel):
    """环境状态"""
    status: Literal["ready", "docker_not_installed", "image_pull_required", "not_configured"]
    mode: Literal["docker", "none"]
    message: str
    image_size: Optional[str] = None
    estimated_time: Optional[str] = None
    error: Optional[str] = None
    guide: Optional[dict] = None
```

- [ ] **Step 3: 创建依赖文件**

```txt
# backend/requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
python-multipart==0.0.9
pydantic==2.10.0
docker==7.1.0
websockets==13.1
pyyaml==6.0.1
```

- [ ] **Step 4: 提交初始化**

```bash
git add backend/
git commit -m "feat: initialize backend project structure and data models"
```

---

### Task 1.2: 创建前端项目结构

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/types/index.ts`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "ne301-model-converter-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@preact/signals": "^2.2.0",
    "axios": "^1.11.0",
    "clsx": "^2.1.1",
    "lucide-preact": "^0.577.0",
    "preact": "^10.26.9",
    "tailwind-merge": "^2.6.0",
    "zustand": "^5.0.8",
    "pyyaml": "^1.1.0"
  },
  "devDependencies": {
    "@preact/preset-vite": "^2.10.1",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.17",
    "typescript": "^5.7.2",
    "vite": "^6.0.3"
  }
}
```

- [ ] **Step 2: 创建 Vite 配置**

```typescript
// frontend/vite.config.ts
import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';

export default defineConfig({
  plugins: [preact()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
});
```

- [ ] **Step 3: 创建 TypeScript 配置**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "jsx": "react-jsx",
    "jsxImportSource": "preact",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src"]
}
```

- [ ] **Step 4: 创建 Tailwind 配置**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#ee5d35',
      }
    },
  },
  plugins: [],
}
```

- [ ] **Step 5: 创建入口文件**

```typescript
// frontend/src/main.tsx
import { render } from 'preact';
import { App } from './App';
import './index.css';

render(<App />, document.getElementById('app')!);
```

- [ ] **Step 6: 创建根组件**

```typescript
// frontend/src/App.tsx
import { Router } from 'preact-compact-router';
import HomePage from './pages/HomePage';
import SetupPage from './pages/SetupPage';

export function App() {
  return (
    <Router>
      <HomePage path="/" />
      <SetupPage path="/setup" />
    </Router>
  );
}
```

- [ ] **Step 7: 创建类型定义**

```typescript
// frontend/src/types/index.ts
export interface ConversionConfig {
  model_type: 'YOLOv8' | 'YOLOX';
  input_size: 256 | 480 | 640;
  num_classes: number;
  confidence_threshold: number;
  quantization: 'int8';
  use_calibration: boolean;
}

export interface ConversionTask {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  current_step: string;
  config: ConversionConfig;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  error_message?: string;
  output_filename?: string;
}

export interface EnvironmentStatus {
  status: 'ready' | 'docker_not_installed' | 'image_pull_required' | 'not_configured';
  mode: 'docker' | 'none';
  message: string;
  image_size?: string;
  estimated_time?: string;
  error?: string;
  guide?: Record<string, unknown>;
}
```

- [ ] **Step 8: 提交前端初始化**

```bash
git add frontend/
git commit -m "feat: initialize frontend project structure"
```

---

## Chunk 2: 后端核心功能

### Task 2.1: 实现 Docker 工具链适配器

**Files:**
- Create: `backend/app/core/docker_adapter.py`

- [ ] **Step 1: 编写测试**

```python
# backend/tests/test_docker_adapter.py
import pytest
from app.core.docker_adapter import DockerToolChainAdapter

def test_check_docker():
    """测试 Docker 检测"""
    adapter = DockerToolChainAdapter()
    available, error = adapter.check_docker()
    # 需要安装 docker 才能测试
    assert isinstance(available, bool)
    assert isinstance(error, str)

def test_check_image():
    """测试镜像检查"""
    adapter = DockerToolChainAdapter()
    result = adapter.check_image()
    assert isinstance(result, bool)
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend
pytest tests/test_docker_adapter.py -v
# Expected: FAIL - DockerToolChainAdapter not implemented
```

- [ ] **Step 3: 实现 Docker 适配器**

```python
# backend/app/core/docker_adapter.py
import docker
import os
import json
import logging
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

class DockerToolChainAdapter:
    """Docker 工具链适配器（混合架构核心）"""

    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None

        self.image_name = "camthink/ne301-dev:latest"

    def check_docker(self) -> tuple[bool, str]:
        """检查 Docker 是否可用

        Returns:
            (是否可用, 错误信息)
        """
        if not self.client:
            return False, "Docker client not initialized"

        try:
            self.client.ping()
            return True, ""
        except docker.errors.DockerException as e:
            return False, f"Docker not available: {str(e)}"

    def check_image(self) -> bool:
        """检查镜像是否存在"""
        if not self.client:
            return False

        try:
            self.client.images.get(self.image_name)
            return True
        except docker.errors.ImageNotFound:
            return False

    def pull_image(
        self,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> bool:
        """拉取 Docker 镜像

        Args:
            progress_callback: 进度回调函数(progress: int)

        Returns:
            是否成功
        """
        if not self.client:
            logger.error("Docker client not available")
            return False

        try:
            logger.info(f"Pulling image {self.image_name}...")

            for layer in self.client.images.pull(
                self.image_name,
                stream=True,
                decode=True
            ):
                if progress_callback and "progressDetail" in layer:
                    progress = layer["progressDetail"].get("current", 0)
                    total = layer["progressDetail"].get("total", 100)
                    progress_callback(int(progress / total * 100))

            logger.info("Image pulled successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to pull image: {e}")
            return False

    def convert_model(
        self,
        task_id: str,
        model_path: str,
        config: dict
    ) -> str:
        """在 Docker 容器中执行转换

        Args:
            task_id: 任务 ID
            model_path: 模型文件路径（本地）
            config: 转换配置

        Returns:
            输出文件路径（本地）
        """
        if not self.client:
            raise RuntimeError("Docker client not available")

        # 准备卷映射
        model_dir = Path(model_path).parent.resolve()
        output_dir = Path("outputs").absolute()

        volumes = {
            str(model_dir): {"bind": "/input", "mode": "ro"},
            str(output_dir): {"bind": "/output", "mode": "rw"}
        }

        # 构建命令
        model_filename = Path(model_path).name
        command = [
            "python",
            "/workspace/ne301/Script/model_packager.py",
            "create",
            "--model", f"/input/{model_filename}",
            "--config", json.dumps(config),
            "--output", f"/output/ne301_model_{task_id}.bin"
        ]

        try:
            logger.info(f"Starting conversion for task {task_id}")

            # 运行容器（同步等待）
            # 容器会在完成后自动删除（remove=True）
            self.client.containers.run(
                self.image_name,
                command=command,
                volumes=volumes,
                remove=True,
                detach=False
            )

            logger.info(f"Conversion completed for task {task_id}")
            return f"outputs/ne301_model_{task_id}.bin"

        except Exception as e:
            logger.error(f"Conversion failed for task {task_id}: {e}")
            raise
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest backend/tests/test_docker_adapter.py -v
# Expected: PASS (如果 Docker 已安装)
```

- [ ] **Step 5: 提交**

```bash
git add backend/app/core/docker_adapter.py backend/tests/test_docker_adapter.py
git commit -m "feat: implement Docker toolchain adapter"
```

---

### Task 2.2: 实现任务管理器

**Files:**
- Create: `backend/app/core/task_manager.py`
- Modify: `backend/tests/test_task_manager.py`

- [ ] **Step 1: 编写测试**

```python
# backend/tests/test_task_manager.py
import pytest
from app.core.task_manager import TaskManager, get_task_manager
from app.models.schemas import ConversionConfig, ConversionTask

def test_singleton():
    """测试单例模式"""
    manager1 = get_task_manager()
    manager2 = get_task_manager()
    assert manager1 is manager2

def test_create_task():
    """测试创建任务"""
    manager = get_task_manager()
    config = ConversionConfig()
    task_id = manager.create_task(config)
    assert task_id is not None
    assert len(task_id) > 0

def test_update_progress():
    """测试更新进度"""
    manager = get_task_manager()
    config = ConversionConfig()
    task_id = manager.create_task(config)

    manager.update_progress(task_id, 50, "量化中...")
    task = manager.get_task(task_id)

    assert task.progress == 50
    assert task.current_step == "量化中..."
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest backend/tests/test_task_manager.py::test_create_task -v
# Expected: FAIL
```

- [ ] **Step 3: 实现任务管理器**

```python
# backend/app/core/task_manager.py
import uuid
from datetime import datetime
from typing import Optional, Dict
from app.models.schemas import ConversionTask, ConversionConfig

class TaskManager:
    """任务管理器（单例）"""

    _instance: Optional['TaskManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.tasks: Dict[str, ConversionTask] = {}
        self.websocket_connections: Dict[str, list] = {}

    def create_task(self, config: ConversionConfig) -> str:
        """创建新任务

        Returns:
            task_id
        """
        task_id = str(uuid.uuid4())
        now = datetime.now()

        task = ConversionTask(
            task_id=task_id,
            status="pending",
            progress=0,
            current_step="",
            config=config,
            created_at=now,
            updated_at=now
        )

        self.tasks[task_id] = task
        return task_id

    def get_task(self, task_id: str) -> Optional[ConversionTask]:
        """获取任务状态"""
        return self.tasks.get(task_id)

    def update_progress(self, task_id: str, progress: int, step: str):
        """更新任务进度"""
        if task_id in self.tasks:
            self.tasks[task_id].progress = progress
            self.tasks[task_id].current_step = step
            self.tasks[task_id].updated_at = datetime.now()

            # WebSocket 推送
            self._broadcast_progress(task_id, progress, step)

    def _broadcast_progress(self, task_id: str, progress: int, step: str):
        """广播进度到 WebSocket 连接"""
        if task_id in self.websocket_connections:
            import asyncio
            import json

            message = {
                "type": "progress",
                "task_id": task_id,
                "progress": progress,
                "step": step
            }

            # 简化版本 - 实际实现需要 WebSocket 管理
            logger.info(f"Broadcasting progress for task {task_id}: {progress}%")

    def complete_task(self, task_id: str, output_filename: str):
        """标记任务完成"""
        if task_id in self.tasks:
            self.tasks[task_id].status = "completed"
            self.tasks[task_id].progress = 100
            self.tasks[task_id].completed_at = datetime.now()
            self.tasks[task_id].output_filename = output_filename
            self.tasks[task_id].updated_at = datetime.now()

    def fail_task(self, task_id: str, error: str):
        """标记任务失败"""
        if task_id in self.tasks:
            self.tasks[task_id].status = "failed"
            self.tasks[task_id].error_message = error
            self.tasks[task_id].updated_at = datetime.now()

# 单例获取函数
_task_manager: Optional[TaskManager] = None

def get_task_manager() -> TaskManager:
    """获取任务管理器单例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest backend/tests/test_task_manager.py -v
# Expected: PASS
```

- [ ] **Step 5: 提交**

```bash
git add backend/app/core/task_manager.py backend/tests/test_task_manager.py
git commit -m "feat: implement task manager with singleton pattern"
```

---

### Task 2.3: 实现环境检测器

**Files:**
- Create: `backend/app/core/environment.py`

- [ ] **Step 1: 实现环境检测器**

```python
# backend/app/core/environment.py
import platform
from app.models.schemas import EnvironmentStatus
from app.core.docker_adapter import DockerToolChainAdapter

class EnvironmentDetector:
    """环境检测器（混合架构 - 仅 Docker）"""

    def __init__(self):
        self.toolchain = DockerToolChainAdapter()

    def check(self) -> EnvironmentStatus:
        """检查环境状态"""
        # 1. 检查 Docker 是否安装并运行
        docker_available, error = self.toolchain.check_docker()
        if not docker_available:
            return EnvironmentStatus(
                status="docker_not_installed",
                mode="none",
                message="Docker 未安装或未启动",
                error=error,
                guide=self._get_docker_install_guide()
            )

        # 2. 检查镜像是否存在
        if not self.toolchain.check_image():
            return EnvironmentStatus(
                status="image_pull_required",
                mode="docker",
                message="Docker 已就绪，首次转换时会自动拉取工具镜像",
                image_size="~3GB",
                estimated_time="3-5 分钟（取决于网络速度）"
            )

        # 3. 环境完全就绪
        return EnvironmentStatus(
            status="ready",
            mode="docker",
            message="环境就绪，可以开始转换"
        )

    def _get_docker_install_guide(self) -> dict:
        """获取 Docker 安装指南"""
        system = platform.system()

        if system == "Darwin":
            return {
                "title": "安装 Docker Desktop for Mac",
                "url": "https://www.docker.com/products/docker-desktop",
                "steps": [
                    "1. 下载 Docker Desktop for Mac",
                    "2. 打开 .dmg 文件并拖拽到 Applications",
                    "3. 启动 Docker Desktop",
                    "4. 等待 Docker 启动完成（菜单栏图标）"
                ]
            }
        elif system == "Linux":
            return {
                "title": "安装 Docker Engine",
                "url": "https://docs.docker.com/engine/install/",
                "command": "curl -fsSL https://get.docker.com | sh"
            }
        elif system == "Windows":
            return {
                "title": "安装 Docker Desktop for Windows",
                "url": "https://www.docker.com/products/docker-desktop",
                "steps": [
                    "1. 下载 Docker Desktop for Windows",
                    "2. 运行安装程序",
                    "3. 启用 WSL 2 功能（如果需要）",
                    "4. 重启计算机",
                    "5. 启动 Docker Desktop"
                ]
            }

        return {}
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/core/environment.py
git commit -m "feat: implement environment detector for Docker"
```

---

## Chunk 3: 后端 API 层

### Task 3.1: 实现 FastAPI 主应用

**Files:**
- Create: `backend/app/main.py`

- [ ] **Step 1: 创建 FastAPI 应用**

```python
# backend/app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.api import convert, setup, tasks, websocket

# 创建应用
app = FastAPI(
    title="NE301 Model Converter",
    version="1.0.0",
    description="PyTorch to NE301 model conversion tool"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(convert.router, prefix="/api", tags=["conversion"])
app.include_router(setup.router, prefix="/api/setup", tags=["setup"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])

# 静态文件服务（前端构建后）
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

@app.on_event("startup")
async def startup_event():
    """启动事件"""
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.info("NE301 Model Converter started")

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}
```

- [ ] **Step 2: 创建 API 路由模块**

```python
# backend/app/api/__init__.py
from app.api.convert import router as convert_router
from app.api.setup import router as setup_router
from app.api.tasks import router as tasks_router
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/main.py backend/app/api/__init__.py
git commit -m "feat: create FastAPI application with route modules"
```

---

### Task 3.2: 实现转换 API

**Files:**
- Create: `backend/app/api/convert.py`

- [ ] **Step 1: 编写测试**

```python
# backend/tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_convert_no_file():
    """测试没有文件的情况"""
    client = TestClient(app)
    response = client.post("/api/convert", data={})
    assert response.status_code == 422  # Validation error
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest backend/tests/test_api.py::test_convert_no_file -v
# Expected: FAIL
```

- [ ] **Step 3: 实现转换 API**

```python
# backend/app/api/convert.py
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
import shutil
import uuid

from app.core.task_manager import get_task_manager
from app.core.converter import Converter
from app.models.schemas import ConversionConfig

router = APIRouter()

@router.post("/convert")
async def convert_model(
    model_file: UploadFile = File(...),
    config: str = Form(...),
    class_yaml: UploadFile = File(None)
):
    """上传模型并启动转换"""

    # 1. 验证文件
    if not model_file.filename.endswith(('.pt', '.pth', '.onnx')):
        return JSONResponse(
            status_code=400,
            content={"error": "不支持的文件格式，请上传 .pt 文件"}
        )

    # 2. 保存上传文件
    task_id = str(uuid.uuid4())
    uploads_dir = "uploads"
    os.makedirs(uploads_dir, exist_ok=True)

    model_path = os.path.join(uploads_dir, f"{task_id}_{model_file.filename}")
    with open(model_path, "wb") as f:
        shutil.copyfileobj(model_file.f, f)

    # 3. 解析配置
    try:
        import json
        config_dict = json.loads(config)
        conversion_config = ConversionConfig(**config_dict)
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": f"配置格式错误: {str(e)}"}
        )

    # 4. 保存 YAML 文件（如果有）
    if class_yaml:
        yaml_path = os.path.join(uploads_dir, f"{task_id}_{class_yaml.filename}")
        with open(yaml_path, "wb") as f:
            shutil.copyfileobj(class_yaml.f, f)

    # 5. 创建任务
    task_manager = get_task_manager()
    task_id = task_manager.create_task(conversion_config)

    # 6. 启动后台转换
    import asyncio
    asyncio.create_task(conversion_task(task_id, model_path, yaml_path))

    return JSONResponse({
        "task_id": task_id,
        "status": "started"
    })

async def conversion_task(task_id: str, model_path: str, yaml_path: str = None):
    """后台转换任务"""
    from app.core.converter import Converter

    converter = Converter()

    try:
        result_path = await converter.convert(task_id, model_path, yaml_path)
        task_manager.complete_task(task_id, result_path)
    except Exception as e:
        task_manager.fail_task(task_id, str(e))
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/api/convert.py backend/tests/test_api.py
git commit -m "feat: implement conversion API endpoint"
```

---

### Task 3.3: 实现设置 API

**Files:**
- Create: `backend/app/api/setup.py`

- [ ] **Step 1: 实现设置 API**

```python
# backend/app/api/setup.py
from fastapi import APIRouter
from app.core.environment import EnvironmentDetector

router = APIRouter()

@router.get("/check")
async def check_setup():
    """检查环境状态"""
    detector = EnvironmentDetector()
    status = detector.check()
    return status
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/api/setup.py
git commit -m "feat: implement setup check endpoint"
```

---

### Task 3.4: 实现 WebSocket 处理

**Files:**
- Create: `backend/app/api/websocket.py`

- [ ] **Step 1: 实现 WebSocket 处理器**

```python
# backend/app/api/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from app.core.task_manager import get_task_manager
import json

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端点"""
    await websocket.accept()
    task_manager = get_task_manager()

    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()

            if data.get("type") == "subscribe":
                task_id = data.get("task_id")
                if task_id:
                    # 订阅任务进度
                    if task_id not in task_manager.websocket_connections:
                        task_manager.websocket_connections[task_id] = []
                    task_manager.websocket_connections[task_id].append(websocket)

                    # 发送当前状态
                    task = task_manager.get_task(task_id)
                    if task:
                        await websocket.send_json({
                            "type": "progress",
                            "task_id": task_id,
                            "progress": task.progress,
                            "step": task.current_step
                        })

            elif data.get("type") == "cancel":
                task_id = data.get("task_id")
                # TODO: 实现取消逻辑

    except WebSocketDisconnect:
        # 清理连接
        pass
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/api/websocket.py
git commit -m "feat: implement WebSocket handler for real-time progress"
```

---

## Chunk 4: 前端核心组件

### Task 4.1: 创建上传组件

**Files:**
- Create: `frontend/src/components/upload/ModelUploadArea.tsx`
- Create: `frontend/src/components/upload/ClassYamlUploadArea.tsx`

- [ ] **Step 1: 实现模型上传组件**

```typescript
// frontend/src/components/upload/ModelUploadArea.tsx
import { h } from 'preact/hooks';
import { useRef, useState } from 'preact/hooks';
import { UploadCloud } from 'lucide-preact';

interface Props {
  onFileSelect: (file: File) => void;
}

export function ModelUploadArea({ onFileSelect }: Props) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0] as File;
    if (file && validateFile(file)) {
      onFileSelect(file);
    }
  };

  const handleFileChange = (e: Event) => {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (file && validateFile(file)) {
      onFileSelect(file);
    }
  };

  const validateFile = (file: File): boolean => {
    const validExtensions = ['.pt', '.pth', '.onnx'];
    const isValidExt = validExtensions.some(ext => file.name.endsWith(ext));
    const isValidSize = file.size <= 500 * 1024 * 1024; // 500MB

    if (!isValidExt) {
      alert('不支持的文件格式，请上传 .pt 文件');
      return false;
    }

    if (!isValidSize) {
      alert('文件大小超过 500MB 限制');
      return false;
    }

    return true;
  };

  return (
    <div
      class={`upload-area ${isDragging ? 'dragging' : ''}`}
      onDrop={handleDrop}
      onDragOver={(e) => e => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={() => setIsDragging(false)}
      onClick={() => fileInput.current?.click()}
    >
      <UploadCloud size={48} />
      <p>拖拽 .pt 模型文件到此处</p>
      <p class="text-sm text-gray-500">或点击选择文件（最大 500MB）</p>

      <input
        ref={fileInput}
        type="file"
        accept=".pt,.pth,.onnx"
        onChange={handleFileChange}
        class="hidden"
      />
    </div>
  );
}
```

- [ ] **Step 2: 实现类别 YAML 上传组件**

```typescript
// frontend/src/components/upload/ClassYamlUploadArea.tsx
import { h } from 'preact/hooks';
import { useRef, useState } from 'preact/hooks';
import { FileText, Upload } from 'lucide-preact';

interface Props {
  onFileSelect: (file: File | null) => void;
}

export function ClassYamlUploadArea({ onFileSelect }: Props) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string>('');

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0] as File;
    if (file && file.name.endsWith(('.yaml', '.yml'))) {
      processFile(file);
    }
  };

  const handleFileChange = (e: Event) => {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const processFile = async (file: File) => {
    const text = await file.text();
    setPreview(text);
    onFileSelect(file);
  };

  return (
    <div>
      <div class="flex items-center justify-between mb-2">
        <h3 class="text-lg font-semibold">类别定义（可选）</h3>
        <button
          onClick={() => fileInput.current?.click()}
          class="btn btn-secondary btn-sm"
        >
          <Upload size={16} />
          上传 YAML
        </button>
      </div>

      <input
        ref={fileInput}
        type="file"
        accept=".yaml,.yml"
        onChange={handleFileChange}
        class="hidden"
      />

      {preview && (
        <div class="mt-2 p-2 bg-gray-100 rounded text-sm font-mono">
          <FileText size={16} />
          <pre class="mt-2 text-xs">{preview}</pre>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/upload/
git commit -m "feat: implement model and YAML upload components"
```

---

### Task 4.2: 实现配置选择组件

**Files:**
- Create: `frontend/src/components/config/PresetCard.tsx`

- [ ] **Step 1: 实现预设卡片组件**

```typescript
// frontend/src/components/config/PresetCard.tsx
import { h } from 'preact/hooks';
import { CheckCircle } from 'lucide-preact';

interface Preset {
  id: string;
  name: string;
  size: number;
  description: string;
}

interface Props {
  preset: Preset;
  selected: boolean;
  onSelect: () => void;
}

export function PresetCard({ preset, selected, onSelect }: Props) {
  return (
    <div
      class={`preset-card p-4 border rounded-lg cursor-pointer transition ${
        selected ? 'border-primary bg-primary/5' : 'border-gray-200 hover:border-primary/50'
      }`}
      onClick={onSelect}
    >
      <div class="flex items-center justify-between mb-2">
        <h3 class="font-semibold">{preset.name}</h3>
        {selected && <CheckCircle class="text-primary" size={20} />}
      </div>
      <p class="text-sm text-gray-600 mb-1">{preset.description}</p>
      <p class="text-xs text-gray-500">{preset.size}x{preset.size} INT8</p>
    </div>
  );
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/config/
git commit -m "feat: implement preset card component"
```

---

### Task 4.3: 实现进度监控组件

**Files:**
- Create: `frontend/src/components/monitor/ProgressBar.tsx`
- Create: `frontend/src/hooks/useWebSocket.ts`

- [ ] **Step 1: 实现 WebSocket Hook**

```typescript
// frontend/src/hooks/useWebSocket.ts
import { useEffect, useState } from 'preact/hooks';

export function useWebSocket(taskId: string | null) {
  const [progress, setProgress] = useState(0);
  const [step, setStep] = useState('');
  const [status, setStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');

  useEffect(() => {
    if (!taskId) return;

    const ws = new WebSocket(`ws://localhost:8000/ws`);

    ws.onopen = () => {
      setStatus('connected');
      // 订阅任务
      ws.send(JSON.stringify({
        type: 'subscribe',
        task_id: taskId
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'progress') {
        setProgress(data.progress);
        setStep(data.step);
      }
    };

    ws.onerror = () => {
      setStatus('disconnected');
    };

    ws.onclose = () => {
      setStatus('disconnected');
    };

    return () => {
      ws.close();
    };
  }, [taskId]);

  return { progress, step, status };
}
```

- [ ] **Step 2: 实现进度条组件**

```typescript
// frontend/src/components/monitor/ProgressBar.tsx
import { h } from 'preact/hooks';

interface Props {
  progress: number;
  step: string;
}

export function ProgressBar({ progress, step }: Props) {
  return (
    <div class="w-full">
      <div class="flex justify-between text-sm mb-1">
        <span>{step}</span>
        <span>{progress}%</span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-2">
        <div
          class="bg-primary h-2 rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/hooks/ frontend/src/components/monitor/
git commit -m "feat: implement WebSocket hook and progress bar component"
```

---

### Task 4.4: 实现主页面

**Files:**
- Create: `frontend/src/pages/HomePage.tsx`

- [ ] **Step 1: 实现主转换页面**

```typescript
// frontend/src/pages/HomePage.tsx
import { h } from 'preact/hooks';
import { useState } from 'preact/hooks';
import { ModelUploadArea } from '../components/upload/ModelUploadArea';
import { ClassYamlUploadArea } from '../components/upload/ClassYamlUploadArea';
import { PresetCard } from '../components/config/PresetCard';
import { ProgressBar } from '../components/monitor/ProgressBar';
import { useWebSocket } from '../hooks/useWebSocket';
import { api } from '../services/api';

const PRESETS = [
  { id: 'fast', name: '快速模式', size: 256, description: '速度优先' },
  { id: 'balanced', name: '平衡模式', size: 480, description: '推荐' },
  { id: 'high', name: '高精度模式', size: 640, description: '精度优先' },
];

export function HomePage() {
  const [modelFile, setModelFile] = useState<File | null>(null);
  const [yamlFile, setYamlFile] = useState<File | null>(null);
  const [selectedPreset, setSelectedPreset] = useState('balanced');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [isConverting, setIsConverting] = useState(false);

  const { progress, step } = useWebSocket(taskId);

  const handleStartConvert = async () => {
    if (!modelFile) {
      alert('请先上传模型文件');
      return;
    }

    setIsConverting(true);

    const config = {
      model_type: 'YOLOv8',
      input_size: selectedPreset === 'fast' ? 256 : selectedPreset === 'balanced' ? 480 : 640,
      num_classes: 80,
      confidence_threshold: 0.25,
      quantization: 'int8',
      use_calibration: false
    };

    try {
      const response = await api.convertModel(modelFile, config, yamlFile);
      setTaskId(response.task_id);
    } catch (error) {
      alert(`转换失败: ${error}`);
      setIsConverting(false);
    }
  };

  return (
    <div class="max-w-4xl mx-auto p-6">
      <h1 class="text-2xl font-bold mb-6">NE301 模型转换工具</h1>

      {/* 上传区域 */}
      <div class="grid grid-cols-2 gap-4 mb-6">
        <div>
          <h2 class="text-lg font-semibold mb-2">1. 上传模型</h2>
          <ModelUploadArea onFileSelect={setModelFile} />
          {modelFile && (
            <p class="text-sm text-gray-600 mt-2">已选择: {modelFile.name}</p>
          )}
        </div>

        <div>
          <h2 class="text-lg font-semibold mb-2">2. 类别定义（可选）</h2>
          <ClassYamlUploadArea onFileSelect={setYamlFile} />
        </div>
      </div>

      {/* 配置选择 */}
      <div class="mb-6">
        <h2 class="text-lg font-semibold mb-3">3. 选择配置预设</h2>
        <div class="grid grid-cols-3 gap-4">
          {PRESETS.map(preset => (
            <PresetCard
              key={preset.id}
              preset={preset}
              selected={selectedPreset === preset.id}
              onSelect={() => setSelectedPreset(preset.id)}
            />
          ))}
        </div>
      </div>

      {/* 转换按钮 */}
      <div class="mb-6">
        <button
          onClick={handleStartConvert}
          disabled={!modelFile || isConverting}
          class="btn btn-primary w-full"
        >
          {isConverting ? '转换中...' : '开始转换'}
        </button>
      </div>

      {/* 进度显示 */}
      {taskId && (
        <div class="mb-6">
          <h2 class="text-lg font-semibold mb-3">转换进度</h2>
          <ProgressBar progress={progress} step={step} />
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: 创建 API 服务**

```typescript
// frontend/src/services/api.ts
import axios from 'axios';

const API_BASE = '/api';

export const api = {
  async convertModel(
    modelFile: File,
    config: any,
    yamlFile?: File
  ): Promise<{ task_id: string }> {
    const formData = new FormData();
    formData.append('model', modelFile);
    formData.append('config', JSON.stringify(config));
    if (yamlFile) {
      formData.append('class_yaml', yamlFile);
    }

    const response = await axios.post(`${API_BASE}/convert`, formData, {
      timeout: 30 * 60 * 1000 // 30 分钟
    });
    return response.data;
  }
};
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/pages/HomePage.tsx frontend/src/services/api.ts
git commit -m "feat: implement main conversion page with progress tracking"
```

---

## Chunk 5: 设置引导页面

### Task 5.1: 实现环境检测和引导

**Files:**
- Create: `frontend/src/pages/SetupPage.tsx`

- [ ] **Step 1: 实现设置页面**

```typescript
// frontend/src/pages/SetupPage.tsx
import { h } from 'preact/hooks';
import { useState, useEffect } from 'preact/hooks';
import { api } from '../services/api';
import { CheckCircle, XCircle, Download, ExternalLink } from 'lucide-preact';

export function SetupPage() {
  const [envStatus, setEnvStatus] = useState<any>(null);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    checkEnvironment();
  }, []);

  const checkEnvironment = async () => {
    setIsChecking(true);
    try {
      const status = await api.checkEnvironment();
      setEnvStatus(status);
    } catch (error) {
      console.error('Failed to check environment:', error);
    } finally {
      setIsChecking(false);
    }
  };

  if (isChecking) {
    return <div class="p-6">检测环境中...</div>;
  }

  if (envStatus?.status === 'ready') {
    return (
      <div class="max-w-2xl mx-auto p-6">
        <CheckCircle class="text-green-500 mx-auto mb-4" size={48} />
        <h1 class="text-2xl font-bold text-center mb-4">环境就绪！</h1>
        <p class="text-center text-gray-600 mb-6">Docker 已安装并运行，工具镜像已下载</p>
        <button
          onClick={() => window.location.href = '/'}
          class="btn btn-primary w-full"
        >
          开始使用
        </button>
      </div>
    );
  }

  if (envStatus?.status === 'docker_not_installed') {
    return (
      <div class="max-w-2xl mx-auto p-6">
        <XCircle class="text-red-500 mx-auto mb-4" size={48} />
        <h1 class="text-2xl font-bold text-center mb-4">需要安装 Docker</h1>

        <div class="bg-gray-100 p-4 rounded-lg mb-6">
          <h2 class="text-lg font-semibold mb-2">安装步骤：</h2>
          <ol class="list-decimal pl-4 space-y-2">
            <li>
              <a
                href={envStatus.guide?.url || '#'}
                target="_blank"
                class="text-primary hover:underline"
              >
                下载 Docker Desktop
              </a>
            </li>
            <li>安装并启动 Docker Desktop</li>
            <li>验证安装：docker --version</li>
          </ol>
        </div>

        <button onClick={checkEnvironment} class="btn btn-secondary w-full">
          重新检测
        </button>
      </div>
    );
  }

  if (envStatus?.status === 'image_pull_required') {
    return (
      <div class="max-w-2xl mx-auto p-6">
        <h1 class="text-2xl font-bold text-center mb-4">首次使用</h1>
        <p class="text-center text-gray-600 mb-6">
          Docker 已就绪，首次转换时会自动拉取工具镜像
        </p>

        <div class="bg-blue-50 p-4 rounded-lg mb-6">
          <h2 class="text-lg font-semibold mb-2">镜像信息：</h2>
          <ul class="list-disc pl-4 space-y-1">
            <li>大小: {envStatus.image_size}</li>
            <li>预计时间: {envStatus.estimated_time}</li>
          </ul>
        </div>

        <button
          onClick={() => window.location.href = '/'}
          class="btn btn-primary w-full"
        >
          开始使用
        </button>
      </div>
    );
  }

  return (
    <div class="max-w-2xl mx-auto p-6">
      <XCircle class="text-red-500 mx-auto mb-4" size={48} />
      <h1 class="text-2xl font-bold text-center mb-4">环境未就绪</h1>
      <p class="text-center text-gray-600 mb-6">{envStatus?.message}</p>
      <button onClick={checkEnvironment} class="btn btn-secondary w-full">
        重新检测
      </button>
    </div>
  );
}
```

- [ ] **Step 2: 更新 API 服务**

```typescript
// frontend/src/services/api.ts
export const api = {
  // ... existing code ...

  async checkEnvironment(): Promise<any> {
    const response = await axios.get('/api/setup/check');
    return response.data;
  }
};
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/pages/SetupPage.tsx frontend/src/services/api.ts
git commit -m "feat: implement setup guide page with environment detection"
```

---

## Chunk 6: 集成测试和文档

### Task 6.1: 创建启动脚本

**Files:**
- Create: `scripts/start.sh`
- Create: `scripts/check-docker.sh`

- [ ] **Step 1: 创建启动脚本**

```bash
#!/bin/bash
# scripts/start.sh

echo "🚀 Starting NE301 Model Converter..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# 进入后端目录
cd backend

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# 检查 Docker
echo "🐳 Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop."
    exit 1
fi

docker ping > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Environment check passed"

# 构建前端
echo "🔨 Building frontend..."
cd ../frontend
pnpm install
pnpm build

cd ..

# 启动服务
echo "✅ Starting server..."
echo "🌐 Open http://localhost:8000 in your browser"
python3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

- [ ] **Step 2: 创建 Docker 检查脚本**

```bash
#!/bin/bash
# scripts/check-docker.sh

echo "Checking Docker installation..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

if ! docker ping &> /dev/null 2>&1; then
    echo "❌ Docker is not running"
    exit 1
fi

echo "✅ Docker is ready"
```

- [ ] **Step 3: 设置执行权限**

```bash
chmod +x scripts/start.sh scripts/check-docker.sh
```

- [ ] **Step 4: 提交**

```bash
git add scripts/
git commit -m "feat: add startup and Docker check scripts"
```

---

### Task 6.2: 创建 README

**Files:**
- Create: `README.md`

- [ ] **Step 1: 创建项目 README**

```markdown
# NE301 Model Converter

PyTorch 模型转换为 NE301 设备 .bin 文件的工具

## 快速开始

### 1. 系统要求

- Python 3.11+
- Docker Desktop
- Node.js 20+ (包含 pnpm)
- 5GB 可用磁盘空间

### 2. 安装 Docker

下载并安装 [Docker Desktop](https://www.docker.com/products/docker-desktop)

### 3. 一键启动

```bash
# 克隆仓库
git clone <repo-url>
cd model-converter

# 启动服务
./start.sh
```

### 4. 访问应用

打开浏览器访问 http://localhost:8000

首次使用时会自动引导环境配置。

## 使用说明

1. 上传 .pt 模型文件
2. 上传类别定义 YAML（可选）
3. 选择配置预设
4. 点击"开始转换"
5. 等待转换完成（3-5 分钟）
6. 下载 .bin 文件

## 架构

- **前端**: Preact 10 + TypeScript
- **后端**: Python 3.11 + FastAPI
- **工具链**: Docker (camthink/ne301-dev:latest)

## 开发

### 后端开发

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 前端开发

```bash
cd frontend
pnpm install
pnpm dev
```

## 故障排查

### Docker 相关

**问题**: Docker 未启动
```bash
# 检查 Docker 状态
docker info

# 重启 Docker Desktop
```

**问题**: 镜像拉取失败
```bash
# 手动拉取镜像
docker pull camthink/ne301-dev:latest
```

### Python 相关

**问题**: 依赖安装失败
```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

## 许可证

MIT

---

- [ ] **Step 2: 提交 README**

```bash
git add README.md
git commit -m "docs: add comprehensive README"
```

---

## 验证和测试

### 验证清单

在提交计划完成之前，验证以下内容：

- [ ] 所有任务步骤完整
- [ ] 代码示例完整可运行
- [ ] 测试命令准确
- [ ] 文件路径正确
- [ ] 依赖版本指定
- [ ] 提交信息清晰

### 端到端测试流程

```bash
# 1. 启动服务
./start.sh

# 2. 访问 http://localhost:8000
# 验证首页加载

# 3. 上传测试模型
# 使用 frontend-old 中的测试模型或下载 YOLOv8n.pt

# 4. 观察转换过程
# 检查 Docker 容器启动
# 验证进度更新

# 5. 下载结果
# 验证 .bin 文件生成
```

---

**计划完成并保存到 `docs/superpowers/plans/2026-03-12-ne301-model-converter.md`**

准备执行吗？
