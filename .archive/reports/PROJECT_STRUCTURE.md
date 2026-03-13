# YOLO 模型转换工具 - 项目结构

```
model-converter/
├── 📁 backend/                    # FastAPI 后端服务
│   ├── 📁 app/
│   │   ├── 📁 api/               # API 路由层
│   │   │   ├── __init__.py       # 路由汇总
│   │   │   ├── models.py         # 模型转换 API (上传/下载)
│   │   │   ├── tasks.py          # 任务管理 API (查询/监控)
│   │   │   └── presets.py        # 配置预设 API
│   │   ├── 📁 core/              # 核心配置
│   │   │   ├── config.py         # 应用配置 (Pydantic Settings)
│   │   │   └── logging.py        # 日志配置 (structlog)
│   │   ├── 📁 models/            # 数据模型
│   │   │   └── schemas.py        # Pydantic 模型定义
│   │   ├── 📁 services/          # 业务逻辑层
│   │   │   ├── conversion.py     # 模型转换服务 (核心)
│   │   │   └── task_manager.py   # 任务状态管理
│   │   └── 📁 workers/           # Celery Workers
│   │       └── celery_app.py     # Celery 配置
│   ├── main.py                   # FastAPI 应用入口
│   ├── Dockerfile                # 后端 Docker 镜像
│   ├── requirements.txt          # Python 依赖
│   └── .env.example              # 环境变量示例
│
├── 📁 frontend/                   # Preact 前端应用
│   ├── 📁 src/
│   │   ├── 📁 pages/             # 页面组件
│   │   │   ├── HomePage.tsx      # 首页 (上传/配置)
│   │   │   └── TaskDetailPage.tsx # 任务详情 (进度监控)
│   │   ├── 📁 components/        # 可复用组件 (待扩展)
│   │   ├── 📁 services/          # API 服务层
│   │   │   └── api.ts            # HTTP 客户端 & WebSocket
│   │   ├── 📁 store/             # 状态管理
│   │   │   └── app.ts            # Zustand 全局状态
│   │   ├── 📁 hooks/             # 自定义 Hooks
│   │   │   └── index.ts          # useWebSocket, useFileUpload
│   │   ├── 📁 types/             # TypeScript 类型
│   │   │   └── index.ts          # 类型定义
│   │   ├── 📁 styles/            # 样式文件
│   │   │   ├── index.css         # Tailwind CSS
│   │   │   └── globals.css       # 全局样式
│   │   ├── App.tsx               # 主应用组件
│   │   └── main.tsx              # 应用入口
│   ├── 📁 public/                # 静态资源
│   ├── Dockerfile                # 前端 Docker 镜像
│   ├── nginx.conf                # Nginx 配置
│   ├── package.json              # Node 依赖
│   ├── vite.config.ts            # Vite 构建配置
│   └── tailwind.config.js        # Tailwind CSS 配置
│
├── docker-compose.yml            # 服务编排 (Redis, Celery, Backend, Frontend)
├── start.sh                      # 快速启动脚本
├── .gitignore                    # Git 忽略规则
├── README.md                     # 项目说明文档
├── IMPLEMENTATION.md             # 实施总结文档
└── PROJECT_STRUCTURE.md          # 本文件
```

## 技术栈总览

### 后端技术栈
- **语言**: Python 3.11
- **框架**: FastAPI 0.115.0
- **任务队列**: Celery 5.4.0 + Redis 7
- **AI/ML**: 
  - Ultralytics 8.3.0 (YOLOv8/v11)
  - PyTorch 2.5.0
  - TensorFlow 2.18.0
- **日志**: structlog 24.4.0
- **验证**: Pydantic 2.10.0

### 前端技术栈
- **语言**: TypeScript 5.7
- **框架**: Preact 10.26
- **构建**: Vite 7.0
- **UI**: Radix UI + Tailwind CSS 4
- **状态**: Zustand 5.0.8
- **路由**: preact-router 4.1.2
- **HTTP**: axios 1.11.0
- **WebSocket**: 原生 WebSocket API

### 基础设施
- **容器**: Docker 20.10+
- **编排**: Docker Compose 3.8
- **反向代理**: Nginx (Alpine)
- **缓存**: Redis 7 (Alpine)

## 数据流向

```
用户浏览器
    ↓ [HTTP/WebSocket]
Nginx (反向代理)
    ↓ [HTTP]
FastAPI 后端
    ↓ [Redis]
Celery Worker
    ↓ [subprocess]
转换脚本 (generate-reloc-model.sh)
    ↓
输出 .bin 文件
    ↓ [HTTP]
用户下载
```

## API 端点总览

### 模型管理 API
- `POST /api/v1/models/upload` - 上传模型并启动转换
- `GET /api/v1/models/download/{task_id}` - 下载转换后的模型
- `DELETE /api/v1/models/tasks/{task_id}` - 删除任务

### 任务管理 API
- `GET /api/v1/tasks` - 获取任务列表
- `GET /api/v1/tasks/{task_id}` - 获取任务详情
- `WS /api/v1/ws/tasks/{task_id}/progress` - 实时进度推送

