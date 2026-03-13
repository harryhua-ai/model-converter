FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖和构建工具
RUN apt-get update && apt-get install -y \
    # 构建工具
    gcc g++ make libc6-dev cmake \
    protobuf-compiler \
    # Docker CLI
    docker-cli \
    curl \
    # ✅ 新增：OpenMP 支持（TensorFlow 多线程）
    libgomp1 \
    # ✅ 新增：OpenGL 和 X11（OpenCV 需要）
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgthread-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖（包含 ML 库）
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ ./app/
COPY tools/ ./tools/

# 复制初始化脚本
COPY scripts/init-ne301.sh /usr/local/bin/init-ne301.sh
RUN chmod +x /usr/local/bin/init-ne301.sh

# 创建工作目录
RUN mkdir -p /app/uploads /app/outputs /app/ne301

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令（集成初始化脚本）
CMD ["sh", "-c", "/usr/local/bin/init-ne301.sh && uvicorn app.main:app --host", "0.0.0.0", "--port", "8000"]
