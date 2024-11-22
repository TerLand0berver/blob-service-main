FROM python:3.9-slim-buster

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 创建必要的目录
WORKDIR /app
RUN mkdir -p /data && chown -R appuser:appuser /data

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .
RUN chown -R appuser:appuser /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV CONFIG_DIR=/data
ENV CONFIG_FILE=/data/config.json

# 切换到非root用户
USER appuser

EXPOSE 8000

# 使用启动脚本
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
