# NE301 模型转换工具 - 技术架构设计

## 📐 架构概述

**设计方案**: 方案 C - 混合架构（后端本地 + Docker 工具链）⭐
**架构师评审**: 4.6/5 分 - 强烈推荐
**创建日期**: 2026-03-12
**最后更新**: 2026-03-12（混合架构）
**状态**: 已批准

---

## 🎯 架构目标

### 核心设计原则

1. **简单优先**: 个人使用，单任务处理，避免过度工程
2. **实时响应**: WebSocket 推送，非阻塞界面
3. **Docker 隔离**: 工具链完全隔离在 Docker 容器中，确保跨平台兼容
4. **可维护性**: 清晰的模块边界，易于扩展
5. **用户友好**: 混合用户群体，平衡简单性和灵活性
6. **快速启动**: 后端本地运行，2 秒启动，Docker 按需调用

---

## 🏗️ 系统架构

### 整体架构图（混合架构）

```
┌─────────────────────────────────────────────────────────────┐
│                   用户层（浏览器）                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Preact 前端（SPA）                                    │  │
│  │  • 页面：首页/设置引导                                │  │
│  │  • 组件：上传/配置/进度/日志                          │  │
│  │  • 通信：HTTP + WebSocket                            │  │
│  └───────────────────────┬───────────────────────────────┘  │
└──────────────────────────┼──────────────────────────────────┘
                         │ HTTP + WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│         应用层（FastAPI 后端 - 本地 Python 运行）             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  API 路由层                                          │  │
│  │  • /api/convert - 转换端点                          │  │
│  │  • /api/progress - 进度查询                         │  │
│  │  • /api/setup/check - 环境检测                       │  │
│  │  • /ws - WebSocket 连接                              │  │
│  │  • / - 静态文件服务                                  │  │
│  └───────────────────────┬─────────────────────────────┘  │
│  ┌───────────────────────▼─────────────────────────────┐  │
│  │  业务逻辑层                                          │  │
│  │  • TaskManager - 任务管理器（单例）                 │  │
│  │  • Converter - 转换协调器                           │  │
│  │  • EnvironmentDetector - Docker 环境检测器          │  │
│  │  • DockerToolChainAdapter - Docker 工具链适配器     │  │
│  └───────────────────────┬─────────────────────────────┘  │
│  ┌───────────────────────▼─────────────────────────────┐  │
│  │  后台执行层（本地线程）                              │  │
│  │  • BackgroundTasks - 异步任务执行                   │  │
│  │  • ProgressReporter - 进度报告器（WebSocket 推送）   │  │
│  └───────────────────────┬─────────────────────────────┘  │
└──────────────────────────┼──────────────────────────────────┘
                         │ 按需调用（仅转换时）
┌──────────────────────────▼──────────────────────────────────┐
│         工具层（Docker 容器 - 按需启动，自动清理）          │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  camthink/ne301-dev:latest （临时容器）             │  │
│  │  • ST Edge AI 量化工具                              │  │
│  │  • model_packager.py                                │  │
│  │  • generate-reloc-model.sh                          │  │
│  │  • 容器生命周期：转换时启动，完成后删除             │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 模块设计

### 1. 任务管理器（TaskManager）

**职责**: 单一任务生命周期管理

**设计模式**: 单例模式

**接口**:
```python
class TaskManager:
    def create_task(self, config: ConversionConfig) -> str:
        """创建新任务，返回 task_id"""

    def get_task(self, task_id: str) -> Optional[ConversionTask]:
        """获取任务状态"""

    def update_progress(self, task_id: str, progress: int, step: str):
        """更新任务进度"""

    def complete_task(self, task_id: str, result: ConversionResult):
        """标记任务完成"""

    def fail_task(self, task_id: str, error: str):
        """标记任务失败"""

    def subscribe(self, task_id: str, websocket: WebSocket):
        """订阅任务进度推送"""
```

**存储策略**:
- **内存**: `Dict[str, ConversionTask]` - 快速访问
- **磁盘**: `temp/tasks.json` - 持久化防丢失

---

### 工具链适配器（DockerToolChainAdapter）

**职责**: 封装 Docker 工具链调用，提供统一的转换接口

**设计模式**: 适配器模式

**核心特性**:
- 按需启动 Docker 容器
- 自动路径映射
- 容器自动清理
- 进度实时推送

**接口**:
```python
class DockerToolChainAdapter:
    def convert_model(
        self,
        task_id: str,
        model_path: str,
        config: ConversionConfig
    ) -> str:
        """在 Docker 容器中执行转换"""

    def check_docker(self) -> bool:
        """检查 Docker 是否可用"""

    def check_image(self) -> bool:
        """检查镜像是否存在"""

    def pull_image(self, progress_callback: Callable[[int], None]):
        """拉取镜像（带进度）"""
