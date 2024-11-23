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
    && rm -rf /var/lib/apt/lists/*

# 设置构建环境
WORKDIR /build
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir wheel setuptools && \
    pip install --no-cache-dir -r requirements.txt

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
