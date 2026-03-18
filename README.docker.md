# NE301 Model Converter - Docker Deployment Guide

## Quick Start

### Prerequisites

- **Docker Desktop** installed and running
- **4GB+ RAM** available for Docker
- **10GB+ disk space** for Docker images

### One-Command Deployment

```bash
# 1. Pull NE301 dependency image
docker pull camthink/ne301-dev:latest

# 2. Build and start the service
docker-compose up -d

# 3. Access the web interface
# Open http://localhost:8000 in your browser
```

**Deployment complete!** You can now start converting models.

---

## Docker Compose Configuration Options

This project provides three Docker Compose configurations for different scenarios:

| File | Purpose | Startup Speed | Use Case |
|------|---------|---------------|----------|
| `docker-compose.yml` | **Production** | ~2 min | Production deployment, first-time setup |
| `docker-compose.dev.yml` | Development | ~2 min | Development environment setup |
| `docker-compose.dev.local.yml` | **Local Development** | ~5 sec | Daily development (recommended) |

### Production Deployment (Recommended)

```bash
# Build and start with production configuration
docker-compose up -d

# View logs
docker-compose logs -f

# Stop service
docker-compose down
```

### Local Development (Fastest)

```bash
# First-time build
docker-compose build

# Start with local development config (~5 sec)
docker-compose -f docker-compose.dev.local.yml up -d

# Code changes auto-reload (~2 sec)
# No need to rebuild for Python code changes

# View logs
docker-compose -f docker-compose.dev.local.yml logs -f
```

---

## When to Rebuild Docker Images

### No Rebuild Needed (Code Mount Mode)

When using `docker-compose.dev.local.yml`:
- Modified `backend/app/` Python files
- Modified `backend/tools/` scripts

**Solution**: Just restart the container
```bash
docker-compose -f docker-compose.dev.local.yml restart api
```

### Rebuild Required

You MUST rebuild the image when:

1. **Modified `requirements.txt`**
   ```bash
   docker-compose build --no-cache api
   ```

2. **Modified frontend code** (`frontend/`)
   ```bash
   docker-compose build --no-cache api
   ```

3. **Modified `Dockerfile`**
   ```bash
   docker-compose build --no-cache api
   ```

---

## Environment Variables

Create `backend/.env` file (optional):

```env
# Docker Configuration
NE301_DOCKER_IMAGE=camthink/ne301-dev:latest
NE301_PROJECT_PATH=/app/ne301

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=False

# Log Level
LOG_LEVEL=INFO

# File Paths
UPLOAD_DIR=./uploads
TEMP_DIR=./temp
OUTPUT_DIR=./outputs
MAX_UPLOAD_SIZE=524288000  # 500MB
```

---

## Common Commands

### Service Management

```bash
# View status
docker-compose ps

# View logs (real-time)
docker-compose logs -f

# Restart service
docker-compose restart

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes
docker-compose down -v
```

### Container Operations

```bash
# Enter container shell
docker-compose exec api /bin/bash

# Check container health
docker inspect --format='{{.State.Health.Status}}' model-converter-api

# View resource usage
docker stats model-converter-api
```

### Image Management

```bash
# Build image
docker-compose build

# Force rebuild (no cache)
docker-compose build --no-cache

# View images
docker images | grep model-converter
```

---

## Troubleshooting

### Docker Not Running

**Error**: `Cannot connect to the Docker daemon`

**Solution**:
1. Start Docker Desktop
2. Verify: `docker ps`

### Image Pull Failed

**Error**: `failed to resolve reference`

**Solution**:
```bash
# Check network connection
# Manually pull image
docker pull camthink/ne301-dev:latest
```

### Port Already in Use

**Error**: `port is already allocated`

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Stop old containers
docker-compose down

# Restart service
docker-compose up -d
```

### Memory Insufficient

**Error**: `OCI runtime create failed`

**Solution**:
```bash
# Use development config with memory limit
docker-compose -f docker-compose.dev.local.yml up -d

# Or increase Docker memory limit in Docker Desktop settings
```

### Code Changes Not Taking Effect

**Reason**: Using production config without code mount

**Solution**:
```bash
# Option 1: Restart container
docker-compose restart

# Option 2: Use development config (recommended)
docker-compose -f docker-compose.dev.local.yml up -d
```

---

## Architecture

### Single Container Deployment

```
┌─────────────────────────────────────────┐
│    Docker Container (API + Frontend)     │
│  ┌──────────┐         ┌──────────┐      │
│  │ Frontend │─────▶   │ Backend  │      │
│  │ (dist/)  │         │ (FastAPI)│      │
│  └──────────┘         └──────────┘      │
│                              │          │
│                              ▼          │
│                    Docker Adapter       │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│     Docker Container (NE301 Tools)       │
│  PyTorch → TFLite → NE301 .bin           │
└─────────────────────────────────────────┘
```

### Multi-Stage Build

- **Stage 1**: `node:20-slim` (Build frontend)
- **Stage 2**: `python:3.10-slim` (Run backend)
- **Image Size**: ~1.01 GB

---

## Performance Comparison

| Operation | Code Mount | Image Built-in |
|-----------|------------|----------------|
| Code change effect | ~2 sec (restart) | ~5-10 min (rebuild) |
| Image size | 1.01 GB | 1.01 GB |
| Use case | Development | Production |
| Dependency change | Rebuild required | Rebuild required |
| Frontend change | Rebuild required | Rebuild required |

---

## Best Practices

1. **Use development config for daily work**
   ```bash
   docker-compose -f docker-compose.dev.local.yml up -d
   ```

2. **Rebuild after dependency changes**
   ```bash
   docker-compose build
   ```

3. **Use production config for deployment**
   ```bash
   docker-compose up -d
   ```

4. **Clean up periodically**
   ```bash
   docker-compose down
   docker system prune -f
   ```

---

## Related Documentation

- [Docker Compose Guide](docs/DOCKER_COMPOSE_GUIDE.md) - Detailed comparison of three configurations
- [Quick Start Guide](docs/QUICK_START.md) - 5-minute setup guide
- [User Guide](docs/USER_GUIDE.md) - Complete feature documentation
- [Development Guide](CLAUDE.md) - Full development documentation

---

**Last Updated**: 2026-03-18
**Document Version**: 1.0.0
