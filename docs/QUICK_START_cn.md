# NE301 Model Converter - 快速开始指南

5 分钟完成你的第一个模型转换！

---

## 前置要求

- **Docker Desktop** 已安装并运行
- **4GB 内存** 可用
- **网络连接**（首次下载镜像需要）

---

## 快速开始（3 步）

### 第 1 步：拉取依赖

```bash
docker pull camthink/ne301-dev:latest
```

### 第 2 步：启动服务

```bash
docker-compose up -d
```

首次构建需要约 2 分钟。

### 第 3 步：访问 Web 界面

打开浏览器，访问：

```
http://localhost:8000
```

**完成！** 服务已启动运行。

---

## 第一个模型转换

### 1. 准备文件

你需要：
- **PyTorch 模型文件**（`.pt` 或 `.pth`）
- **类别定义 YAML**（可选，用于 YOLO 模型）
- **校准数据集**（可选，提高量化精度）

### 2. 上传并转换

1. 点击 **"选择模型文件"**，选择你的 `.pt` 文件
2. （可选）上传 `classes.yaml` 定义类别名称
3. （可选）上传校准数据集（包含 32+ 张图片的 ZIP 文件）
4. 选择预设配置：
   - **快速模式**: 256x256，转换最快
   - **平衡模式**: 480x480，推荐使用
   - **高精度模式**: 640x640，精度最高
5. 点击 **"开始转换"**

### 3. 监控进度

实时查看进度条和日志：
- 步骤 1/4: PyTorch → TFLite (0-30%)
- 步骤 2/4: TFLite 量化 (30-60%)
- 步骤 3/4: NE301 准备 (60-70%)
- 步骤 4/4: NE301 打包 (70-100%)

### 4. 下载结果

转换完成后，点击 **"下载 .bin 文件"** 获取 NE301 部署包。

---

## 示例文件

没有模型？使用我们的测试文件：

```bash
# 下载示例 YOLOv8 模型
wget https://github.com/ultralytics/assets/raw/main/yolov8n.pt

# 创建示例类别定义
cat > classes.yaml << EOF
names:
  - person
  - bicycle
  - car
  - motorcycle
  - airplane
  - bus
  - train
  - truck
  - boat
EOF
```

---

## 常用命令

```bash
# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 检查服务状态
docker-compose ps
```

---

## 故障排查

### Docker 未运行

**错误**: `Cannot connect to the Docker daemon`

**解决**: 启动 Docker Desktop

### 端口被占用

**错误**: `port is already allocated`

**解决**:
```bash
# 查找并停止占用进程
lsof -i :8000
docker-compose down
docker-compose up -d
```

### 镜像拉取失败

**解决**:
```bash
# 检查网络并手动拉取
docker pull camthink/ne301-dev:latest
```

### 转换失败

**解决**:
1. 检查模型格式（必须是 `.pt` 或 `.pth`）
2. 在 Web 界面查看详细日志
3. 确保模型与 YOLOv8 兼容

---

## 下一步

- 阅读 [用户指南](USER_GUIDE_cn.md) 了解详细功能
- 查看 [Docker 部署指南](../README.docker_cn.md) 了解高级配置
- 参考 [开发文档](../CLAUDE.md) 了解技术细节

---

## 获取帮助

- **文档**: [用户指南](USER_GUIDE_cn.md)
- **问题反馈**: 在 GitHub Issues 上提交
- **日志**: 使用 `docker-compose logs -f` 查看详情

---

**最后更新**: 2026-03-18
