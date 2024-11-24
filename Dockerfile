# 构建参数
ARG PYTHON_VERSION=3.9

# 构建依赖阶段
FROM python:${PYTHON_VERSION}-slim-bullseye AS builder

# 安装构建依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
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
    ffmpeg \
    antiword \
    && rm -rf /var/lib/apt/lists/*

# 设置构建环境
WORKDIR /build
COPY requirements.txt .

# 安装基础工具
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir wheel setuptools

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 最终运行时镜像
FROM python:${PYTHON_VERSION}-slim-bullseye

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser -s /sbin/nologin appuser

# 安装运行时依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libmagic1 \
    libjpeg62-turbo \
    libpng16-16 \
    libtiff5 \
    libwebp6 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libmupdf-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 设置工作目录
WORKDIR /app

# 复制Python依赖
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# 复制应用代码
COPY --chown=appuser:appuser . .

# 设置环境变量
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/bin:/home/appuser/.local/bin:${PATH}"

# 创建必要的目录并设置权限
RUN mkdir -p /data /data/files /data/temp /app/logs && \
    chown -R appuser:appuser /data /app/logs && \
    chmod 755 /data /data/files /data/temp /app/logs

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 8000

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 复制并设置入口点脚本
COPY --chown=appuser:appuser docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["docker-entrypoint.sh"]

# 启动应用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
