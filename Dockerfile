FROM python:3.9-slim-buster as builder

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 设置构建环境
WORKDIR /build
COPY requirements.txt .

# 分步安装依赖以便于调试
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir wheel setuptools

# 逐个安装依赖以定位问题
RUN pip install --no-cache-dir fastapi==0.68.2 && \
    pip install --no-cache-dir pydantic==1.9.0 && \
    pip install --no-cache-dir uvicorn==0.15.0 && \
    pip install --no-cache-dir python-multipart==0.0.5 && \
    pip install --no-cache-dir aiohttp==3.8.0 && \
    pip install --no-cache-dir aiofiles==0.7.0 && \
    pip install --no-cache-dir python-jose[cryptography]==3.3.0 && \
    pip install --no-cache-dir passlib[bcrypt]==1.7.4 && \
    pip install --no-cache-dir python-dotenv==0.19.0 && \
    pip install --no-cache-dir pymupdf==1.19.0 && \
    pip install --no-cache-dir pandas==1.3.0 && \
    pip install --no-cache-dir openpyxl==3.0.9 && \
    pip install --no-cache-dir xlrd==2.0.1 && \
    pip install --no-cache-dir python-docx==0.8.11 && \
    pip install --no-cache-dir python-magic==0.4.24 && \
    pip install --no-cache-dir chardet==4.0.0 && \
    pip install --no-cache-dir boto3==1.26.0 && \
    pip install --no-cache-dir botocore==1.29.0

# 最终镜像
FROM python:3.9-slim-buster

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    libmagic1 \
    curl \
    libxml2 \
    libxslt1.1 \
    libjpeg62-turbo \
    libpng16-16 \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 创建必要的目录
WORKDIR /app
RUN mkdir -p /data && chown -R appuser:appuser /data

# 从构建阶段复制Python包
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# 复制应用代码
COPY . .
RUN chown -R appuser:appuser /app

# 复制并设置启动脚本权限
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh && chown appuser:appuser /docker-entrypoint.sh

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV CONFIG_DIR=/data
ENV CONFIG_FILE=/data/config.json

# 切换到非root用户
USER appuser

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
