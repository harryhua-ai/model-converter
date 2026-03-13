# 使用 NE301 开发镜像（包含 ST Edge AI、ARM GCC 等工具链）
FROM camthink/ne301-dev:latest

# 设置工作目录
WORKDIR /app

# 安装 Python 3.11 和必要的系统库
# ne301-dev 基础镜像是 Ubuntu 22.04，自带 python3.10
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-dev python3.11-distutils python3-pip \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# 升级 pip 并安装 Python 依赖
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir -r requirements.txt && \
    python3 -m pip install --no-cache-dir 'celery[redis]==5.4.0' 'redis==5.2.0' 'loguru>=0.7.0'

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p uploads temp outputs

# 容器启动时自动加载 ST Edge AI 环境
RUN echo "source /etc/profile.d/stedgeai.sh 2>/dev/null || true" >> ~/.bashrc

EXPOSE 8000

# 启动命令
CMD ["/bin/bash", "-c", "pip install --no-cache-dir 'celery[redis]==5.4.0' 'redis==5.2.0' 'loguru>=0.7.0' 2>/dev/null || true && source /etc/profile.d/stedgeai.sh 2>/dev/null || true && exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8000"]
