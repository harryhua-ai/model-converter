# NE301 Model Converter - Quick Start Guide

Get your first model converted in 5 minutes!

---

## Prerequisites

- **Docker Desktop** installed and running
- **4GB RAM** available
- **Internet connection** (for first-time image download)

---

## Quick Start (3 Steps)

### Step 1: Pull Dependencies

```bash
docker pull camthink/ne301-dev:latest
```

### Step 2: Start Service

```bash
docker-compose up -d
```

Wait ~2 minutes for the first build.

### Step 3: Access Web Interface

Open your browser and navigate to:

```
http://localhost:8000
```

**Done!** The service is now running.

---

## Your First Model Conversion

### 1. Prepare Your Files

You need:
- **PyTorch model file** (`.pt` or `.pth`)
- **Class definition YAML** (optional, for YOLO models)
- **Calibration dataset** (optional, improves quantization accuracy)

### 2. Upload and Convert

1. Click **"Select Model File"** and choose your `.pt` file
2. (Optional) Upload `classes.yaml` for class names
3. (Optional) Upload calibration dataset (ZIP with 32+ images)
4. Select a preset:
   - **Fast**: 256x256, fastest conversion
   - **Balanced**: 480x480, recommended
   - **High Precision**: 640x640, best accuracy
5. Click **"Start Conversion"**

### 3. Monitor Progress

Watch the real-time progress bar and logs:
- Step 1/4: PyTorch → TFLite (0-30%)
- Step 2/4: TFLite Quantization (30-60%)
- Step 3/4: NE301 Preparation (60-70%)
- Step 4/4: NE301 Packaging (70-100%)

### 4. Download Result

When complete, click **"Download .bin File"** to get your NE301 deployment package.

---

## Sample Files

Don't have a model? Use our test files:

```bash
# Download sample YOLOv8 model
wget https://github.com/ultralytics/assets/raw/main/yolov8n.pt

# Download sample class definitions
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

## Common Commands

```bash
# View logs
docker-compose logs -f

# Restart service
docker-compose restart

# Stop service
docker-compose down

# Check service status
docker-compose ps
```

---

## Troubleshooting

### Docker Not Running

**Error**: `Cannot connect to the Docker daemon`

**Fix**: Start Docker Desktop

### Port Already In Use

**Error**: `port is already allocated`

**Fix**:
```bash
# Find and stop the process
lsof -i :8000
docker-compose down
docker-compose up -d
```

### Image Pull Failed

**Fix**:
```bash
# Check network and manually pull
docker pull camthink/ne301-dev:latest
```

### Conversion Failed

**Fix**:
1. Check model format (must be `.pt` or `.pth`)
2. View detailed logs in the web interface
3. Ensure model is compatible with YOLOv8

---

## Next Steps

- Read the [User Guide](USER_GUIDE.md) for detailed features
- Check [Docker Deployment Guide](../README.docker.md) for advanced configuration
- See [Development Guide](../CLAUDE.md) for technical details

---

## Getting Help

- **Documentation**: [User Guide](USER_GUIDE.md)
- **Issues**: Report bugs on GitHub Issues
- **Logs**: Check `docker-compose logs -f` for details

---

**Last Updated**: 2026-03-18
