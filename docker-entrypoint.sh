#!/bin/sh
set -e

# 函数：错误处理
handle_error() {
    echo "Error occurred in script at line: ${1}"
    exit 1
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
trap 'handle_error $?' ERR

# 检查目录权限
echo "Checking directory permissions..."
for dir in /data /data/files /data/temp /app/logs; do
    if [ ! -d "$dir" ]; then
        echo "Creating directory $dir"
        mkdir -p "$dir"
    fi
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
        "temp_path": "/data/temp",
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
        "max_file_size": ${MAX_FILE_SIZE:-10485760},
        "max_image_dimension": ${MAX_IMAGE_DIMENSION:-4096},
        "max_pdf_pages": ${MAX_PDF_PAGES:-1000}
    },
    "features": {
        "ocr_enabled": ${ENABLE_OCR:-false},
        "vision_enabled": ${ENABLE_VISION:-true},
        "azure_speech_enabled": ${ENABLE_AZURE_SPEECH:-false}
    },
    "processing": {
        "image_quality": ${IMAGE_QUALITY:-85},
        "force_webp": ${FORCE_WEBP:-true},
        "video_bitrate": "${VIDEO_BITRATE:-2M}",
        "audio_bitrate": "${AUDIO_BITRATE:-192k}"
    }
}
EOF
    chown appuser:appuser "/data/config.json"
    chmod 644 "/data/config.json"
fi

# 检查环境
echo "Checking environment..."
check_system_dependencies
check_python_dependencies

# 验证配置文件
echo "Validating configuration..."
if ! python3 -c "import json; json.load(open('/data/config.json'))" > /dev/null 2>&1; then
    echo "Error: Invalid configuration file"
    exit 1
fi

# 清理临时文件
echo "Cleaning temporary files..."
find /data/temp -type f -mtime +1 -delete 2>/dev/null || true

echo "Initialization completed successfully"

# 执行主命令
echo "Starting application with command: $@"
exec "$@"
