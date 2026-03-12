# Docker 集成实现真实模型转换

**日期**: 2025-03-12
**状态**: 设计阶段
**优先级**: HIGH（阻塞用户使用核心功能）

---

## 📋 目标

实现真实的模型转换功能，通过 Docker 容器调用 NE301 工具链，将 PyTorch/ONNX 模型量化并转换为 NE301 .bin 部署包。

---

## 🎯 核心需求

### 功能需求
- ✅ 支持通过 Docker 容器执行模型转换
- ✅ 自动拉取 Docker 镜像（首次使用时）
- ✅ 实时报告转换进度（镜像拉取 + 转换过程）
- ✅ 友好的错误提示和自动重试机制
- ✅ 支持校准数据集（可选）

### 非功能需求
- 转换时间：3-5 分钟（取决于模型大小）
- 镜像大小：~3GB（首次下载）
- 并发：单任务执行（避免资源冲突）

---

## 🏗️ 架构设计

### 系统流程

```
用户上传文件 + 配置
    ↓
POST /api/convert
    ↓
创建任务 (task_id)
    ↓
后台任务 _run_conversion()
    ↓
检查 Docker 镜像？
    ├─ 不存在 → 拉取镜像（0-50% 进度）
    └─ 存在 → 跳过
    ↓
调用 DockerToolChainAdapter.convert_model()
    ├─ 运行容器
    ├─ 流式捕获日志
    └─ 更新进度（50-100%）
    ↓
容器完成 → 生成 .bin 文件
    ↓
标记任务完成 → 用户可下载
```

### 组件交互

```python
# convert.py
from app.core.docker_adapter import DockerToolChainAdapter

async def _run_conversion(...):
    adapter = DockerToolChainAdapter()

    # 1. 检查镜像
    if not adapter.check_image():
        # 2. 拉取镜像（带进度）
        adapter.pull_image(progress_callback=...)

    # 3. 执行转换（带日志流）
    output_path = adapter.convert_model(
        task_id, model_path, config
    )

    # 4. 返回结果
    task_manager.complete_task(task_id, output_path)
```

---

## 📦 详细设计

### 1. 镜像拉取集成

**触发时机**: 首次转换或镜像不存在时

**进度报告**:
```python
def pull_progress(progress: int):
    """镜像拉取进度回调"""
    task_manager.update_progress(
        task_id,
        progress // 2,  # 0-50%
        f"正在拉取 Docker 镜像... {progress}%"
    )
```

**用户看到**:
- 0-50%: "正在拉取 Docker 镜像... X%"
- 预计时间：3-5 分钟（取决于网络）

---

### 2. 容器日志流式传输

**实现方式**: 修改 `DockerToolChainAdapter.convert_model()`

**当前签名**:
```python
def convert_model(self, task_id, model_path, config) -> str:
    # 同步执行，无日志流
```

**需要改为**:
```python
def convert_model(
    self,
    task_id,
    model_path,
    config,
    log_callback: Optional[Callable[[str], None]] = None,
    calibration_path: Optional[str] = None,
    yaml_path: Optional[str] = None
) -> str:
    """支持日志流式传输和可选参数"""
    # 运行容器时使用 logs=True
    # 实时捕获并传递日志

    # 添加资源限制
    self.client.containers.run(
        self.image_name,
        command=command,
        volumes=volumes,
        remove=True,
        detach=False,
        mem_limit="2g",      # 限制内存使用
        cpu_count=1          # 限制 CPU 核心
    )
```

**日志解析**:
```python
def parse_docker_log(log_line: str) -> tuple[int, str]:
    """解析容器日志，提取进度和步骤"""
    # 示例日志格式：
    # "Quantizing model... 50%"
    # "Packaging... 80%"

    if "Quantizing" in log_line:
        return (60, "模型量化中...")
    elif "Packaging" in log_line:
        return (80, "打包部署文件...")
    # ...
```

---

### 3. 配置传递

**Pydantic Config → Docker 命令参数**

```python
# ConversionConfig (输入)
{
    "model_type": "YOLOv8",
    "input_size": 480,
    "num_classes": 30,
    "confidence_threshold": 0.25,
    "quantization": "int8"
}

# Docker 命令
python /workspace/ne301/Script/model_packager.py \
    create \
    --model /input/model.pt \
    --config '{"model_type":"YOLOv8",...}' \
    --output /output/ne301_model_{task_id}.bin
```

