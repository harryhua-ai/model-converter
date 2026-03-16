# NE301 打包流程详解

## 概述

本文档详细说明 NE301 模型打包流程，包括 OTA 固件包和纯模型包两种方式。

## 打包方式对比

| 方式 | 推荐度 | 优点 | 缺点 | 适用场景 |
|------|--------|------|------|----------|
| OTA 固件包 | ⭐⭐⭐⭐⭐ | 可直接 OTA 部署 | 文件较大 | 生产环境部署 |
| 纯模型包 | ⭐⭐⭐⭐ | 文件小、更新快 | 需要手动部署 | 开发测试 |
| TFLite 输出 | ⭐⭐ | 最简单 | 需要手动打包 | 调试阶段 |

## 完整打包流程

### 流程图

```
量化 TFLite 模型 (int8)
    ↓
[步骤 3] 准备 NE301 项目结构
    ├─ 创建目录结构
    ├─ 生成 JSON 配置
    └─ 更新 Makefile
    ↓
[步骤 4] NE301 打包
    ├─ 优先: OTA 固件包
    ├─ 备选: 纯模型包
    └─ 降级: TFLite 输出
    ↓
NE301 .bin 文件
```

## 步骤 3: 准备 NE301 项目

### 目录结构

```
ne301/
├── models/
│   └── model_name/
│       ├── model.tflite         # 量化模型
│       └── model.json           # 模型配置
├── include/
│   └── model_name.h             # 头文件
├── Makefile                      # 构建配置
└── stedgeai_models/              # ST 工具链
```

### JSON 配置文件

`models/model_name/model.json`:

```json
{
  "name": "yolov8n",
  "version": "1.0.0",
  "input_shape": [1, 640, 640, 3],
  "output_shape": [1, 34, 1344],
  "num_classes": 80,
  "confidence_threshold": 0.25,
  "nms_threshold": 0.45,
  "created_at": "2026-03-16T12:00:00Z"
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| name | str | 模型名称 |
| version | str | 版本号 |
| input_shape | list | 输入形状 [N, H, W, C] |
| output_shape | list | 输出形状 |
| num_classes | int | 类别数量 |
| confidence_threshold | float | 置信度阈值 |
| nms_threshold | float | NMS 阈值 |

### Makefile 更新

```makefile
# 模型名称
MODEL_NAME = yolov8n

# 输入尺寸
MODEL_INPUT_SIZE = 640

# 类别数量
MODEL_NUM_CLASSES = 80

# 输出形状
MODEL_OUTPUT_SHAPE = 1344
```

## 步骤 4: NE301 打包

### 方式 1: OTA 固件包（推荐）

#### 流程图

```
运行 make pkg-model
    ↓
检查 stedgeai_models/
    ├─ 存在 → 继续
    └─ 不存在 → 降级到 TFLite 输出
    ↓
生成 Model Package
    ├─ model.tflite
    ├─ model.json
    └─ metadata.bin
    ↓
添加 OTA Header (1024 字节)
    ├─ Magic Number: 0x4F544131
    ├─ Version: 3.0
    ├─ Model Size
    └─ CRC32 Checksum
    ↓
ne301_model_{task_id}.bin
```

#### OTA Header 结构（1024 字节）

```
偏移量  长度    字段              说明
------  ------  --------------    ----------------
0       4       magic             魔数: 0x4F544131
4       4       version           版本: 3
8       4       model_size        模型大小（字节）
12      4       crc32             CRC32 校验和
16      1008    reserved          保留字段
------  ------  --------------    ----------------
总计    1024    N/A               OTA Header 大小
```

#### 生成 OTA 包

```python
def _build_ota_package(self, task_id: str, ne301_project_path: Path) -> str:
    """构建 OTA 固件包"""
    # 1. 检查 stedgeai_models
    if not (ne301_project_path / "stedgeai_models").exists():
        logger.warning("stedgeai_models 不存在，无法生成 OTA 包")
        return None

    # 2. 运行 make pkg-model
    self._run_make_in_container(ne301_project_path)

    # 3. 查找生成的 .bin 文件
    bin_files = list((ne301_project_path / "build").glob("*.bin"))

    if not bin_files:
        logger.error("OTA 包生成失败")
        return None

    # 4. 添加 OTA Header
    ota_bin = self._add_ota_header(task_id, bin_files[0])

    return ota_bin
```

### 方式 2: 纯模型包

#### 流程图

```
运行 make model
    ↓
生成纯模型包
    ├─ model.tflite
    └─ model.json
    ↓
打包为 .bin 文件
    ↓
ne301_model_{task_id}.bin
```

#### 生成纯模型包

```python
def _build_model_package(self, task_id: str, ne301_project_path: Path) -> str:
    """构建纯模型包"""
    # 1. 运行 make model
    self._run_make_in_container(ne301_project_path)

    # 2. 查找生成的 .bin 文件
    bin_files = list((ne301_project_path / "build").glob("*.bin"))

    if not bin_files:
        logger.error("模型包生成失败")
        return None

    # 3. 复制到输出目录
    output_bin = self.outputs_dir / f"ne301_model_{task_id}.bin"
    shutil.copy2(bin_files[0], output_bin)

    return str(output_bin)
