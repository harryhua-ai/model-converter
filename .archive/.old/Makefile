.PHONY: help start stop clean install backend frontend convert
.PHONY: docker-build docker-up docker-down docker-logs
.PHONY: build-parallel build-frontend build-backend build-status
.PHONY: build-logs-frontend build-logs-backend build-clean-logs retry-backend
.PHONY: cleanup-cleanup cleanup-cache cleanup-images cleanup-all

# 默认目标：显示帮助
help:
	@echo "NE301 模型转换工具 - Makefile 快捷命令"
	@echo ""
	@echo "本地运行:"
	@echo "  make start           启动 Web 服务（一键启动）"
	@echo "  make stop            停止服务"
	@echo "  make restart         重启服务"
	@echo "  make convert         命令行转换"
	@echo "  make install         安装依赖"
	@echo "  make clean           清理依赖和临时文件"
	@echo ""
	@echo "Docker 运行:"
	@echo "  make docker-build    构建 Docker 镜像（串行）"
	@echo "  make build-parallel  并行构建所有镜像（推荐）"
	@echo "  make build-frontend  仅构建前端镜像"
	@echo "  make build-backend   仅构建后端镜像（含 Celery）"
	@echo "  make build-status    查看构建状态"
	@echo "  make retry-backend   重新构建后端（失败重试）"
	@echo "  make verify          验证 Docker 镜像"
	@echo "  make docker-up       启动 Docker 服务"
	@echo "  make docker-down     停止 Docker 服务"
	@echo "  make docker-logs     查看 Docker 日志"
	@echo ""
	@echo "Docker 清理:"
	@echo "  make cleanup-disk    查看磁盘占用"
	@echo "  make cleanup-cache   清理构建缓存（推荐）"
	@echo "  make cleanup-images  清理悬空镜像"
	@echo "  make cleanup-all     深度清理所有未使用资源"
	@echo ""
	@echo "命令行转换示例:"
	@echo "  make convert MODEL=yolov8n.pt PRESET=yolov8n-480"
	@echo "  ./convert.sh yolov8n.pt --preset yolov8n-480"

# ── 本地运行命令 ─────────────────────────────────────────────

start: ## 启动 Web 服务（一键启动）
	@echo "🚀 启动 NE301 模型转换工具..."
	@./start.sh

stop: ## 停止服务
	@echo "🛑 停止服务..."
	@./stop.sh

restart: ## 重启服务
	@echo "🔄 重启服务..."
	@$(MAKE) stop
	@sleep 2
	@$(MAKE) start

backend: ## 仅启动后端
	@echo "🐍 启动后端服务..."
	@cd backend && source venv/bin/activate && python3 main.py

frontend: ## 仅启动前端
	@echo "🎨 启动前端服务..."
	@cd frontend && pnpm dev

convert: ## 命令行转换模型
	@if [ -z "$(MODEL)" ]; then \
		echo "❌ 错误: 请指定 MODEL 参数"; \
		echo "   示例: make convert MODEL=yolov8n.pt PRESET=yolov8n-480"; \
		exit 1; \
	fi
	@echo "🔄 转换模型: $(MODEL)"
	@./convert.sh $(MODEL) --preset $(PRESET)

# ── Docker 命令 ───────────────────────────────────────────────

docker-build: ## 构建 Docker 镜像
	@echo "🔨 构建 Docker 镜像..."
	@docker-compose build

docker-up: ## 启动 Docker 服务
	@echo "🚀 启动 Docker 服务..."
	@docker-compose up -d
	@echo "⏳ 等待服务启动..."
	@sleep 5
	@echo ""
	@echo "✅ 服务已启动:"
	@echo "   Web 界面:  http://localhost:3000"
	@echo "   API 文档:  http://localhost:8000/docs"
	@echo ""
	@echo "   查看日志: make docker-logs"
	@echo "   停止服务: make docker-down"

docker-down: ## 停止 Docker 服务
	@echo "🛑 停止 Docker 服务..."
	@docker-compose down

docker-logs: ## 查看 Docker 日志
	@docker-compose logs -f backend

docker-restart: ## 重启 Docker 服务
	@echo "🔄 重启 Docker 服务..."
	@$(MAKE) docker-down
	@sleep 2
	@$(MAKE) docker-up

# ─── 并行构建命令 ─────────────────────────────────────────────

build-parallel: ## 并行构建所有镜像（推荐）
	@echo "🚀 开始并行构建..."
	@./build-parallel.sh

