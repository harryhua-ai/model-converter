# NE301 Model Converter

PyTorch 模型转换为 NE301 设备可用 .bin 文件的工具。

## 功能特性

- ✅ **零代码操作** - 界面化操作，无需理解底层流程
- ✅ **端到端自动化** - PyTorch → 量化 → NE301 .bin 全自动
- ✅ **实时反馈** - WebSocket 推送转换进度
- ✅ **跨平台支持** - macOS / Linux / Windows

## 快速开始

### 1. 环境准备

```bash
# 克隆仓库
git clone <repository-url>
cd model-converter

# 创建虚拟环境（Python 3.11/3.12 推荐）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装所有依赖（包含 ML 库）
pip install -r backend/requirements.txt

# 启动 Docker Desktop
# 确保 Docker 正在运行
docker --version
```

### 1.1 可选：配置环境变量

```bash
# 复制环境配置模板
cp backend/.env.example backend/.env

# 根据需要修改配置（可选）
vim backend/.env
```

### 2. 启动服务

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### 3. 访问 Web 界面

打开浏览器访问 http://localhost:8000

## 模型转换

支持将 YOLOv8 PyTorch 模型转换为 NE301 .bin 格式。

**功能特性:**
- ✅ 支持 .pt/.pth 格式
- ✅ 三种转换预设（256/480/640）
- ✅ 自动类别识别（YAML 文件）
- ✅ 校准数据集支持（提高量化精度）
- ✅ 实时进度显示
- ✅ 完整错误处理

详细文档请参阅 [MODEL_CONVERSION.md](backend/docs/MODEL_CONVERSION.md)。

## 使用指南

1. 上传 PyTorch 模型 (.pt/.pth/.onnx)
2. （可选）上传类别定义 YAML 文件
3. 选择预设配置（快速/平衡/高精度）
4. 点击"开始转换"
5. 实时查看进度和日志
6. 转换完成后下载 .bin 文件

## 技术架构

- **前端**: Preact 10 + TypeScript + Tailwind CSS
- **后端**: Python 3.11 + FastAPI + Docker
- **工具链**: NE301 Docker 容器

## 开发

### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest

# 启动开发服务器
python -m uvicorn app.main:app --reload
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
```

### 项目结构

```
model-converter/
├── backend/              # 后端代码
│   ├── app/
│   │   ├── main.py      # FastAPI 应用入口
│   │   ├── api/         # API 路由
│   │   ├── core/        # 核心逻辑
│   │   │   ├── converter.py      # 模型转换器
│   │   │   └── docker_adapter.py # Docker 适配器
│   │   └── models/      # 数据模型
│   ├── tools/           # ST 量化脚本
│   ├── docs/            # 文档
│   └── requirements.txt
├── frontend/            # 前端代码
│   ├── src/
│   │   ├── pages/      # 页面组件
│   │   ├── components/ # UI 组件
│   │   └── lib/        # 工具函数
│   └── package.json
└── scripts/            # 启动脚本
    ├── start.sh        # Linux/macOS
    └── start.bat       # Windows
```

## 环境变量

创建 `backend/.env` 文件：

```env
# Docker 配置
NE301_DOCKER_IMAGE=your-registry/ne301-converter:latest

# 服务器配置
HOST=0.0.0.0
PORT=8000

# 日志级别
LOG_LEVEL=INFO
```

## 故障排除

### Docker 相关问题

**问题**: Docker 未安装或未运行
**解决**: 访问 [Docker 官网](https://www.docker.com/products/docker-desktop/) 下载安装

**问题**: 镜像拉取失败
**解决**:
- 检查网络连接
- 配置 Docker 镜像加速器
- 手动拉取镜像: `docker pull camthink/ne301-dev:latest`

### 转换相关问题

**问题**: 转换失败
**解决**:
1. 检查上传的模型格式是否正确（.pt/.pth）
2. 查看实时日志了解详细错误信息
3. 确认模型输入尺寸符合要求

**问题**: ML 库导入错误（No module named 'ultralytics' 或 'tensorflow'）
**解决**:
1. 确认使用 Python 3.11/3.12 环境（不支持 3.14）
2. 安装 ML 依赖: `pip install ultralytics tensorflow hydra-core opencv-python`
3. 重新启动服务

**问题**: 量化失败
**解决**:
- 检查校准数据集格式（必须是包含 .jpg/.png 的 ZIP 文件）
- 确保校准数据至少包含 32 张图片

**问题**: 转换速度慢
**解决**:
- 选择"快速"预设配置
- 减小模型输入尺寸（256x256）
- 检查系统资源使用情况

详细故障排查请参阅 [MODEL_CONVERSION.md](backend/docs/MODEL_CONVERSION.md)。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题或建议，请通过以下方式联系：

- GitHub Issues: [项目地址](https://github.com/yourusername/model-converter)
- Email: your.email@example.com
