# NE301 Model Converter - User Guide

Complete guide for using the NE301 Model Converter.

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Model Conversion](#model-conversion)
4. [Configuration Options](#configuration-options)
5. [Advanced Features](#advanced-features)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

---

## Overview

NE301 Model Converter is a zero-code, end-to-end model conversion platform that automatically converts PyTorch models to NE301 edge device format (.bin).

### Key Features

- **Zero-Code Operation**: Web-based interface, no coding required
- **End-to-End Automation**: PyTorch → Quantization → NE301 .bin
- **Real-Time Feedback**: WebSocket-based progress updates
- **Cross-Platform Support**: macOS / Linux / Windows
- **Smart OOM Fix**: Automatic diagnosis and fix for NE301 OOM issues

### Supported Models

| Model Type | Formats | Input Sizes |
|------------|---------|-------------|
| YOLOv5 | .pt, .pth | 256, 480, 640 |
| YOLOv8 | .pt, .pth | 256, 480, 640 |
| Custom PyTorch | .pt, .pth | Custom |

---

## Getting Started

### System Requirements

- **Docker Desktop**: Must be installed and running
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 10GB for Docker images
- **Browser**: Chrome, Firefox, Safari, Edge (latest versions)

### Starting the Service

```bash
# 1. Pull dependency image
docker pull camthink/ne301-dev:latest

# 2. Start service
docker-compose up -d

# 3. Access web interface
# Open http://localhost:8000
```

### Stopping the Service

```bash
docker-compose down
```

---

## Model Conversion

### Step-by-Step Guide

#### 1. Upload Model File

Click **"Select Model File"** and choose your PyTorch model:
- Supported formats: `.pt`, `.pth`
- Maximum file size: 500MB

#### 2. (Optional) Upload Class Definitions

Upload a YAML file defining class names:

```yaml
names:
  - person
  - bicycle
  - car
  - motorcycle
  # Add more classes as needed
```

This file is used for:
- Setting the correct number of classes
- Displaying class names in detection results

#### 3. (Optional) Upload Calibration Dataset

Upload a ZIP file containing calibration images:
- **Minimum**: 32 images
- **Recommended**: 50-100 images
- **Formats**: .jpg, .png
- **Purpose**: Improves quantization accuracy

#### 4. Select Conversion Preset

| Preset | Input Size | Speed | Accuracy | Use Case |
|--------|------------|-------|----------|----------|
| Fast | 256x256 | Fastest | Good | Real-time applications |
| Balanced | 480x480 | Fast | Better | General purpose (recommended) |
| High Precision | 640x640 | Slower | Best | High-accuracy requirements |

#### 5. Start Conversion

Click **"Start Conversion"** and monitor progress:
- Real-time progress bar
- Detailed conversion logs
- WebSocket-based updates

#### 6. Download Result

When complete:
- Click **"Download .bin File"**
- The file is ready for NE301 deployment

---

## Configuration Options

### Environment Variables

Create `backend/.env` to customize settings:

```env
# Docker Configuration
NE301_DOCKER_IMAGE=camthink/ne301-dev:latest
NE301_PROJECT_PATH=/app/ne301

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=False

# Logging
LOG_LEVEL=INFO

# File Storage
UPLOAD_DIR=./uploads
TEMP_DIR=./temp
OUTPUT_DIR=./outputs
MAX_UPLOAD_SIZE=524288000  # 500MB
```

### Conversion Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `input_size` | Model input resolution | 480 |
| `num_classes` | Number of detection classes | Auto-detected |
| `quantization` | Quantization type | int8 |

---

## Advanced Features

### Calibration Dataset

**Purpose**: Improve quantization accuracy by providing representative samples.

**Requirements**:
- ZIP file containing images
- Minimum 32 images (recommended: 50-100)
- Images should represent real-world use cases
- Supported formats: .jpg, .png

**Creating a Calibration Dataset**:

```bash
# Create directory with sample images
mkdir calibration_images

# Add 32-100 representative images
cp /path/to/your/images/*.jpg calibration_images/

# Create ZIP file
zip -r calibration.zip calibration_images/
```

**Best Practices**:
- Use images similar to production data
- Include various lighting conditions
- Cover different object sizes and angles
- Avoid duplicate or very similar images

### Custom Class Definitions

**YAML Format**:

```yaml
# classes.yaml
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
  - traffic light
```

**Auto-Detection**:
- If not provided, the system attempts to auto-detect from the model
- For YOLO models, COCO classes (80) are used by default

### Batch Conversion

For multiple models, use the REST API:

```bash
# Convert multiple models sequentially
for model in model1.pt model2.pt model3.pt; do
  curl -X POST "http://localhost:8000/api/convert" \
    -F "model_file=@$model" \
    -F 'config={"model_type": "yolov8", "input_size": 480}'
done
```

---

## Troubleshooting

### Common Issues

#### Docker Not Running

**Symptoms**:
- Error: "Cannot connect to Docker daemon"
- Service won't start

**Solution**:
1. Start Docker Desktop
2. Wait for Docker to fully initialize
3. Verify: `docker ps`

#### Image Pull Failed

**Symptoms**:
- Error: "failed to resolve reference"
- Timeout during image pull

**Solution**:
```bash
# Check network connection
ping google.com

# Manually pull image
docker pull camthink/ne301-dev:latest

# If still failing, configure Docker mirror
```

#### Port Already In Use

**Symptoms**:
- Error: "port is already allocated"
- Service fails to start

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Stop conflicting service
kill -9 <PID>

# Or stop existing container
docker-compose down
docker-compose up -d
```

#### Conversion Failed

**Symptoms**:
- Progress stops at a certain step
- Error message in logs

**Solutions**:

1. **Check model format**:
   - Must be valid PyTorch model (.pt/.pth)
   - YOLOv5/v8 models recommended

2. **Check calibration dataset**:
   - Must be ZIP file
   - Must contain .jpg/.png images
   - Minimum 32 images

3. **Check logs**:
   ```bash
   docker-compose logs -f
   ```

4. **Check memory**:
   - Ensure 4GB+ RAM available
   - Close other memory-intensive applications

#### OOM (Out of Memory) on NE301 Device

**Symptoms**:
- Model loads on device with error
- "[DRIVER] model_init: OOM"

**Solution** (v2.1+):
- This issue is **automatically fixed** during conversion
- The system detects and corrects mpool configuration
- No user action required

---

## FAQ

### General Questions

**Q: What models are supported?**

A: Currently supported:
- YOLOv5 (all variants)
- YOLOv8 (all variants)
- Custom PyTorch models (experimental)

**Q: How long does conversion take?**

A: Typical conversion times:
- Small models (YOLOv8n): 2-3 minutes
- Medium models (YOLOv8s/m): 3-5 minutes
- Large models (YOLOv8l/x): 5-10 minutes

**Q: Is calibration dataset required?**

A: No, it's optional. Without it, the system uses fake quantization, which may reduce accuracy slightly.

**Q: What's the difference between presets?**

A:
- **Fast**: Smallest model, fastest inference, slightly lower accuracy
- **Balanced**: Good balance of speed and accuracy (recommended)
- **High Precision**: Largest model, best accuracy, slower inference

### Technical Questions

**Q: Which Python version is supported?**

A: Python 3.11 or 3.12. Python 3.14 is not supported due to TensorFlow compatibility.

**Q: Can I convert models offline?**

A: After the initial setup (pulling Docker images), conversion works offline.

**Q: Where are converted files stored?**

A: Files are stored in Docker volumes:
- `uploads/`: Uploaded models
- `outputs/`: Converted .bin files
- `temp/`: Temporary files

**Q: How do I access converted files?**

A:
1. Download via web interface (recommended)
2. Or copy from container:
   ```bash
   docker cp model-converter-api:/app/outputs/ ./
   ```

### Deployment Questions

**Q: Can I deploy this on a server?**

A: Yes. The Docker-based deployment works on any server with Docker installed.

**Q: How do I update to a new version?**

A:
```bash
git pull
docker-compose build --no-cache
docker-compose up -d
```

**Q: Is authentication supported?**

A: Not in the current version. For production deployment, add authentication via reverse proxy (e.g., Nginx).

---

## Related Documentation

- [Quick Start Guide](QUICK_START.md) - 5-minute setup
- [Docker Deployment Guide](../README.docker.md) - Detailed Docker instructions
- [Docker Compose Guide](DOCKER_COMPOSE_GUIDE.md) - Configuration options
- [Development Guide](../CLAUDE.md) - Technical documentation

---

## Getting Help

- **Documentation**: Check this guide and related docs
- **Logs**: `docker-compose logs -f` for detailed logs
- **Issues**: Report bugs on GitHub Issues
- **Community**: Join discussions on GitHub

---

**Last Updated**: 2026-03-18
**Document Version**: 1.0.0
