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

# 安装基础工具
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir wheel setuptools build

# 分组安装Python依赖以便于调试
RUN pip install --no-cache-dir fastapi==0.104.1 pydantic==2.4.2 pydantic-settings==2.0.3 uvicorn[standard]==0.24.0 python-multipart==0.0.6 && \
    pip install --no-cache-dir aiohttp==3.8.5 aiofiles==23.2.1 && \
    pip install --no-cache-dir python-jose[cryptography]==3.3.0 passlib[bcrypt]==1.7.4 python-dotenv==1.0.0 && \
    pip install --no-cache-dir PyJWT==2.8.0 redis==5.0.1 python-json-logger==2.0.7 && \
    pip install --no-cache-dir boto3==1.29.3 python-magic==0.4.27 && \
    pip install --no-cache-dir pymupdf==1.23.6 PyPDF2==3.0.1 python-docx==0.8.11 docx2txt==0.8 && \
    pip install --no-cache-dir chardet==5.2.0 openpyxl==3.1.2 pygments==2.17.2 && \
    pip install --no-cache-dir Pillow==10.1.0 && \
    pip install --no-cache-dir pyyaml==6.0.1 aioredis==2.0.1 async-timeout==4.0.3 httpx==0.26.0 && \
    pip install --no-cache-dir prometheus-client==0.19.0 psutil==5.9.6 azure-cognitiveservices-speech==1.31.0 && \
    if [ "$(uname -s)" = "Windows_NT" ]; then pip install --no-cache-dir python-magic-bin==0.4.14; fi

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
    antiword \
    curl \
    bash \
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
    mkdir -p /home/appuser/bin && \
    chown -R appuser:appuser /data /app/logs /home/appuser && \
    chmod 755 /data /data/files /data/temp /app/logs /home/appuser/bin

# 复制并设置入口点脚本
COPY --chown=appuser:appuser docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh && \
    ln -sf /usr/local/bin/docker-entrypoint.sh /home/appuser/bin/ && \
    chown -R appuser:appuser /home/appuser/bin && \
    # 确保使用bash作为默认shell
    ln -sf /bin/bash /bin/sh

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 8000

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# 启动应用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
