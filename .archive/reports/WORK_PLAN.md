# YOLO 模型转换工具 - 工作计划与任务清单

**项目状态**: Phase 1 (MVP) 基本完成 - 90%
**最后更新**: 2026-03-09
**项目路径**: `/Users/harryhua/Documents/GitHub/ne301/model-converter/`

---

## ✅ 已完成的工作

### Phase 1: MVP 核心功能

#### 后端开发（FastAPI）
- ✅ FastAPI 应用框架搭建
- ✅ 完整的 API 端点实现
  - `POST /api/v1/models/upload` - 模型上传
  - `GET /api/v1/models/download/{task_id}` - 下载结果
  - `GET /api/v1/tasks` - 任务列表
  - `GET /api/v1/tasks/{task_id}` - 任务详情
  - `WS /api/v1/ws/tasks/{task_id}/progress` - 实时进度
  - `GET /api/v1/presets` - 配置预设
- ✅ WebSocket 实时进度推送
- ✅ 模型转换核心服务
  - PyTorch → TFLite 转换
  - TFLite → network_rel.bin
  - 配置 JSON 生成
  - 最终 .bin 打包
- ✅ **校准数据集上传功能** ⭐ 新增
  - ZIP 文件上传和验证（最大 1GB）
  - 自动解压和目录结构识别
  - 动态生成 Ultralytics data.yaml
  - 支持多种目录结构
- ✅ Celery + Redis 任务队列
- ✅ 结构化日志系统（structlog）

#### 前端开发（Preact + TypeScript）
- ✅ Preact + TypeScript 项目搭建
- ✅ Vite 7 构建配置
- ✅ Tailwind CSS 4 + Radix UI
- ✅ Zustand 状态管理
- ✅ 拖拽上传文件界面
- ✅ **校准数据集上传组件** ⭐ 新增
  - 复选框控制启用/禁用
  - 拖拽上传 ZIP 文件
  - 文件大小和名称显示
  - 移除文件按钮
- ✅ 配置预设选择
- ✅ 实时进度监控页面
- ✅ 任务详情和下载功能
- ✅ WebSocket 客户端（自动重连）

#### 基础设施
- ✅ Docker 容器化配置
- ✅ Docker Compose 服务编排
  - Redis 服务
  - Celery Worker
  - FastAPI Backend
  - Preact Frontend
- ✅ Nginx 反向代理配置
- ✅ 快速启动脚本（start.sh）
- ✅ **目录结构调整** ⭐ 新增
  - 移除嵌套的 model-converter/model-converter/
  - 统一为 model-converter/ 单层结构

#### 文档
- ✅ README.md - 项目说明和快速开始
- ✅ IMPLEMENTATION.md - 详细实施总结
- ✅ PROJECT_STRUCTURE.md - 项目结构和开发指南
- ✅ CALIBRATION_UPDATE.md - 校准数据集功能说明
- ✅ WORK_PLAN.md - 本工作计划

---

## 🔄 当前问题清单

### P0 - 严重问题（立即修复）

1. **后端导入错误**
   - 文件: `backend/app/api/models.py`
   - 问题: 缺少 `from fastapi import Form`
   - 修复: 在文件顶部添加导入

2. **前端导入错误**
   - 文件: `frontend/src/hooks/index.ts`
   - 问题: `useState` 导入位置错误
   - 修复: 调整导入顺序

3. **缺少测试文件**
   - 问题: 没有 tests/ 目录和测试文件
   - 修复: 创建测试框架

### P1 - 重要问题（尽快修复）

1. **路径引用问题**
   - 文档中可能有旧的嵌套路径引用
   - 需要检查并更新所有文档

2. **环境变量配置**
   - backend/.env.example 需要更新
   - 添加校准数据集相关配置

### P2 - 优化建议（可延后）

1. 前端 UI 优化
2. 错误提示优化
3. 性能优化

---

## 📋 接下来的工作安排

### 阶段 1: 修复和验证（1 天）⭐ 立即开始

#### 1.1 修复已知问题（2 小时）

