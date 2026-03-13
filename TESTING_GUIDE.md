# Model Converter 测试指南

## 🚀 快速启动

### 1. 启动 Docker Desktop

**macOS**: 打开 Applications 文件夹中的 Docker Desktop

等待 Docker Desktop 完全启动（顶部菜单栏图标稳定）

### 2. 启动服务

**方式 A: 使用启动脚本**（推荐）
```bash
./start-local.sh
```

**方式 B: 手动启动**
```bash
# 激活虚拟环境
source venv/bin/activate

# 进入后端目录
cd backend

# 启动服务
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 验证服务

**访问 API 文档**:
- 主页: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/api/health

**预期输出**:
```json
{
  "status": "healthy",
  "docker": "available",
  "ne301_image": "ready"
}
```

## 🧪 测试转换功能

### 准备测试文件

**1. YOLOv8 模型** (.pt 文件):
```bash
# 如果没有真实模型，可以使用测试文件
# 或从 https://github.com/ultralytics/assets/releases 下载
```

**2. 类别定义文件** (classes.yaml):
```yaml
classes:
  - name: person
    id: 0
  - name: car
    id: 1
  - name: dog
    id: 2
  # ... 更多类别
```

**3. 校准数据集** (calibration.zip):
- 包含 32-100 张图片（.jpg 或 .png）
- 图片尺寸与模型输入尺寸一致（如 640x640）

### 使用 Web 界面测试

1. 打开浏览器访问: http://localhost:8000
2. 上传模型文件（.pt 或 .pth）
3. 配置参数:
   - 模型类型: YOLOv8
   - 输入尺寸: 640
   - 类别数量: 80
4. 上传类别文件（可选）
5. 上传校准数据集（可选，但推荐）
6. 点击"开始转换"

### 使用 API 测试

**完整转换请求**:
```bash
curl -X POST http://localhost:8000/api/convert \
  -F "model_file=@yolov8n.pt" \
  -F 'config={"model_type": "YOLOv8", "input_size": 640, "num_classes": 80}' \
  -F "yaml_file=@classes.yaml" \
  -F "calibration_dataset=@calibration.zip"
```

**预期响应**:
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "pending",
  "message": "转换任务已创建"
}
```

**查看任务状态**:
```bash
curl http://localhost:8000/api/tasks/abc123-def456-ghi789
```

## ✅ 验证 NE301 配置改进

### 1. 检查生成的 JSON 配置

转换完成后，检查生成的配置文件:

```bash
# 查找最新的任务 ID
TASK_ID=$(ls -t backend/outputs/*.json | head -1 | xargs basename | sed 's/model_\(.*\)\.json/\1/')

# 查看 JSON 配置
cat backend/ne301/Model/weights/model_${TASK_ID}.json | jq '.'
```

### 2. 验证关键字段

**检查量化参数**:
```bash
cat backend/ne301/Model/weights/model_*.json | jq '{
  version: .version,
  scale: .output_spec.outputs[0].scale,
  zero_point: .output_spec.outputs[0].zero_point,
  total_boxes: .postprocess_params.total_boxes,
  exec_memory: .memory.exec_memory_pool,
  ext_memory: .memory.ext_memory_pool
}'
```

**预期输出**:
```json
{
  "version": "1.0.0",
  "scale": 0.003921568859368563,
  "zero_point": -128,
  "total_boxes": 8400,
  "exec_memory": 1073741824,
  "ext_memory": 2147483648
}
```

### 3. 对比改进前后

**之前** (4 个字段):
```json
{
  "input_size": 640,
  "num_classes": 80,
  "model_type": "YOLOv8",
  "quantization": "int8"
}
```

**现在** (20+ 字段):
```json
{
  "version": "1.0.0",
  "model_info": {...},
  "input_spec": {...},
  "output_spec": {
    "outputs": [{
      "scale": 0.003921568859368563,
      "zero_point": -128,
      "width": 8400
    }]
  },
  "memory": {...},
  "postprocess_params": {...}
}
```

## 📊 检查日志

**实时查看转换日志**:
```bash
# 查看后端日志
tail -f backend/logs/converter.log

# 或在终端中直接查看输出
# 服务启动的终端会显示实时日志
```

**关键日志信息**:
```
[INFO] 步骤 1: 导出 TFLite 模型...
[INFO] ✅ TFLite 导出成功: /app/outputs/model.tflite
[INFO] 步骤 2: 量化模型...
[INFO] ✅ 提取量化参数: scale=0.003921568859368563, zero_point=-128
[INFO] ✅ 计算 total_boxes: 8400
[INFO] ✅ NE301 JSON 配置生成完成
[INFO] 步骤 3: 准备 NE301 项目...
[INFO] 步骤 4: 调用 NE301 容器打包...
[INFO] ✅ 转换成功: /app/outputs/ne301_model_xxx.bin
```

## 🔍 故障排查

### 问题 1: Docker 不可用

**错误**: `Docker 不可用: Docker client not initialized`

**解决**:
1. 确保 Docker Desktop 正在运行
2. 检查 Docker 套接字: `ls -la /var/run/docker.sock`
3. 重启 Docker Desktop

### 问题 2: NE301 镜像不存在

**错误**: `NE301 镜像不存在`

**解决**:
```bash
docker pull camthink/ne301-dev:latest
```

### 问题 3: NumPy 版本不兼容

**错误**: `NumPy 2.x 与 TensorFlow 不兼容`

**解决**:
```bash
source venv/bin/activate
pip install "numpy<2.0"
```

### 问题 4: 转换失败

**检查步骤**:
1. 查看后端日志: `tail -f backend/logs/converter.log`
2. 检查上传的文件: `ls -la backend/uploads/`
3. 检查输出目录: `ls -la backend/outputs/`
4. 检查 NE301 目录: `ls -la backend/ne301/`

## 📝 测试检查清单

- [ ] Docker Desktop 已启动
- [ ] 后端服务正常运行（http://localhost:8000）
- [ ] API 文档可访问（http://localhost:8000/docs）
- [ ] 健康检查通过（http://localhost:8000/api/health）
- [ ] 可以上传模型文件
- [ ] 转换任务创建成功
- [ ] 转换进度正常更新
- [ ] 生成的 JSON 配置包含 20+ 字段
- [ ] JSON 配置包含量化参数（scale, zero_point）
- [ ] JSON 配置包含 total_boxes
- [ ] JSON 配置包含内存池配置
- [ ] 转换完成，生成 .bin 或 .tflite 文件

## 🎯 测试成功标准

**基础功能**:
- ✅ 服务正常启动
- ✅ API 端点可访问
- ✅ 文件上传功能正常

**核心功能**:
- ✅ 转换任务创建成功
- ✅ 转换流程完整执行
- ✅ 生成有效的输出文件

**配置改进验证**:
- ✅ JSON 配置包含 20+ 字段
- ✅ 自动提取量化参数
- ✅ 正确计算 total_boxes
- ✅ 动态计算内存池
- ✅ 包含 class_names

**性能和稳定性**:
- ✅ 没有崩溃或错误
- ✅ 日志输出清晰
- ✅ 降级策略正常工作（如参数提取失败时使用默认值）

---

**准备好测试了吗？**

启动 Docker Desktop，然后运行 `./start-local.sh` 开始测试！🚀
