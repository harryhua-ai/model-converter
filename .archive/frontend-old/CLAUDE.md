# CLAUDE.md - model-converter Frontend

NE301 模型转换工具前端项目 - 基于 Preact + TypeScript 的 Web 界面

## 项目概述

这是一个单页应用（SPA），为 NE301 模型转换工具提供用户界面。用户可以通过这个界面上传 PyTorch 模型文件，配置转换参数，实时监控转换进度，并下载转换后的固件文件。

### 核心功能

- 模型文件上传（支持拖拽）
- 配置预设选择（yolov8n-256/480/640）
- 实时进度监控（WebSocket）
- 转换结果下载
- 任务历史管理

---

## 技术栈

### 前端框架
- **Preact 10** - 轻量级 React 替代方案
- **TypeScript** - 类型安全
- **Vite 7** - 快速的开发服务器和构建工具

### 状态管理
- **Zustand** - 轻量级状态管理
- **@preact/signals** - 细粒度响应式状态

### UI 组件
- **Radix UI** - 无样式、可访问的组件库
- **Tailwind CSS 4** - 实用优先的 CSS 框架
- **lucide-preact** - 图标库

### HTTP 客户端
- **axios** - HTTP 请求
- **WebSocket API** - 实时进度推送

### 开发工具
- **ESLint** - 代码检查
- **TypeScript** - 类型检查
- **pnpm** - 包管理器（推荐）

---

## 项目结构

```
frontend/
├── src/
│   ├── components/          # 可复用组件
│   │   ├── ui/              # 通用 UI 组件
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Progress.tsx
│   │   │   └── Toast.tsx
│   │   ├── layout/         # 布局组件
│   │   │   ├── Header.tsx
│   │   │   └── Footer.tsx
│   │   └── ModelUploader.tsx  # 模型上传组件
│   ├── pages/              # 页面组件
│   │   ├── Home.tsx        # 首页
│   │   └── Converter.tsx   # 转换页面
│   ├── services/           # API 服务
│   │   ├── api.ts          # API 客户端配置
│   │   ├── conversion.ts   # 转换相关 API
│   │   └── websocket.ts    # WebSocket 连接
│   ├── store/              # 状态管理
│   │   ├── conversionStore.ts  # 转换任务状态
│   │   └── uiStore.ts          # UI 状态
│   ├── hooks/              # 自定义 Hooks
│   │   ├── useWebSocket.ts
│   │   └── useConversion.ts
│   ├── types/              # TypeScript 类型定义
│   │   └── api.ts
│   ├── utils/              # 工具函数
│   │   └── helpers.ts
│   ├── styles/             # 样式文件
│   │   └── index.css
│   ├── App.tsx             # 根组件
│   └── main.tsx            # 入口文件
├── public/                 # 静态资源
├── index.html              # HTML 模板
├── vite.config.ts          # Vite 配置
├── tailwind.config.js      # Tailwind 配置
├── tsconfig.json           # TypeScript 配置
├── package.json            # 项目依赖
└── CLAUDE.md               # 本文档
```

---

## 快速开始

### 环境要求

- Node.js 20+
- pnpm 9+ (推荐) 或 npm

### 安装依赖

```bash
pnpm install
# 或
npm install
```

### 开发模式

```bash
pnpm dev
# 或
npm run dev
```

访问 http://localhost:3000

### 生产构建

```bash
pnpm build
# 或
npm run build
```

构建产物输出到 `dist/` 目录。

### 预览构建结果

```bash
pnpm preview
# 或
npm run preview
```

---

## 开发指南

### 组件开发规范

**函数组件**：所有组件使用函数组件和 Hooks

```tsx
import { h } from 'preact';
import { useState } from 'preact/hooks';

interface ButtonProps {
  variant?: 'primary' | 'secondary';
  onClick?: () => void;
  children: preact.ComponentChildren;
}

export function Button({ variant = 'primary', onClick, children }: ButtonProps) {
  return (
    <button
      className={`btn btn-${variant}`}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
```

**类型定义**：使用 TypeScript 接口定义 Props

```tsx
interface TaskCardProps {
  task: ConversionTask;
  onCancel?: (taskId: string) => void;
  onDownload?: (taskId: string) => void;
}
```

**样式**：使用 Tailwind CSS 和 clsx

```tsx
import { clsx } from 'clsx';

<div className={clsx(
  'p-4 rounded-lg',
  isActive && 'bg-blue-500',
  isDisabled && 'opacity-50'
)} />
```

### 状态管理

使用 Zustand 创建 store：

```tsx
// store/conversionStore.ts
import { create } from 'zustand';

interface ConversionStore {
  tasks: ConversionTask[];
  activeTaskId: string | null;
  addTask: (task: ConversionTask) => void;
  updateTask: (taskId: string, updates: Partial<ConversionTask>) => void;
}

export const useConversionStore = create<ConversionStore>((set) => ({
  tasks: [],
  activeTaskId: null,
  addTask: (task) => set((state) => ({
    tasks: [...state.tasks, task]
  })),
  updateTask: (taskId, updates) => set((state) => ({
    tasks: state.tasks.map((t) =>
      t.task_id === taskId ? { ...t, ...updates } : t
    )
  })),
}));
```

### API 调用

使用 axios 实例：