### 配置预设 API
- `GET /api/v1/presets` - 获取所有预设
- `GET /api/v1/presets/{preset_id}` - 获取指定预设

## 配置文件说明

### 后端配置 (.env)
```bash
# API 配置
API_PREFIX=/api/v1
HOST=0.0.0.0
PORT=8000

# 文件存储
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=524288000  # 500MB

# Redis/Celery
REDIS_HOST=redis
CELERY_BROKER_URL=redis://redis:6379/0

# NE301 项目路径
NE301_PROJECT_PATH=/workspace
```

### 前端配置 (vite.config.ts)
```typescript
server: {
  proxy: {
    '/api': 'http://localhost:8000',
    '/ws': 'ws://localhost:8000',
  }
}
```

## 开发指南

### 后端开发
```bash
cd model-converter/backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn main:app --reload
```

### 前端开发
```bash
cd model-converter/frontend

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev

# 构建生产版本
pnpm build
```

### Docker 开发
```bash
cd model-converter

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 核心模块说明

### ConversionService (backend/app/services/conversion.py)
**职责**: 实现完整的模型转换流程

**核心方法**:
- `convert_model()` - 主转换流程
- `_convert_to_tflite()` - PyTorch → TFLite
- `_generate_network_bin()` - TFLite → C 模型
- `_generate_config_json()` - 生成配置文件
- `_package_model()` - 打包最终 .bin

**依赖**:
- Ultralytics YOLO
- generate-reloc-model.sh
- model_packager.py

### TaskManager (backend/app/services/task_manager.py)
**职责**: 管理转换任务的生命周期

**核心方法**:
- `create_task()` - 创建新任务
- `get_task()` - 获取任务详情
- `update_task()` - 更新任务状态
- `subscribe_task_updates()` - WebSocket 订阅

**特性**:
- 内存存储 (生产环境需改用 Redis)
- 异步事件通知
- 自动清理过期文件

### WebSocketClient (frontend/src/services/api.ts)
**职责**: 管理与服务器的实时连接

**核心方法**:
- `connect()` - 建立 WebSocket 连接
- `disconnect()` - 断开连接
- `isConnected()` - 检查连接状态

**特性**:
- 自动重连 (最多 5 次)
- 指数退避延迟
- 心跳检测

## 扩展指南

### 添加新的配置预设
编辑 `backend/app/api/presets.py`:
```python
PRESETS.append(ConfigPreset(
    id="your-preset-id",
    name="预设名称",
    description="预设描述",
    config={...},
))
```

### 添加新的 API 端点
1. 在 `backend/app/api/` 创建新模块
2. 在 `backend/app/api/__init__.py` 注册路由
3. 在 `frontend/src/services/api.ts` 添加客户端方法

### 添加新的前端页面
1. 在 `frontend/src/pages/` 创建组件
2. 在 `frontend/src/App.tsx` 添加路由
3. 更新导航菜单

## 性能优化建议

### 后端优化
- 使用 Redis 缓存频繁访问的数据
- 限制并发任务数量 (MAX_CONCURRENT_TASKS)
- 启用 HTTP/2
- 使用 Nginx gzip 压缩

### 前端优化
- 代码分割 (React.lazy)
- 图片懒加载
- CDN 加速静态资源
- 浏览器缓存策略

### 转换优化
- 使用 GPU 加速 (CUDA)
- 预加载常用模型
- 批处理多个小任务
- 缓存中间结果

## 安全建议

1. **文件上传验证**
   - 文件类型检查 (魔数验证)
   - 文件大小限制
   - 病毒扫描

2. **API 安全**
   - JWT 认证
   - 速率限制
   - CORS 限制
   - SQL 注入防护

3. **数据安全**
   - 敏感配置加密
   - 定期清理临时文件
   - 访问日志记录
   - 错误信息脱敏

## 测试策略

### 后端测试
```bash
cd backend
pytest --cov=app --cov-report=html
```

### 前端测试
```bash
cd frontend
pnpm test --coverage
```

### 端到端测试
```bash
# 使用 Playwright
cd frontend
pnpm test:e2e
```

## 部署检查清单

- [ ] 更新 SECRET_KEY
- [ ] 配置 HTTPS 证书
- [ ] 设置防火墙规则
- [ ] 配置日志轮转
- [ ] 设置监控告警
- [ ] 备份策略
- [ ] 性能测试
- [ ] 安全扫描

## 常见问题

**Q: 如何增加上传文件大小限制？**
A: 修改 `backend/.env` 中的 `MAX_UPLOAD_SIZE` 和 `nginx.conf` 中的 `client_max_body_size`

**Q: 如何添加新的模型类型支持？**
A: 1. 在 `schemas.py` 添加枚举值
   2. 在 `conversion.py` 添加转换逻辑
   3. 更新前端表单

**Q: WebSocket 连接频繁断开？**
A: 检查 Nginx 配置中的 `proxy_read_timeout` 和 `proxy_send_timeout`

**Q: 转换任务卡住不动？**
A: 查看 Celery Worker 日志: `docker-compose logs -f celery-worker`

---

**文档版本**: v1.0.0
**最后更新**: 2026-03-09