**任务 1.1.1: 修复后端导入**
```bash
# 文件: backend/app/api/models.py
# 在第 10 行后添加
from fastapi import Form
```

**任务 1.1.2: 修复前端导入**
```bash
# 文件: frontend/src/hooks/index.ts
# 将 useState 的导入移到 import 语句块顶部
import { useState, useEffect, useRef } from 'preact/hooks';
```

**任务 1.1.3: 创建测试目录**
```bash
# 创建测试目录结构
mkdir -p backend/tests
touch backend/tests/__init__.py
touch backend/tests/test_api.py
touch backend/tests/test_conversion.py
touch backend/tests/conftest.py
```

**任务 1.1.4: 验证目录结构**
```bash
# 确认项目结构正确
cd /Users/harryhua/Documents/GitHub/ne301/model-converter
tree -L 2 -I 'node_modules|__pycache__|*.pyc'
```

#### 1.2 本地测试（3 小时）

**任务 1.2.1: 后端启动测试**
```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，设置 NE301_PROJECT_PATH=/path/to/ne301

# 启动服务
uvicorn main:app --reload --port 8000
```

**任务 1.2.2: 前端启动测试**
```bash
cd frontend

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

**任务 1.2.3: 完整流程测试**
```bash
# 1. 访问 Web 界面
open http://localhost:3000

# 2. 测试文件上传
# - 上传小模型文件（可用于测试）
# - 上传校准数据集 ZIP（10-20 张图片）

# 3. 测试配置选择
# - 选择不同的预设

# 4. 提交转换任务
# - 观察进度更新
# - 检查 WebSocket 连接

# 5. 查看后端日志
# - 检查转换流程
# - 验证校准数据集处理

# 6. 测试下载功能
# - 下载转换后的文件
```

#### 1.3 文档更新（1 小时）

**任务 1.3.1: 更新路径引用**
- 检查所有文档中的路径引用
- 移除嵌套的 model-converter/model-converter/
- 更新为单层 model-converter/

**任务 1.3.2: 更新 README**
- 添加校准数据集说明
- 添加快速开始指南
- 添加常见问题解答

### 阶段 2: 测试和优化（1-2 天）

#### 2.1 单元测试

**后端测试**（4 小时）
```bash
cd backend

# 创建测试文件
touch tests/test_api.py
touch tests/test_conversion.py
touch tests/test_services.py

# 编写测试用例
# - test_upload_model()
# - test_extract_calibration_dataset()
# - test_convert_to_tflite()
# - test_websocket_progress()

# 运行测试
pytest --cov=app --cov-report=html
```

**前端测试**（3 小时）
```bash
cd frontend

# 创建测试文件
mkdir tests
touch tests.testHomePage.tsx
touch tests.testTaskDetail.tsx

# 运行测试
pnpm test --coverage
```

#### 2.2 集成测试（3 小时）

```bash
# 测试完整转换流程
1. 准备测试模型（yolov8n.pt）
2. 准备测试数据集（coco8.zip）
3. 上传并转换
4. 验证输出文件
5. 在 NE301 设备上测试
```

#### 2.3 性能测试（2 小时）

```bash
# 测试不同场景
- 大文件上传（500MB）
- 并发任务（3-5 个）
- 长时间运行（30 分钟）
- 内存使用监控
```

### 阶段 3: 部署准备（1 天）

#### 3.1 Docker 优化

**任务 3.1.1: 增加 Nginx 文件大小限制**
```nginx
# frontend/nginx.conf
client_max_body_size 1024M;
client_body_timeout 300s;
```

**任务 3.1.2: 优化 Docker 资源**
```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G
    environment:
      - MAX_CALIBRATION_SIZE=1073741824