```tsx
import api from '../services/api';

// 上传模型
const uploadModel = async (file: File, config: ConversionConfig) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('config', JSON.stringify(config));

  const response = await api.post<ModelUploadResponse>('/models/upload', formData);
  return response.data;
};
```

### WebSocket 连接

```tsx
import { useWebSocket } from '../hooks/useWebSocket';

const Converter = () => {
  const { connect, disconnect, lastMessage } = useWebSocket();

  const startConversion = async (taskId: string) => {
    connect(`ws://localhost:8000/ws/tasks/${taskId}/progress`);
  };

  useEffect(() => {
    if (lastMessage?.status === 'completed') {
      disconnect();
    }
  }, [lastMessage]);

  return <div>Progress: {lastMessage?.progress}%</div>;
};
```

---

## 架构说明

### 数据流

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│          Preact Components             │
│  ┌──────────┐    ┌──────────────────┐  │
│  │  Pages   │───▶│   UI Components  │  │
│  └──────────┘    └──────────────────┘  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│         Zustand Stores                  │
│  • conversionStore                     │
│  • uiStore                             │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│         Services Layer                  │
│  • API Client (axios)                   │
│  • WebSocket Client                    │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│         Backend API                     │
│  • http://localhost:8000/api/v1        │
│  • ws://localhost:8000/ws               │
└──────────────────────────────────────────┘
```

### 组件层级

```
App
├── Router
│   ├── Home
│   │   ├── Header
│   │   ├── ModelUploader
│   │   ├── PresetSelector
│   │   └── Button
│   └── Converter
│       ├── TaskList
│       ├── TaskCard
│       │   ├── ProgressBar
│       │   └── StatusBadge
│       └── DownloadButton
└── ToastProvider
```

---

## 与后端 API 交互

### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/models/upload` | POST | 上传模型并创建转换任务 |
| `/api/v1/tasks` | GET | 获取任务列表 |
| `/api/v1/tasks/{id}` | GET | 获取任务详情 |
| `/api/v1/tasks/{id}/cancel` | POST | 取消任务 |
| `/api/v1/models/download/{id}` | GET | 下载转换结果 |
| `/ws/tasks/{id}/progress` | WebSocket | 实时进度推送 |

### 配置预设

```typescript
const PRESETS = {
  'yolov8n-256': {
    name: 'YOLOv8n 256x256',
    input_width: 256,
    input_height: 256,
    description: '快速检测'
  },
  'yolov8n-480': {
    name: 'YOLOv8n 480x480',
    input_width: 480,
    input_height: 480,
    description: '推荐'
  },
  'yolov8n-640': {
    name: 'YOLOv8n 640x640',
    input_width: 640,
    input_height: 640,
    description: '高精度'
  }
};
```

---

## 常见任务

### 添加新页面

1. 在 `src/pages/` 创建新组件
2. 添加路由到 `App.tsx`:

```tsx
import { Route } from 'preact-compact-router';
import NewPage from './pages/NewPage';

<Route path="/new" component={NewPage} />
```

### 添加新 API 方法

在 `src/services/api.ts` 添加：

```typescript
export const getSomething = async (id: string) => {
  const response = await api.get(`/something/${id}`);
  return response.data;
};
```

### 更新状态

```tsx
import { useConversionStore } from '../store/conversionStore';

const MyComponent = () => {
  const { updateTask } = useConversionStore();

  const handleUpdate = () => {
    updateTask(taskId, { progress: 50 });
  };
};
```

---

## 开发注意事项

### 热更新

Vite 提供快速的热模块替换（HMR），修改组件后自动刷新。

### 代理配置

开发环境下，API 请求自动代理到后端：

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': 'http://localhost:8000',
    '/ws': {
      target: 'ws://localhost:8000',
      ws: true
    }
  }
}
```

### 类型检查

```bash
pnpm run type-check
# 或
npx tsc --noEmit
```

### 代码检查

```bash
pnpm run lint
# 或
npx eslint src/
```

---

## 构建和部署

### 本地构建

```bash
pnpm build
```

构建产物在 `dist/` 目录，包含：
- `index.html`
- `assets/` - CSS、JS、图片等静态资源

### Docker 构建

前端通过 Dockerfile 构建为 Nginx 镜像：

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install
COPY . .
RUN pnpm build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### 环境变量

前端在构建时可通过 `.env` 文件配置：

```bash
# .env.production
VITE_API_URL=https://api.example.com
VITE_WS_URL=wss://api.example.com
```

---

## 故障排查

### 开发服务器启动失败

```bash
# 检查端口占用
lsof -i :3000

# 更换端口
vite --port 3001
```

### API 请求失败

1. 确认后端服务运行中：`curl http://localhost:8000/health`
2. 检查代理配置：`vite.config.ts`
3. 查看浏览器网络面板的错误信息

### WebSocket 连接失败

1. 确认后端支持 WebSocket
2. 检查防火墙设置
3. 验证 WS URL 格式：`ws://localhost:8000/ws/...`

---

## 相关资源

- [Preact 文档](https://preactjs.com/)
- [Vite 文档](https://vitejs.dev/)
- [Zustand 文档](https://zustand-demo.pmnd.rs/)
- [Tailwind CSS 文档](https://tailwindcss.com/)
- [Radix UI 文档](https://www.radix-ui.com/)

---

**最后更新**: 2026-03-11