build-frontend: ## 仅构建前端
	@echo "🎨 构建前端镜像..."
	@mkdir -p logs
	@docker-compose build frontend 2>&1 | tee logs/build-frontend.log
	@docker images | grep ne301-model-converter-frontend

build-backend: ## 仅构建后端（包括 Celery Worker）
	@echo "🐍 构建后端镜像..."
	@mkdir -p logs
	@docker-compose build backend 2>&1 | tee logs/build-backend.log
	@docker tag ne301-model-converter-backend:v2 ne301-model-converter-celery:v2
	@docker images | grep ne301-model-converter-backend

build-status: ## 查看构建状态
	@echo "=== Docker 镜像状态 ==="
	@docker images | grep -E "ne301-model-converter|REPOSITORY"
	@echo ""
	@echo "=== 构建日志 ==="
	@ls -lh logs/build-*.log 2>/dev/null || echo "暂无构建日志"

build-logs-frontend: ## 查看前端构建日志
	@less +G logs/build-frontend.log

build-logs-backend: ## 查看后端构建日志
	@less +G logs/build-backend.log

build-clean-logs: ## 清理构建日志
	@rm -f logs/build-*.log
	@echo "✅ 构建日志已清理"

retry-backend: ## 重新构建后端（用于修复失败后重试）
	@echo "🔄 重新构建后端..."
	@docker-compose build --no-cache backend 2>&1 | tee logs/build-backend-retry.log
	@docker tag ne301-model-converter-backend:v2 ne301-model-converter-celery:v2
	@echo "✅ 后端重新构建完成"

verify: ## 验证 Docker 镜像
	@./verify-build.sh

# ─── Docker 清理命令 ─────────────────────────────────────────────

cleanup-disk: ## 查看 Docker 磁盘占用
	@echo "=== Docker 磁盘占用 ==="
	@docker system df
	@echo ""
	@echo "=== 镜像列表 ==="
	@docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

cleanup-cache: ## 清理构建缓存（推荐，释放最多空间）
	@echo "🧹 清理构建缓存..."
	@docker builder prune -a -f
	@echo "✅ 构建缓存已清理"
	@echo ""
	@$(MAKE) cleanup-disk

cleanup-images: ## 清理悬空镜像
	@echo "🧹 清理悬空镜像..."
	@docker image prune -f
	@echo "✅ 悬空镜像已清理"
	@echo ""
	@$(MAKE) cleanup-disk

cleanup-all: ## 深度清理所有未使用资源（⚠️ 会删除未使用的镜像）
	@echo "⚠️  警告：这将删除所有未使用的镜像和容器！"
	@read -p "确认继续? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker system prune -a -f; \
		echo "✅ 系统清理完成"; \
	else \
		echo "已取消"; \
	fi
	@echo ""
	@$(MAKE) cleanup-disk

cleanup-interactive: ## 交互式清理（推荐）
	@./cleanup-docker.sh

# ─── 依赖管理 ────────────────────────────────────────────────

install: ## 安装所有依赖
	@echo "📦 安装后端依赖..."
	@python3 -m venv backend/venv
	@source backend/venv/bin/activate && pip install -r backend/requirements.txt
	@echo "📦 安装前端依赖..."
	@cd frontend && pnpm install
	@echo "✅ 依赖安装完成"

install-backend: ## 仅安装后端依赖
	@echo "📦 安装后端依赖..."
	@python3 -m venv backend/venv
	@source backend/venv/bin/activate && pip install -r backend/requirements.txt

install-frontend: ## 仅安装前端依赖
	@echo "📦 安装前端依赖..."
	@cd frontend && pnpm install

# ─── 清理 ─────────────────────────────────────────────────────

clean: ## 清理依赖和临时文件
	@echo "🧹 清理依赖和临时文件..."
	@rm -rf backend/venv frontend/node_modules
	@rm -f .backend.pid .frontend.pid
	@rm -rf uploads/* temp/* outputs/*
	@echo "✅ 清理完成"

clean-cache: ## 清理临时文件
	@echo "🧹 清理临时文件..."
	@rm -rf uploads/* temp/*
	@rm -f .backend.pid .frontend.pid
	@echo "✅ 临时文件已清理"

clean-docker: ## 清理 Docker 资源
	@echo "🧹 清理 Docker 资源..."
	@docker-compose down -v
	@docker system prune -f
	@echo "✅ Docker 资源已清理"

# ─── 帮助 ─────────────────────────────────────────────────────
.DEFAULT_GOAL := help