```

#### 3.2 环境配置

**任务 3.2.1: 更新 .env.example**
```bash
# backend/.env.example
# 添加校准数据集配置
MAX_CALIBRATION_SIZE=1073741824
ALLOW_CALIBRATION_EXTENSIONS=[".zip"]
```

**任务 3.2.2: 创建生产环境配置**
```bash
# docker-compose.prod.yml
# 优化日志级别
# 启用 HTTPS
# 配置监控
```

### 阶段 4: 文档完善（1 天）

#### 4.1 用户文档

- [ ] 数据集准备指南
  - 如何收集代表性图像
  - 目录结构示例
  - ZIP 压缩方法
  - 数据集质量建议

- [ ] 更新 README.md
  - 校准数据集详细说明
  - 使用示例和截图
  - 常见问题解答
  - 故障排查指南

#### 4.2 开发文档

- [ ] API 文档补充
  - 校准数据集 API 说明
  - 错误码完整列表
  - WebSocket 协议说明

- [ ] 架构图更新
  - 添加校准数据集流程
  - 更新数据流图

---

## 🎯 Phase 2 计划（未来 1-2 周）

### 核心功能扩展

#### 2.1 批量转换（优先级：高）
- [ ] 多文件同时上传
- [ ] 批量任务管理界面
- [ ] 任务队列优化
- [ ] 批量下载功能
- [ ] 进度统计面板

#### 2.2 数据集管理（优先级：中）
- [ ] 保存常用数据集
- [ ] 数据集预览功能
- [ ] 使用统计分析
- [ ] 数据集评分系统

#### 2.3 用户系统（优先级：低）
- [ ] 用户注册/登录
- [ ] 权限管理
- [ ] 使用记录
- [ ] 配置保存

---

## 📊 时间估算总览

| 阶段 | 任务 | 预计时间 | 优先级 |
|-----|------|---------|--------|
| **阶段 1** | 修复和验证 | 6 小时 | P0 |
| - | 修复已知问题 | 2 小时 | P0 |
| - | 本地测试 | 3 小时 | P0 |
| - | 文档更新 | 1 小时 | P0 |
| **阶段 2** | 测试和优化 | 12 小时 | P1 |
| - | 单元测试 | 7 小时 | P0 |
| - | 集成测试 | 3 小时 | P0 |
| - | 性能测试 | 2 小时 | P1 |
| **阶段 3** | 部署准备 | 8 小时 | P1 |
| - | Docker 优化 | 4 小时 | P1 |
| - | 环境配置 | 4 小时 | P1 |
| **阶段 4** | 文档完善 | 8 小时 | P1 |
| - | 用户文档 | 4 小时 | P1 |
| - | 开发文档 | 4 小时 | P1 |
| **总计** | - | **34 小时** | - |

---

## 🚀 快速开始检查清单

### 立即执行（今天）

- [ ] 1. 修复后端导入错误
  ```bash
  vim backend/app/api/models.py
  # 添加: from fastapi import Form
  ```

- [ ] 2. 修复前端导入错误
  ```bash
  vim frontend/src/hooks/index.ts
  # 调整 useState 导入
  ```

- [ ] 3. 创建测试目录
  ```bash
  mkdir -p backend/tests frontend/tests
  ```

- [ ] 4. 启动服务测试
  ```bash
  cd /Users/harryhua/Documents/GitHub/ne301/model-converter
  ./start.sh
  ```

- [ ] 5. 访问 Web 界面
  ```bash
  open http://localhost:3000
  ```

### 本周完成

- [ ] 手动测试完整流程
- [ ] 编写核心功能测试
- [ ] 更新文档
- [ ] 准备演示环境

### 下周计划

- [ ] 完成 Phase 2 批量转换功能
- [ ] 性能优化
- [ ] 生产环境部署

---

## 📝 备注

### 项目路径
**根目录**: `/Users/harryhua/Documents/GitHub/ne301/model-converter/`

### 关键文件
- 后端入口: `backend/main.py`
- 前端入口: `frontend/src/main.tsx`
- 启动脚本: `start.sh`
- Docker 编排: `docker-compose.yml`

### 环境要求
- Python 3.11+
- Node.js 20+
- pnpm 9+
- Docker 20.10+

### 联系方式
- 问题反馈: GitHub Issues
- 技术讨论: 项目 Wiki

---

**文档版本**: v2.0.0
**创建日期**: 2026-03-09
**最后更新**: 2026-03-09 19:54
**状态**: 🟡 进行中 - 阶段 1 修复和验证
