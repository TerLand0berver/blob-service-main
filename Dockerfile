# 构建依赖阶段
FROM python:3.9-slim-bullseye AS builder

# 添加 backports 源以获取最新的 libavif
RUN echo "deb http://deb.debian.org/debian bullseye-backports main" >> /etc/apt/sources.list

# 安装构建依赖
RUN apt-get update && \
    apt-get install -y -t bullseye-backports libavif-dev && \
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
FROM python:3.9-slim-bullseye

# 添加 backports 源并安装运行时依赖
RUN echo "deb http://deb.debian.org/debian bullseye-backports main" >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y -t bullseye-backports libavif13 && \
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
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 创建必要的目录并设置权限
WORKDIR /app
RUN mkdir -p /data /app/logs && \
    chown -R appuser:appuser /data /app/logs

# 复制Python依赖
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# 复制应用代码
COPY --chown=appuser:appuser . .

# 设置环境变量
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PATH="/app/bin:${PATH}"

# 切换到非root用户
USER appuser

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 复制并设置入口点脚本
COPY --chown=appuser:appuser docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["docker-entrypoint.sh"]

# 启动应用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
