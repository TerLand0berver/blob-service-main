# 构建参数
ARG PYTHON_VERSION=3.9

# 构建依赖阶段
FROM python:${PYTHON_VERSION}-slim-bullseye AS builder

# 安装构建依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    cmake \
    libmagic-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff5-dev \
    libwebp-dev \
    python3-dev \
    libffi-dev \
    zlib1g-dev \
    libmupdf-dev \
    libgl1-mesa-dev \
    antiword \
    pkg-config \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# 设置构建环境
WORKDIR /build
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir wheel setuptools build && \
    pip install --no-cache-dir -r requirements.txt

# 运行阶段
FROM python:${PYTHON_VERSION}-slim-bullseye

# 安装运行时依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libmagic1 \
    libjpeg62-turbo \
    libpng16-16 \
    libtiff5 \
    libwebp6 \
    libmupdf-dev \
    antiword \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制Python包
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# 创建非root用户和必要目录
RUN useradd -m -s /bin/bash appuser && \
    mkdir -p /data /data/files /data/temp /app/logs

# 设置入口点脚本
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh && \
    chown -R appuser:appuser /app /data /app/logs /usr/local/bin/docker-entrypoint.sh

# 创建应用目录并复制应用代码
WORKDIR /app
COPY --chown=appuser:appuser . .

# 设置环境变量
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 8000

# 设置入口点和默认命令
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
