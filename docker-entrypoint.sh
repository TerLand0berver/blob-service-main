#!/bin/bash
set -eo pipefail

# 函数：错误处理
handle_error() {
    echo "Error occurred in script at line: ${1}"
    exit 1
}

# 设置错误处理
trap 'handle_error ${LINENO}' ERR

# 创建必要的目录
echo "Creating and configuring directories..."
directories=("/data" "/data/files" "/app/logs")
for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "Creating directory: $dir"
        mkdir -p "$dir"
    fi
    echo "Setting permissions for: $dir"
    chown -R appuser:appuser "$dir"
    chmod 755 "$dir"
done

# 初始化配置文件
if [ ! -f "/data/config.json" ]; then
    echo "Initializing default configuration..."
    cat > "/data/config.json" <<EOF
{
    "storage": {
        "type": "${STORAGE_TYPE:-local}",
        "local_path": "/data/files",
        "s3": {
            "access_key": "${S3_ACCESS_KEY:-}",
            "secret_key": "${S3_SECRET_KEY:-}",
            "bucket_name": "${S3_BUCKET_NAME:-}",
            "endpoint_url": "${S3_ENDPOINT_URL:-}",
            "region_name": "${S3_REGION_NAME:-}"
        }
    },
    "auth": {
        "required": ${REQUIRE_AUTH:-true},
        "admin_user": "${ADMIN_USER:-admin}"
    },
    "limits": {
        "max_file_size": ${MAX_FILE_SIZE:-10485760}
    },
    "features": {
        "ocr_enabled": ${ENABLE_OCR:-false},
        "vision_enabled": ${ENABLE_VISION:-true},
        "azure_speech_enabled": ${ENABLE_AZURE_SPEECH:-false}
    }
}
EOF
    chown appuser:appuser "/data/config.json"
    chmod 644 "/data/config.json"
fi

# 检查Python环境
echo "Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed"
    exit 1
fi

# 验证配置文件
echo "Validating configuration..."
if ! python3 -c "import json; json.load(open('/data/config.json'))"; then
    echo "Error: Invalid configuration file"
    exit 1
fi

echo "Initialization completed successfully"

# 执行主命令
echo "Starting application..."
exec "$@"
