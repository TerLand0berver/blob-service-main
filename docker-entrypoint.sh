#!/bin/bash
set -e

# 函数：错误处理
error_handler() {
    echo "Error occurred in script at line: $1, error code: $2"
    exit "$2"
}

# 函数：检查系统依赖
check_system_dependencies() {
    if ! command -v curl > /dev/null 2>&1; then
        echo "Warning: Recommended system tool 'curl' is not installed"
    fi
}

# 函数：检查Python依赖
check_python_dependencies() {
    for package in PIL pydub magic fitz docx pandas PyPDF2 numpy odf; do
        if ! python3 -c "import importlib; importlib.import_module('${package}')" > /dev/null 2>&1; then
            echo "Warning: Python package '$package' is not installed"
        fi
    done
}

# 设置错误处理
trap 'error_handler "$LINENO" "$?"' ERR

# 检查目录权限前确保用户存在
if ! id -u appuser > /dev/null 2>&1; then
    echo "Warning: appuser not found, using current user"
else
    # 检查目录权限
    echo "Checking directory permissions..."
    for dir in /data /data/files /data/temp /app/logs; do
        if [ ! -d "$dir" ]; then
            echo "Creating directory $dir"
            mkdir -p "$dir" || true
        fi
        chown -R appuser:appuser "$dir" 2>/dev/null || true
        chmod 755 "$dir" 2>/dev/null || true
    done
fi

# 初始化配置文件
if [ ! -f "/data/config.json" ]; then
    echo "Initializing default configuration..."
    cat > "/data/config.json" <<EOF
{
    "storage": {
        "type": "${STORAGE_TYPE:-local}",
        "local_path": "/data/files",
        "temp_path": "/data/temp",
        "s3": {
            "access_key": "${S3_ACCESS_KEY:-}",
            "secret_key": "${S3_SECRET_KEY:-}",
            "endpoint": "${S3_ENDPOINT:-}",
            "bucket": "${S3_BUCKET:-}",
            "region": "${S3_REGION:-}"
        }
    },
    "security": {
        "require_auth": ${REQUIRE_AUTH:-false},
        "max_file_size": ${MAX_FILE_SIZE:-10485760}
    },
    "features": {
        "enable_ocr": ${ENABLE_OCR:-false},
        "enable_vision": ${ENABLE_VISION:-false},
        "image_quality": {
            "jpeg_quality": ${JPEG_QUALITY:-85},
            "png_compression": ${PNG_COMPRESSION:-6}
        },
        "video_quality": {
            "max_resolution": "${VIDEO_MAX_RESOLUTION:-720p}",
            "frame_rate": ${VIDEO_FRAME_RATE:-30}
        }
    }
}
EOF
    chown appuser:appuser "/data/config.json"
    chmod 644 "/data/config.json"
fi

# 检查依赖
echo "Checking dependencies..."
check_system_dependencies
check_python_dependencies

# 设置Python环境变量
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# 启动应用
echo "Starting application..."
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
