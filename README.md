# NE301 Model Converter

PyTorch 模型转换为 NE301 设备可用 .bin 文件的工具。

## 功能特性

- ✅ **零代码操作** - 界面化操作，无需理解底层流程
- ✅ **端到端自动化** - PyTorch → 量化 → NE301 .bin 全自动
- ✅ **实时反馈** - WebSocket 推送转换进度
- ✅ **跨平台支持** - macOS / Linux / Windows

## 快速开始

### 1. 系统要求

- Python 3.11+
- Docker Desktop（已安装并运行）
- Node.js 18+ (仅开发环境)

### 2. 启动应用

```bash
# Linux/macOS
./scripts/start.sh

# Windows
scripts\start.bat
```

### 3. 打开浏览器

访问 http://localhost:8000

首次使用会引导您安装 Docker 并拉取工具镜像。

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
│   │   ├── services/    # 业务逻辑
│   │   └── models/      # 数据模型
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
- 手动拉取镜像: `docker pull your-registry/ne301-converter:latest`

### 转换相关问题

**问题**: 转换失败
**解决**:
1. 检查上传的模型格式是否正确
2. 查看实时日志了解详细错误信息
3. 确认模型输入尺寸符合要求

**问题**: 转换速度慢
**解决**:
- 选择"快速"预设配置
- 减小模型输入尺寸
- 检查系统资源使用情况

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题或建议，请通过以下方式联系：

- GitHub Issues: [项目地址](https://github.com/yourusername/model-converter)
- Email: your.email@example.com