---

### 4. 错误处理和重试

**自动重试机制**:
```python
MAX_RETRIES = 1

for attempt in range(MAX_RETRIES + 1):
    try:
        output_path = adapter.convert_model(...)
        break  # 成功
    except Exception as e:
        if attempt < MAX_RETRIES:
            logger.warning(f"转换失败，正在重试 ({attempt+1}/{MAX_RETRIES})...")
            task_manager.update_progress(
                task_id,
                current_progress,
                f"转换失败，正在重试..."
            )
            continue
        else:
            # 最后一次失败
            task_manager.fail_task(
                task_id,
                f"转换失败: {str(e)}"
            )
            raise
```

**友好错误提示**:
- Docker 未运行 → "Docker 未启动，请启动 Docker Desktop"
- 镜像拉取失败 → "网络错误，请检查连接"
- 容器执行失败 → 显示容器错误日志
- 模型格式错误 → "不支持的模型格式，请使用 .pt/.pth/.onnx"

---

### 5. 文件路径管理

**卷映射**:
```python
volumes = {
    "/path/to/upload": {"bind": "/input", "mode": "ro"},
    "/path/to/outputs": {"bind": "/output", "mode": "rw"}
}

# 如果有校准数据集，添加额外卷
if calibration_path:
    calibration_dir = os.path.dirname(calibration_path)
    volumes[str(calibration_dir)] = {"bind": "/input", "mode": "ro"}
```

**输出文件**:
- 路径: `outputs/ne301_model_{task_id}.bin`
- 下载端点: `GET /api/download/{task_id}`
- 文件名: `ne301_model_{timestamp}_{task_id}.bin`

**可选参数传递**:
```python
command = [
    "python", "/workspace/ne301/Script/model_packager.py",
    "create",
    "--model", f"/input/{model_filename}",
    "--config", json.dumps(config),
    "--output", f"/output/ne301_model_{task_id}.bin"
]

# 添加校准数据集（如果提供）
if calibration_path:
    command.extend(["--calibration", "/input/calibration.zip"])

# 添加 YAML 文件（如果提供）
if yaml_path:
    command.extend(["--classes", "/input/classes.yaml"])
```

---

## 🔧 实现计划

### 阶段 1: DockerToolChainAdapter 增强
- [ ] 添加 `log_callback` 参数到 `convert_model()`
- [ ] 实现容器日志流式捕获
- [ ] 添加日志解析函数

### 阶段 2: convert.py 集成
- [ ] 移除模拟转换代码
- [ ] 实现镜像拉取逻辑
- [ ] 集成 `convert_model()` 调用
- [ ] 实现进度报告（拉取 + 转换）
- [ ] 添加错误重试机制

### 阶段 3: 测试验证
- [ ] 单元测试：Docker 适配器
- [ ] 集成测试：完整转换流程
- [ ] 手动测试：真实模型转换

---

## ✅ 验收标准

### 功能验收
- [ ] 上传模型 → 点击转换 → 进度 0-100% → 生成 .bin 文件
- [ ] 首次使用自动拉取镜像（显示进度）
- [ ] 日志实时显示转换步骤
- [ ] 转换失败显示清晰错误信息
- [ ] 转换失败自动重试 1 次

### 性能验收
- [ ] 镜像拉取时间：3-5 分钟（~3GB）
- [ ] 模型转换时间：2-5 分钟（YOLOv8n）
- [ ] 内存使用：< 2GB（容器限制）

### 错误处理验收
- [ ] Docker 未安装 → 显示安装指南
- [ ] Docker 未启动 → 提示启动 Docker
- [ ] 网络错误 → 显示网络错误
- [ ] 模型格式错误 → 提示支持的格式

---

## 📝 备注

### Docker 镜像
- 镜像名: `camthink/ne301-dev:latest`
- 大小: ~3GB
- 包含: ST Edge AI + NE301 工具链

### 转换脚本
- 容器内路径: `/workspace/ne301/Script/model_packager.py`
- 命令: `python model_packager.py create --model ... --config ... --output ...`

### 已知限制
- 仅支持 Docker 模式（不支持本地工具链）
- 单任务并发（避免资源冲突）
- 需要网络连接（首次拉取镜像）
- **并发控制**: 使用任务队列或锁机制确保同时只有一个转换任务执行

---

**下一步**: 等待用户批准设计 → 编写实现计划 → 执行实现
