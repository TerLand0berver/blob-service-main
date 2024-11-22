#!/bin/bash
set -e

# 确保数据目录存在且有正确的权限
if [ ! -d "/data" ]; then
    mkdir -p /data
    chown -R appuser:appuser /data
fi

# 如果配置文件不存在，创建默认配置
if [ ! -f "/data/config.json" ]; then
    echo "{}" > /data/config.json
    chown appuser:appuser /data/config.json
fi

# 执行传入的命令
exec "$@"
