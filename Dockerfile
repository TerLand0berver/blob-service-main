# 构建依赖阶段
FROM python:3.9-slim-bullseye as builder

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
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

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    libjpeg62-turbo \
    libpng16-16 \
    libtiff5 \
    libwebp6 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 创建必要的目录并设置权限
WORKDIR /app
RUN mkdir -p /data /app/logs && \
    chown -R appuser:appuser /data /app/logs

# 从构建阶段复制Python包
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# 复制应用代码
COPY . .
RUN chown -R appuser:appuser /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    CONFIG_DIR=/data \
    CONFIG_FILE=/data/config.json \
    PATH="/home/appuser/.local/bin:$PATH" \
    AUDIT_LOG_PATH=/app/logs/audit.log \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# 切换到非root用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
