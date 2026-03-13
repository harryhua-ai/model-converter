#!/bin/bash
# rollback-mixed-arch.sh - 回滚到混合架构

echo "⚠️  回滚到混合架构..."
echo ""

# 1. 备份当前配置
BACKUP_FILE="docker-compose-rosetta.yml.backup.$(date +%Y%m%d_%H%M%S)"
echo "📦 备份当前配置到: $BACKUP_FILE"
cp docker-compose-rosetta.yml "$BACKUP_FILE"

# 2. 修改为混合架构
echo "📝 创建混合架构配置文件..."
cat > docker-compose-mixed.yml << 'EOF'
services:
  # Redis - 使用 ARM64 原生（移除 platform）
  redis:
    image: redis:7-alpine
    # 无 platform 约束，使用宿主机架构
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
    restart: unless-stopped

  # Frontend - 使用 ARM64 原生
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      # 无 platform 约束，使用宿主机架构
    image: ne301-model-converter-frontend:v2
    ports:
      - "3000:80"
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped

  # Backend - 保持 AMD64
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      platform: linux/amd64
      args:
        BUILDPLATFORM: linux/amd64
    image: ne301-model-converter-backend:rosetta
    command: sh -c "pip install --no-cache-dir 'celery[redis]==5.4.0' 'redis==5.2.0' 'loguru>=0.7.0' && source /etc/profile.d/stedgeai.sh 2>/dev/null || true && exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8000"
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./uploads:/app/uploads
      - ./temp:/app/temp
      - ./outputs:/app/outputs
      - ../Model:/workspace/Model:ro
      - ../Script:/workspace/Script:ro
    environment:
      - NE301_PROJECT_PATH=/workspace
      - PYTHONUNBUFFERED=1
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - ATEN_CPU_CAPABILITY=avx2
    cpus: '4.0'
    mem_limit: 8g
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # Celery - 保持 AMD64
  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
      platform: linux/amd64
      args:
        BUILDPLATFORM: linux/amd64
    image: ne301-model-converter-backend:rosetta
    command: sh -c "pip install --no-cache-dir 'celery[redis]==5.4.0' 'redis==5.2.0' 'loguru>=0.7.0' && python3 -m celery -A app.worker worker --loglevel=info --concurrency=1"
    volumes:
      - ./backend:/app
      - ./uploads:/app/uploads
      - ./temp:/app/temp
      - ./outputs:/app/outputs
      - ../Model:/workspace/Model:ro
      - ../Script:/workspace/Script:ro
    environment:
      - NE301_PROJECT_PATH=/workspace
      - PYTHONUNBUFFERED=1
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - ATEN_CPU_CAPABILITY=avx2
    cpus: '4.0'
    mem_limit: 8g
    depends_on:
      redis:
        condition: service_healthy
      backend:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "celery -A app.worker inspect active --timeout=5 || exit 1"]
      interval: 60s
      timeout: 10s
      retries: 3
      start_period: 120s
EOF

# 3. 切换到混合架构
echo "🔄 切换到混合架构..."
docker-compose -f docker-compose-rosetta.yml down
docker-compose -f docker-compose-mixed.yml up -d

# 4. 验证架构
echo ""
echo "🔍 验证架构（应该是 frontend=arm64, redis=arm64, backend=amd64）"
sleep 3
docker ps --format "table {{.Names}}\t{{.Architecture}}"

echo ""
echo "✅ 回滚完成"
echo ""
echo "恢复统一 AMD64 架构："
echo "  docker-compose -f docker-compose-mixed.yml down"
echo "  docker-compose -f docker-compose-rosetta.yml up -d"
