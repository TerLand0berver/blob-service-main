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
    required_packages=(
        "PIL:pillow"
        "fitz:PyMuPDF"
        "docx:python-docx"
        "openpyxl:openpyxl"
    )
    
    for package_pair in "${required_packages[@]}"; do
        import_name="${package_pair%%:*}"
        package_name="${package_pair#*:}"
        if ! python3 -c "import $import_name" > /dev/null 2>&1; then
            echo "Warning: Python package '$package_name' (import name: $import_name) is not installed"
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

# 检查依赖
echo "Checking dependencies..."
check_system_dependencies
check_python_dependencies

# 启动应用
echo "Starting application..."
exec "$@"