```

### 方式 3: TFLite 输出（降级方案）

#### 使用场景

- `stedgeai_models` 不存在
- Make 失败
- 开发调试阶段

#### 输出内容

```
quantized_model_{task_id}.tflite  # 量化 TFLite 模型
```

#### 实现代码

```python
def _provide_fallback_output(self, task_id: str, quantized_tflite: str) -> str:
    """提供降级输出（TFLite 文件）"""
    logger.warning("⚠️  注意: TFLite 格式需要手动打包为 NE301 格式")

    output_path = self.outputs_dir / f"quantized_model_{task_id}.tflite"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(quantized_tflite, output_path)

    return str(output_path)
```

## 打包优先级

系统按以下顺序尝试打包：

1. **OTA 固件包** → 如果成功，返回 `.bin` 文件
2. **纯模型包** → 如果 OTA 失败，尝试纯模型包
3. **TFLite 输出** → 如果所有打包失败，返回 TFLite 文件

## 性能基准

### 打包时间（参考值）

| 输入尺寸 | 准备项目 | OTA 打包 | 纯模型包 | 总耗时 |
|---------|---------|---------|---------|--------|
| 256 | 5-8s | 60-90s | 30-45s | ~1min |
| 480 | 5-8s | 90-120s | 45-60s | ~2min |
| 640 | 5-8s | 120-180s | 60-90s | ~3min |

### 文件大小对比

| 模型类型 | TFLite | 纯模型包 | OTA 包 |
|---------|--------|---------|--------|
| YOLOv8n (640) | 1.6 MB | 1.7 MB | 2.1 MB |
| YOLOv8s (640) | 5.7 MB | 5.8 MB | 6.2 MB |
| YOLOv8m (640) | 13.4 MB | 13.5 MB | 13.9 MB |

## 故障排查

### 错误：stedgeai_models 不存在

**症状**:
```
WARNING: stedgeai_models 不存在，无法生成 OTA 包
```

**原因**:
NE301 工具链未正确配置

**解决**:
1. 检查 NE301 项目完整性
2. 确认 `stedgeai_models/` 目录存在
3. 重新初始化 NE301 项目

### 错误：make 失败

**症状**:
```
ERROR: Make 失败，退出码: 2
```

**原因**:
- Makefile 配置错误
- 模型文件缺失
- 权限问题

**解决**:
1. 检查 Makefile 配置
2. 确认模型文件存在
3. 查看详细错误日志

### 错误：OTA Header 添加失败

**症状**:
```
ERROR: 无法添加 OTA header
```

**原因**:
- 文件权限不足
- 磁盘空间不足
- 输出目录不存在

**解决**:
1. 检查文件权限
2. 确认磁盘空间充足
3. 创建输出目录

## OTA 部署指南

### 部署步骤

1. **上传 .bin 文件**
   ```bash
   scp ne301_model_task-123.bin user@device:/tmp/
   ```

2. **验证 OTA 包**
   ```bash
   # 检查文件大小
   ls -lh /tmp/ne301_model_task-123.bin

   # 验证魔数
   hexdump -C /tmp/ne301_model_task-123.bin | head -1
   # 预期输出: 31 54 41 4f (OTA1 的十六进制)
   ```

3. **执行 OTA 更新**
   ```bash
   # 假设设备支持 OTA 命令
   ota-update /tmp/ne301_model_task-123.bin
   ```

4. **验证部署**
   ```bash
   # 重启设备
   reboot

   # 检查模型加载
   model-check
   ```

### OTA Header 验证

```python
def validate_ota_header(bin_path: str) -> bool:
    """验证 OTA Header"""
    with open(bin_path, 'rb') as f:
        header = f.read(1024)

        # 检查魔数
        magic = int.from_bytes(header[0:4], 'little')
        if magic != 0x4F544131:  # "OTA1"
            return False

        # 检查版本
        version = int.from_bytes(header[4:8], 'little')
        if version != 3:
            return False

        # 检查模型大小
        model_size = int.from_bytes(header[8:12], 'little')
        actual_size = os.path.getsize(bin_path) - 1024
        if model_size != actual_size:
            return False

        # 验证 CRC32
        import zlib
        crc_stored = int.from_bytes(header[12:16], 'little')
        model_data = open(bin_path, 'rb').read()[1024:]
        crc_computed = zlib.crc32(model_data) & 0xFFFFFFFF
        if crc_stored != crc_computed:
            return False

        return True
```

## 参考

- [NE301 技术文档](https://www.st.com/en/microcontrollers-microprocessors/stm32-ai-ecosystem.html)
- [ST Edge AI 用户指南](https://www.st.com/resource/en/user_manual/dm00684350.pdf)
- [OTA 更新协议](https://www.st.com/resource/en/application_note/dm00507447.pdf)