```

**实现**:
```python
import docker
from pathlib import Path

class DockerToolChainAdapter:
    """Docker 工具链适配器（混合架构核心）"""

    def __init__(self):
        self.client = docker.from_env()
        self.image_name = "camthink/ne301-dev:latest"

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

        # 1. 准备卷映射
        volumes = {
            str(Path(model_path).parent): {
                "bind": "/input",
                "mode": "ro"  # 只读
            },
            str(Path("outputs").absolute()): {
                "bind": "/output",
                "mode": "rw"  # 读写
            }
        }

        # 2. 构建命令
        command = self._build_command(task_id, model_path, config)

        # 3. 运行容器（同步等待）
        # 容器会在完成后自动删除（remove=True）
        logs = self.client.containers.run(
            self.image_name,
            command=command,
            volumes=volumes,
            remove=True,
            detach=False  # 同步等待完成
        )

        # 4. 返回输出路径
        return f"outputs/ne301_model_{task_id}.bin"

    def _build_command(self, task_id: str, model_path: str, config: dict) -> list:
        """构建容器命令"""

        model_filename = Path(model_path).name

        return [
            "python",
            "/workspace/ne301/Script/model_packager.py",
            "create",
            "--model", f"/input/{model_filename}",
            "--config", json.dumps(config),
            "--output", f"/output/ne301_model_{task_id}.bin"
        ]

    def check_docker(self) -> tuple[bool, str]:
        """检查 Docker 状态

        Returns:
            (是否可用, 错误信息)
        """
        try:
            self.client.ping()
            return True, ""
        except docker.errors.DockerException as e:
            return False, str(e)

    def check_image(self) -> bool:
        """检查镜像是否存在"""
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
        """

        try:
            for layer in self.client.images.pull(
                self.image_name,
                stream=True,
                decode=True
            ):
                if progress_callback and "progressDetail" in layer:
                    progress = layer["progressDetail"].get("current", 0)
                    total = layer["progressDetail"].get("total", 100)
                    progress_callback(int(progress / total * 100))

            return True
        except Exception as e:
            logger.error(f"拉取镜像失败: {e}")
            return False
```

**职责**: 编排模型转换流程

**流程**:
```python
async def convert_model(task_id: str, config: ConversionConfig):
    """转换主流程"""

    # 1. 验证阶段（5%）
    update_progress(task_id, 5, "验证文件格式")

    # 2. 量化阶段（10-60%）
    update_progress(task_id, 10, "PyTorch → TFLite")
    await convert_to_tflite(model_path, config)

    update_progress(task_id, 40, "INT8 量化")
    await quantize_model(tflite_path, config)

    # 3. 打包阶段（60-90%）
    update_progress(task_id, 60, "生成 C 模型")
    await generate_c_model(quantized_path, config)

    update_progress(task_id, 80, "打包 .bin 文件")
    await package_model(c_model_path, config)

    # 4. 完成阶段（100%）
    update_progress(task_id, 100, "转换完成")
    return output_path
```

**工具链适配**:
```python
class ToolChainAdapter:
    """工具链适配器"""

    def detect_mode(self) -> str:
        """检测工具链模式"""
        if self._check_docker():
            return "docker"
        elif self._check_local():
            return "local"
        else:
            raise ToolChainNotReadyError()

    def execute_conversion(self, task_id: str, config: dict):
        """执行转换（自动适配模式）"""
        mode = self.detect_mode()

        if mode == "docker":
            return self._convert_with_docker(task_id, config)
        else:
            return self._convert_with_local(task_id, config)
```

---

### 环境检测器（EnvironmentDetector）

**职责**: 检测 Docker 环境，提供安装引导

**检测逻辑**:
```python
class EnvironmentDetector:
    """环境检测器（混合架构 - 仅 Docker）"""

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
                estimated_time="3-5 分钟（取决于网络速度）",
                advice="建议在空闲时进行首次转换，系统将自动拉取镜像"
            )

        # 3. 环境完全就绪
        return EnvironmentStatus(
            status="ready",
            mode="docker",
            message="环境就绪，可以开始转换"
        )
```

---

### 4. WebSocket 处理器

**职责**: 实时进度推送

**协议**:
```typescript
// 客户端 → 服务器
{ "type": "subscribe", "task_id": "xxx" }
{ "type": "unsubscribe", "task_id": "xxx" }
{ "type": "cancel", "task_id": "xxx" }

// 服务器 → 客户端
{ "type": "progress", "task_id": "xxx", "progress": 50, "step": "量化中..." }
{ "type": "completed", "task_id": "xxx", "output": "ne301_model_xxx.bin" }
{ "type": "failed", "task_id": "xxx", "error": "错误信息" }
```

**实现**:
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    while True:
        data = await websocket.receive_json()

        if data["type"] == "subscribe":
            task_id = data["task_id"]
            task_manager.subscribe(task_id, websocket)

        elif data["type"] == "cancel":
            task_id = data["task_id"]
            task_manager.cancel_task(task_id)
```

---

## 🎨 前端架构

### 组件层次

```
App.tsx
├── SetupPage.tsx          # 设置引导页（首次使用）
│   ├── DockerSetupGuide.tsx
│   └── LocalSetupGuide.tsx
│
└── HomePage.tsx           # 主转换页
    ├── Header.tsx         # 顶部导航
    ├── FileUploadArea.tsx # 文件上传
    ├── ConfigSection.tsx  # 配置区域
    │   ├── PresetCard.tsx     # 预设卡片
    │   └── CustomConfigForm.tsx # 自定义表单
    ├── CalibrationUploadArea.tsx # 校准数据集
    ├── ConvertButton.tsx   # 转换按钮
    ├── ProgressSection.tsx # 进度区域
    │   ├── ProgressBar.tsx
    │   ├── LogTerminal.tsx
    │   └── CancelButton.tsx
    └── ResultSection.tsx   # 结果区域
        └── DownloadButton.tsx
```

### 状态管理（Zustand）

```typescript
interface AppState {
  // 环境状态
  envStatus: EnvironmentStatus;
  checkEnvironment: () => Promise<void>;

  // 转换任务
  currentTask: ConversionTask | null;
  taskProgress: number;
  taskStep: string;

  // 操作
  startConversion: (config: ConversionConfig) => Promise<string>;
  cancelConversion: () => Promise<void>;
  downloadResult: () => Promise<void>;
}
```

### WebSocket 集成

```typescript
// hooks/useWebSocket.ts
export function useWebSocket(taskId: string) {
  const [progress, setProgress] = useState(0);
  const [step, setStep] = useState("");

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws`);

    ws.onopen = () => {
      ws.send(JSON.stringify({ type: "subscribe", task_id: taskId }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "progress") {
        setProgress(data.progress);
        setStep(data.step);
      }
    };

    return () => ws.close();
  }, [taskId]);

  return { progress, step };
}
```

---

## 🗂️ 数据模型

### 转换配置（ConversionConfig）

```python
from pydantic import BaseModel

class ConversionConfig(BaseModel):
    """转换配置"""
    model_type: str = "YOLOv8"          # YOLOv8 / YOLOX
    input_size: int = 480              # 256 / 480 / 640
    num_classes: int = 80              # 1-1000
    confidence_threshold: float = 0.25  # 0.01-0.99
    quantization: str = "int8"         # 固定 INT8
    use_calibration: bool = False      # 是否使用校准数据集
```

### 任务状态（ConversionTask）

```python
class ConversionTask(BaseModel):
    """转换任务"""
    task_id: str
    status: str                        # pending/running/completed/failed
    progress: int = 0                 # 0-100
    current_step: str = ""
    config: ConversionConfig
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    output_filename: Optional[str] = None
```

### 环境状态（EnvironmentStatus）

```python
class EnvironmentStatus(BaseModel):
    """环境状态"""
    status: str                        # ready/docker_pull_required/not_configured
    mode: str                          # docker/local/none
    path: Optional[str] = None         # 本地工具路径
    message: Optional[str] = None      # 提示信息
```

---

## 🔄 数据流（混合架构）

### 应用启动流程（极快）⚡️

```
用户启动应用
    ↓
[python -m uvicorn backend.main:app]
    ↓
FastAPI 后端启动（本地 Python）
    ├─ 加载配置
    ├─ 初始化 TaskManager
    ├─ 初始化 DockerToolChainAdapter
    └─ 启动 WebSocket 服务
    ↓
✅ 服务就绪（~2 秒）
    ↓
[浏览器自动打开 http://localhost:8000]
    ↓
环境检测（/api/setup/check）
    ├─ Docker 已安装？
    │   ├─ 是 → 检查镜像
    │   └─ 否 → 显示安装引导
    └─ 镜像已拉取？
        ├─ 是 → 进入主界面
        └─ 否 → 提示首次转换时会拉取
    ↓
用户可以开始使用
```

### 转换执行流程

```
用户上传文件并点击转换
    ↓
[HTTP POST /api/convert]
    ↓
TaskManager.create_task()
    ├─ 生成 task_id
    ├─ 保存文件到本地 uploads/
    └─ 启动后台线程
    ↓
后台线程执行转换
    ├─ 更新状态：pending → running
    ├─ WebSocket 推送：{"type": "started"}
    ↓
    ┌─────────────────────────────────┐
    │  步骤 1: 验证文件（5%）        │
    │  更新进度 + WebSocket 推送      │
    └─────────────────────────────────┘
    ↓
    ┌─────────────────────────────────┐
    │  步骤 2: 调用 Docker 工具链    │
    │  ├─ 首次？→ 拉取镜像（3-5min） │
    │  ├─ 启动容器                   │
    │  ├─ 执行转换（3-5min）         │
    │  └─ 容器自动清理               │
    │                                 │
    │  实时推送进度                   │
    └─────────────────────────────────┘
    ↓
    ┌─────────────────────────────────┐
    │  步骤 3: 转换完成（100%）      │
    │  ├─ 保存输出到 outputs/         │
    │  └─ WebSocket 推送：completed   │
    └─────────────────────────────────┘
    ↓
用户下载结果
```

---

## 🔒 错误处理

### 错误类型

| 错误类型 | HTTP 状态 | 用户提示 |
|---------|----------|---------|
| 文件格式错误 | 400 | "不支持的文件格式，请上传 .pt 文件" |
| 文件过大 | 413 | "文件大小超过 500MB 限制" |
| 工具链未配置 | 503 | "NE301 工具链未配置，请先完成设置" |
| 转换失败 | 500 | "转换失败：{具体错误信息}" |
| 任务超时 | 408 | "转换超时（10分钟），请重试" |

### 错误处理策略

```python
@app.exception_handler(ConversionError)
async def conversion_error_handler(request: Request, exc: ConversionError):
    """转换错误处理"""
    return JSONResponse(
        status_code=500,
        content={
            "error": exc.message,
            "suggestion": exc.suggestion,
            "docs_url": exc.docs_url
        }
    )
```

---

## 🧪 测试策略

### 单元测试

| 模块 | 测试内容 | 覆盖率目标 |
|------|---------|-----------|
| TaskManager | 任务生命周期管理 | 90% |
| Converter | 转换流程（mock 工具） | 80% |
| EnvironmentDetector | 环境检测逻辑 | 85% |
| API 端点 | 请求处理（mock 业务层） | 80% |

### 集成测试

```python
def test_full_conversion_flow():
    """端到端转换流程测试"""
    # 1. 上传模型
    response = client.post("/api/convert", files={"model": ...})
    task_id = response.json()["task_id"]

    # 2. 等待完成
    wait_for_task(task_id, timeout=300)

    # 3. 验证结果
    task = client.get(f"/api/tasks/{task_id}").json()
    assert task["status"] == "completed"
    assert task["output_filename"] is not None
```

### 性能测试

| 指标 | 目标 | 测试方法 |
|------|------|---------|
| API 响应时间 | < 200ms | Apache Bench |
| WebSocket 延迟 | < 100ms | 自定义脚本 |
| 内存占用 | < 500MB | memory_profiler |
| 转换时间 | < 5min | 真实模型测试 |

---

## 🚀 部署架构（混合架构）

### 本地开发

```bash
# 后端（本地 Python）
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 启动服务（2 秒启动）⚡️
uvicorn app.main:app --reload
```

### 生产运行

```bash
# 方式 1: 直接运行
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# 方式 2: 使用启动脚本
./start.sh  # Linux/macOS
start.bat  # Windows
```

### Docker 镜像管理

```bash
# 用户首次转换时自动拉取
# 或手动拉取：
docker pull camthink/ne301-dev:latest

# 查看镜像大小
docker images camthink/ne301-dev
# REPOSITORY              TAG         SIZE
# camthink/ne301-dev      latest      2.8GB
```

### 文件结构（混合架构）

```
ne301-converter/
├── backend/                    # 后端（本地运行）
│   ├── app/
│   │   ├── main.py             # FastAPI 应用入口
│   │   ├── api/                # API 路由
│   │   ├── core/               # 核心业务逻辑
│   │   │   ├── task_manager.py
│   │   │   ├── converter.py
│   │   │   ├── environment.py  # 环境检测
│   │   │   └── docker_adapter.py  # Docker 适配器 ⭐
│   │   └── models/             # 数据模型
│   ├── tests/                  # 测试
│   ├── requirements.txt
│   ├── uploads/                # 上传文件目录
│   └── outputs/                # 输出文件目录
│
├── frontend/                   # 前端（构建后静态文件）
│   ├── src/
│   │   ├── components/         # UI 组件
│   │   ├── pages/              # 页面
│   │   ├── services/           # API 客户端
│   │   ├── store/              # 状态管理
│   │   └── types/              # TypeScript 类型
│   ├── dist/                   # 构建输出（由 FastAPI 服务）
│   └── package.json
│
├── scripts/                    # 工具脚本
│   ├── start.sh                # 启动脚本
│   ├── check-docker.sh         # Docker 检查脚本
│   └── install-docker.sh       # Docker 安装引导
│
└── ne301/                       # 不再包含（由 Docker 镜像提供）
```

---

## 📊 技术栈总结（混合架构）

| 层级 | 技术 | 理由 |
|------|------|------|
| **前端框架** | Preact 10 | 轻量级，兼容 React 生态 |
| **状态管理** | Zustand | 简单，无样板代码 |
| **UI 组件** | Radix UI | 无样式，可访问性强 |
| **样式** | Tailwind CSS | 快速开发，一致性好 |
| **后端框架** | FastAPI | 现代，异步支持，类型安全 |
| **异步执行** | BackgroundTasks + Threading | 简单，满足单任务需求 |
| **实时通信** | WebSocket | 双向通信，低延迟 |
| **数据验证** | Pydantic | 类型安全，自动验证 |
| **工具链隔离** | Docker | 跨平台兼容，环境隔离 |
| **Docker SDK** | docker-py | Python Docker 控制库 |

---

## ⚡ 性能特性（混合架构优势）

### 启动性能

| 操作 | 纯 Docker | 混合架构 | 提升 |
|------|----------|----------|------|
| 首次启动 | 4-6 分钟 | 30 秒 | **8-12x** ⚡️ |
| 后续启动 | 5-10 秒 | 2 秒 | **2.5-5x** ⚡️ |
| 热重载 | 重建镜像 | 自动重载 | **开发体验最佳** |

### 资源占用

| 状态 | 纯 Docker | 混合架构 |
|------|----------|----------|
| **空闲时** | ~500MB（常驻） | ~100MB（仅后端） |
| **转换时** | ~500MB | ~600MB（后端 + Docker） |
| **节省** | - | **400MB（空闲时）** 💾 |

### 开发体验

| 操作 | 纯 Docker | 混合架构 |
|------|----------|----------|
| 代码修改 | 重建镜像 | 自动重载 ⚡️ |
| 调试 | 容器内复杂 | 本地简单 ⚡️ |
| 日志查看 | docker logs | 直接输出 ⚡️ |

---

## 🎯 混合架构核心优势

### 1. 最佳用户体验 ⭐⭐⭐⭐⭐

- 应用**秒级启动**（2 秒）
- 转换时才用 Docker（用户无感知）
- 本地文件访问更快

### 2. 跨平台完美兼容 ⭐⭐⭐⭐⭐

- 支持 macOS（包括 M1/M2）⭐
- 支持 Linux
- 支持 Windows（通过 Docker Desktop）

### 3. 开发体验极佳 ⭐⭐⭐⭐⭐

- 后端热重载（uvicorn --reload）
- 无需频繁重建 Docker 镜像
- 调试更方便（本地 Python）

### 4. 资源优化 ⭐⭐⭐⭐

- 不转换时：仅后端运行（~100MB）
- 转换时：Docker 容器临时启动
- 转换完成：容器自动清理

### 5. 部署简单 ⭐⭐⭐⭐

```bash
# 用户只需：
1. 安装 Docker Desktop（一次性）
2. pip install -r requirements.txt
3. python start.py
```

---

## 🔄 未来扩展性

### Phase 2: 批量转换

```python
# 扩展 TaskManager 支持队列
class TaskManager:
    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=3)
        self.concurrency_limit = 3

    async def create_task(self, config):
        await self.queue.put(config)
        await self._process_queue()
```

### Phase 3: 分布式

```python
# 升级到 Celery + Redis
from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task
def convert_model(task_id, config):
    # 转换逻辑
    pass
```

---

**文档维护**: 本文档随架构演进持续更新
**最后更新**: 2026-03-12
**负责人**: 架构团队
