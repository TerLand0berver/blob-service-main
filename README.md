# Blob Service

一个安全、高性能的文件存储和处理服务。

## 功能特点

- 🔐 完整的认证和授权系统
  - JWT 令牌认证
  - 令牌刷新机制
  - IP 和域名白名单
  - 细粒度访问控制

- 📁 多样化文件处理
  - 文本文件处理
  - 图片处理（支持 JPEG, PNG, GIF, WebP, TIFF, BMP）
  - PDF 文档处理
  - Office 文档处理
  - 音频文件处理

- 🚀 高性能设计
  - 异步文件处理
  - WebSocket 实时进度
  - 分块上传支持
  - 缓存优化

- 🛡️ 企业级安全
  - 内容安全策略 (CSP)
  - 请求速率限制
  - 文件类型验证
  - 安全头部配置

## 快速开始

### 使用 Docker

```bash
# 拉取镜像
docker pull teraccc/chatnio-blob-service:latest

# 运行容器
docker run -d \
  -p 8000:8000 \
  -v /path/to/data:/data \
  -e ADMIN_USER=admin \
  -e ADMIN_PASSWORD=your-secure-password \
  -e JWT_SECRET_KEY=your-secret-key \
  teraccc/chatnio-blob-service:latest

# 或者使用 docker-compose
docker compose up -d
```

注意事项：
1. 确保挂载卷时使用 `/data` 作为容器内的目标路径
2. 建议使用 docker-compose 进行部署，可以更方便地管理配置
3. 首次运行时会自动创建必要的目录结构

### 手动安装

1. 克隆仓库
```bash
git clone https://github.com/yourusername/blob-service.git
cd blob-service
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\\Scripts\\activate   # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件设置必要的配置项
```

5. 运行服务
```bash
python main.py
```

## 配置说明

### 基础配置
```env
# 基本设置
APP_NAME=blob-service
APP_ENV=production
DEBUG=false
HOST=0.0.0.0
PORT=8000

# 管理员账户
ADMIN_USER=admin
ADMIN_PASSWORD=your-secure-password

# JWT配置
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 存储配置
STORAGE_TYPE=local  # 存储类型：local 或 s3
STORAGE_PATH=/data  # 存储根目录
LOCAL_STORAGE_PATH=/data/files  # 文件存储目录
LOCAL_STORAGE_DOMAIN=https://your-domain.com  # 访问域名
LOCAL_STORAGE_SERVE=true  # 是否提供静态文件服务
LOCAL_STORAGE_URL_PREFIX=/files  # URL前缀
MAX_CONTENT_LENGTH=100MB

# 安全配置
ENABLE_RATE_LIMIT=true
RATE_LIMIT_PER_MINUTE=60
ENABLE_CORS=true
ALLOWED_ORIGINS=http://localhost:3000,https://your-domain.com
```

### 白名单配置
```env
# IP白名单
WHITELIST_IPS=192.168.1.1,10.0.0.1

# 域名白名单
WHITELIST_DOMAINS=trusted-domain1.com,trusted-domain2.com

# 白名单访问控制
WHITELIST_RATE_LIMIT=1000
WHITELIST_MAX_FILE_SIZE=100MB
WHITELIST_ALLOWED_TYPES=pdf,jpg,png,docx
```

### S3 存储配置
```env
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_BUCKET_NAME=your-bucket
S3_REGION=your-region
S3_ENDPOINT=https://s3.your-region.amazonaws.com
```

## 存储配置

### 本地存储
```env
# 存储类型设置为本地
STORAGE_TYPE=local

# 本地存储路径
STORAGE_PATH=/data

# 文件命名策略
FILENAME_STRATEGY=uuid  # uuid, timestamp, original
PRESERVE_ORIGINAL_FILENAME=true  # 是否保留原始文件名

# 目录结构
DIRECTORY_STRUCTURE=date  # date, type, hash
SUB_DIRECTORY_FORMAT=%Y/%m/%d  # 日期格式的子目录结构

# 重复文件处理
DUPLICATE_STRATEGY=rename  # rename, replace, error
```

### S3 兼容存储
```env
# 存储类型设置为 S3
STORAGE_TYPE=s3

# 访问凭证
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key

# 存储桶配置
S3_BUCKET_NAME=your-bucket
S3_REGION=your-region
S3_ENDPOINT=https://s3.your-region.amazonaws.com

# 可选配置
S3_PATH_STYLE=false  # 是否使用路径样式访问
S3_SSL_VERIFY=true   # 是否验证SSL证书
S3_STORAGE_CLASS=STANDARD  # 存储类型：STANDARD, STANDARD_IA, ONEZONE_IA, GLACIER

# 预签名URL配置
S3_PRESIGNED_EXPIRY=3600  # 预签名URL过期时间（秒）
S3_PUBLIC_URL_PREFIX=https://cdn.your-domain.com  # CDN域名前缀
```

### Azure Blob 存储
```env
# 存储类型设置为 Azure
STORAGE_TYPE=azure

# 连接信息
AZURE_STORAGE_CONNECTION_STRING=your-connection-string
AZURE_CONTAINER_NAME=your-container

# 可选配置
AZURE_STORAGE_TIER=Hot  # Hot, Cool, Archive
AZURE_CDN_ENDPOINT=https://your-cdn.azureedge.net
```

### MinIO 存储
```env
# 存储类型设置为 MinIO
STORAGE_TYPE=minio

# 服务器配置
MINIO_ENDPOINT=play.min.io
MINIO_PORT=9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_BUCKET=your-bucket
MINIO_SECURE=true  # 是否使用HTTPS
```

### Google Cloud Storage
```env
# 存储类型设置为 GCS
STORAGE_TYPE=gcs

# 认证配置
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCS_BUCKET_NAME=your-bucket

# 可选配置
GCS_PROJECT_ID=your-project-id
GCS_LOCATION=us-central1
GCS_STORAGE_CLASS=STANDARD  # STANDARD, NEARLINE, COLDLINE, ARCHIVE
```

## API 文档

### 认证 API

#### 1. 登录获取令牌
```http
POST /auth/login
Content-Type: application/json

{
    "username": "admin",
    "password": "your-secure-password"
}
```

响应：
```json
{
    "status": true,
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 1800
}
```

#### 2. 刷新令牌
```http
POST /auth/refresh
Authorization: Bearer your-refresh-token
```

### 文件处理 API

#### 1. 上传文件（需要认证）
```http
POST /upload
Authorization: Bearer your-access-token
Content-Type: multipart/form-data

Form Data:
- file: [文件]
- save_all: true
```

#### 2. 批量上传（需要认证）
```http
POST /upload/batch
Authorization: Bearer your-access-token
Content-Type: multipart/form-data

Form Data:
- files: [file1, file2, file3]
- save_all: true
```

### 白名单 API（无需认证）

#### 1. 白名单上传
```http
POST /whitelist/upload
Content-Type: multipart/form-data
X-Client-IP: your-whitelisted-ip
X-Origin-Domain: your-whitelisted-domain.com

Form Data:
- file: [文件]
- save_all: true
```

#### 2. 白名单下载
```http
GET /whitelist/download/{file_id}
X-Client-IP: your-whitelisted-ip
X-Origin-Domain: your-whitelisted-domain.com
```

## API 响应参数说明

### 通用响应格式
```json
{
    "status": true,          // 请求状态：true/false
    "error": "",            // 错误信息，成功时为空
    "error_code": "",       // 错误代码
    "details": {},          // 详细信息
    "timestamp": "",        // 响应时间戳
    "request_id": ""        // 请求唯一标识
}
```

### 文件上传响应
```json
{
    "status": true,
    "type": "file",         // 文件类型：text, image, pdf, audio, video, office
    "content": {
        "url": "",          // 文件访问URL
        "filename": "",     // 文件名
        "size": 0,          // 文件大小（字节）
        "mime_type": "",    // MIME类型
        "hash": "",         // 文件哈希值
        "metadata": {       // 文件元数据
            "width": 0,     // 图片宽度
            "height": 0,    // 图片高度
            "duration": 0,  // 音视频时长
            "pages": 0,     // PDF页数
            "created": "",  // 创建时间
            "modified": "", // 修改时间
            "author": ""    // 作者信息
        },
        "processing": {     // 处理信息
            "ocr_text": "", // OCR识别文本
            "labels": [],   // 图像标签
            "transcript": "" // 音频转写文本
        }
    }
}
```

### 批量上传响应
```json
{
    "status": true,
    "results": [
        {
            "filename": "",
            "url": "",
            "status": "success",
            "error": ""
        }
    ],
    "summary": {
        "total": 0,
        "success": 0,
        "failed": 0
    }
}
```

## 开发指南

### 项目结构
```
blob-service/
├── app/
│   ├── api/            # API路由和处理器
│   ├── core/           # 核心功能模块
│   ├── models/         # 数据模型
│   ├── services/       # 业务逻辑服务
│   ├── utils/          # 工具函数
│   └── config.py       # 配置管理
├── tests/              # 测试用例
├── .env.example        # 环境变量示例
├── .gitignore         # Git忽略文件
├── Dockerfile         # Docker构建文件
├── docker-compose.yml # Docker编排文件
├── main.py           # 应用入口
├── requirements.txt   # Python依赖
└── README.md         # 项目文档
```

### 代码示例

#### Python
```python
import requests

def upload_file(file_path, token):
    url = "http://your-domain.com/upload"
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(file_path, "rb") as f:
        files = {"file": f}
        data = {"save_all": "true"}
        response = requests.post(url, headers=headers, files=files, data=data)
    
    return response.json()

# 使用示例
token = "your-access-token"
result = upload_file("document.pdf", token)
print(result)
```

#### JavaScript
```javascript
async function uploadFile(file, token) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('save_all', 'true');

    const response = await fetch('http://your-domain.com/upload', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    });
    return await response.json();
}

// 使用示例
const token = 'your-access-token';
const fileInput = document.querySelector('input[type="file"]');
const result = await uploadFile(fileInput.files[0], token);
console.log(result);
```

## 错误处理

### 1. 认证错误
```json
{
    "status": false,
    "error": "Invalid credentials",
    "error_code": "AUTH_001",
    "details": {
        "message": "用户名或密码错误",
        "attempts_remaining": 4
    }
}
```

### 2. 文件处理错误
```json
{
    "status": false,
    "error": "File processing failed",
    "error_code": "PROC_001",
    "details": {
        "message": "不支持的文件类型",
        "supported_types": ["pdf", "docx", "xlsx", "jpg", "png"]
    }
}
```

### 3. 白名单错误
```json
{
    "status": false,
    "error": "Access denied",
    "error_code": "WHITELIST_001",
    "details": {
        "message": "IP不在白名单中",
        "client_ip": "192.168.1.100"
    }
}
```

## 部署

### Docker 部署
```bash
# 构建镜像
docker build -t blob-service .

# 使用 docker-compose 部署
docker-compose up -d
```

### Kubernetes 部署
```bash
# 应用配置
kubectl apply -f k8s/config.yaml

# 部署服务
kubectl apply -f k8s/deployment.yaml
```

## 安全建议

1. **密码安全**
   - 使用强密码
   - 定期更换密码
   - 启用密码策略

2. **令牌管理**
   - 合理设置令牌过期时间
   - 定期刷新令牌
   - 妥善保管令牌

3. **访问控制**
   - 严格限制白名单
   - 启用速率限制
   - 监控异常访问

4. **文件安全**
   - 验证文件类型
   - 限制文件大小
   - 扫描恶意内容

## 常见问题

1. **Q: 如何更改文件存储位置？**  
   A: 修改 `.env` 文件中的 `STORAGE_PATH` 配置项。

2. **Q: 如何配置 S3 存储？**  
   A: 在 `.env` 文件中设置 S3 相关配置项，并将 `STORAGE_TYPE` 设置为 `s3`。

3. **Q: 如何增加白名单 IP？**  
   A: 在 `.env` 文件中的 `WHITELIST_IPS` 添加新的 IP 地址，多个 IP 用逗号分隔。

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 基本文件处理功能
- JWT 认证系统
- 白名单机制

### v1.1.0 (2024-01-15)
- 添加批量上传功能
- 优化文件处理性能
- 增强安全性配置
- 改进错误处理

## 许可证

MIT License

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

## 联系方式

- 作者：telagod
- 邮箱：vnw@live.com
- GitHub：https://github.com/TerLand0berver

## 文件存储 API

### 1. 上传文件
```http
POST /file/upload
Authorization: Bearer your-access-token
Content-Type: multipart/form-data

Form Data:
- file: [文件]
- path: storage/images  # 可选，存储路径
- filename: custom.jpg  # 可选，自定义文件名
- overwrite: false     # 可选，是否覆盖同名文件
- metadata: {"key": "value"}  # 可选，自定义元数据
```

响应：
```json
{
    "status": true,
    "data": {
        "file_id": "550e8400-e29b-41d4-a716-446655440000",
        "path": "storage/images/custom.jpg",
        "url": "https://your-domain.com/files/550e8400-e29b-41d4-a716-446655440000",
        "size": 1024,
        "mime_type": "image/jpeg",
        "metadata": {
            "key": "value",
            "created_at": "2024-01-01T12:00:00Z"
        }
    }
}
```

### 2. 获取文件信息
```http
GET /file/info/{file_id}
Authorization: Bearer your-access-token
```

响应：
```json
{
    "status": true,
    "data": {
        "file_id": "550e8400-e29b-41d4-a716-446655440000",
        "filename": "custom.jpg",
        "path": "storage/images/custom.jpg",
        "size": 1024,
        "mime_type": "image/jpeg",
        "created_at": "2024-01-01T12:00:00Z",
        "modified_at": "2024-01-01T12:00:00Z",
        "checksum": "d41d8cd98f00b204e9800998ecf8427e",
        "metadata": {
            "key": "value"
        },
        "storage": {
            "type": "s3",
            "bucket": "your-bucket",
            "region": "your-region"
        }
    }
}
```

### 3. 下载文件
```http
GET /file/download/{file_id}
Authorization: Bearer your-access-token
Query Parameters:
- disposition: attachment  # inline或attachment，默认inline
- filename: custom.jpg    # 可选，下载时的文件名
```

### 4. 删除文件
```http
DELETE /file/{file_id}
Authorization: Bearer your-access-token
Query Parameters:
- permanent: false  # 是否永久删除，默认false（软删除）
```

响应：
```json
{
    "status": true,
    "data": {
        "file_id": "550e8400-e29b-41d4-a716-446655440000",
        "deleted_at": "2024-01-01T12:00:00Z"
    }
}
```

### 5. 更新文件元数据
```http
PATCH /file/{file_id}/metadata
Authorization: Bearer your-access-token
Content-Type: application/json

{
    "metadata": {
        "key": "new_value",
        "tags": ["image", "profile"]
    }
}
```

响应：
```json
{
    "status": true,
    "data": {
        "file_id": "550e8400-e29b-41d4-a716-446655440000",
        "metadata": {
            "key": "new_value",
            "tags": ["image", "profile"],
            "updated_at": "2024-01-01T12:00:00Z"
        }
    }
}
```

### 6. 移动/重命名文件
```http
POST /file/{file_id}/move
Authorization: Bearer your-access-token
Content-Type: application/json

{
    "new_path": "storage/archive/2024",
    "new_filename": "renamed.jpg",
    "overwrite": false
}
```

响应：
```json
{
    "status": true,
    "data": {
        "file_id": "550e8400-e29b-41d4-a716-446655440000",
        "old_path": "storage/images/custom.jpg",
        "new_path": "storage/archive/2024/renamed.jpg",
        "moved_at": "2024-01-01T12:00:00Z"
    }
}
```

### 7. 复制文件
```http
POST /file/{file_id}/copy
Authorization: Bearer your-access-token
Content-Type: application/json

{
    "destination_path": "storage/backup",
    "new_filename": "backup.jpg",
    "overwrite": false
}
```

响应：
```json
{
    "status": true,
    "data": {
        "original_file_id": "550e8400-e29b-41d4-a716-446655440000",
        "new_file_id": "661f9511-f3ab-52e5-b827-557766551111",
        "path": "storage/backup/backup.jpg",
        "copied_at": "2024-01-01T12:00:00Z"
    }
}
```

### 8. 列出文件
```http
GET /file/list
Authorization: Bearer your-access-token
Query Parameters:
- path: storage/images    # 可选，指定目录
- page: 1                # 分页页码
- per_page: 20          # 每页数量
- sort: -created_at     # 排序字段和方向
- type: image           # 可选，按类型筛选
- q: profile           # 可选，搜索关键词
```

响应：
```json
{
    "status": true,
    "data": {
        "files": [
            {
                "file_id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "custom.jpg",
                "path": "storage/images/custom.jpg",
                "size": 1024,
                "mime_type": "image/jpeg",
                "created_at": "2024-01-01T12:00:00Z"
            }
        ],
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total": 150,
            "total_pages": 8
        }
    }
}
```

### 9. 生成预签名URL
```http
POST /file/{file_id}/presign
Authorization: Bearer your-access-token
Content-Type: application/json

{
    "expires_in": 3600,  # URL有效期（秒）
    "operation": "read"  # read或write
}
```

响应：
```json
{
    "status": true,
    "data": {
        "url": "https://your-domain.com/presigned/...",
        "expires_at": "2024-01-01T13:00:00Z",
        "operation": "read"
    }
}
```

### 10. 批量操作
```http
POST /file/batch
Authorization: Bearer your-access-token
Content-Type: application/json

{
    "operation": "delete",  # delete, move, copy
    "file_ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "661f9511-f3ab-52e5-b827-557766551111"
    ],
    "params": {
        "permanent": true  # 操作相关的参数
    }
}
```

响应：
```json
{
    "status": true,
    "data": {
        "successful": [
            {
                "file_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "deleted"
            }
        ],
        "failed": [
            {
                "file_id": "661f9511-f3ab-52e5-b827-557766551111",
                "error": "File not found"
            }
        ],
        "summary": {
            "total": 2,
            "successful": 1,
            "failed": 1
        }
    }
}
```

## 在线配置参数

### 系统配置
```env
# 应用设置
APP_NAME=blob-service
APP_ENV=production
DEBUG=false
HOST=0.0.0.0
PORT=8000

# 性能设置
WORKERS=4                 # 工作进程数
THREAD_POOL_SIZE=20      # 线程池大小
MAX_REQUESTS=1000        # 最大请求数
TIMEOUT=300              # 请求超时时间（秒）
KEEP_ALIVE=5            # Keep-Alive 时间（秒）

# 缓存设置
ENABLE_CACHE=true
CACHE_TYPE=redis        # redis, memcached
CACHE_URL=redis://localhost:6379/0
CACHE_TTL=3600         # 缓存过期时间（秒）

# 日志设置
LOG_LEVEL=INFO
LOG_FORMAT=json        # json, text
LOG_FILE=/var/log/blob-service.log
ENABLE_ACCESS_LOG=true
ENABLE_ERROR_LOG=true

# 监控设置
ENABLE_METRICS=true
METRICS_PORT=9090
ENABLE_HEALTH_CHECK=true
HEALTH_CHECK_PATH=/health
```

### 处理配置
```env
# 文件处理
MAX_FILE_SIZE=100MB
ALLOWED_EXTENSIONS=.jpg,.png,.gif,.pdf,.docx
SCAN_VIRUS=true
PRESERVE_EXIF=false
GENERATE_THUMBNAIL=true
THUMBNAIL_SIZE=200x200

# 图片处理
IMAGE_QUALITY=85
IMAGE_FORMAT=webp
MAX_IMAGE_SIZE=5000x5000
STRIP_METADATA=true

# OCR 设置
ENABLE_OCR=true
OCR_LANGUAGE=eng,chi_sim
OCR_API_KEY=your-api-key
OCR_TIMEOUT=30

# 音视频处理
ENABLE_TRANSCODING=true
VIDEO_CODEC=h264
AUDIO_CODEC=aac
MAX_VIDEO_LENGTH=3600
GENERATE_PREVIEW=true
```

### 安全配置
```env
# CORS 设置
ENABLE_CORS=true
ALLOWED_ORIGINS=http://localhost:3000,https://your-domain.com
ALLOWED_METHODS=GET,POST,PUT,DELETE
ALLOWED_HEADERS=Content-Type,Authorization
MAX_AGE=3600

# 安全头部
ENABLE_SECURITY_HEADERS=true
STRICT_TRANSPORT_SECURITY=max-age=31536000
CONTENT_SECURITY_POLICY=default-src 'self'
X_FRAME_OPTIONS=DENY
X_CONTENT_TYPE_OPTIONS=nosniff

# 速率限制
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STRATEGY=fixed-window  # fixed-window, sliding-window
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10

# 会话管理
SESSION_TIMEOUT=3600
MAX_SESSIONS_PER_USER=5
ENFORCE_SINGLE_SESSION=false

```

### 存储配置
```env
# 存储类型选择
STORAGE_TYPE=local  # 可选值: local, s3, azure, minio, gcs, file_api

# 本地存储配置
LOCAL_STORAGE_PATH=/path/to/storage  # 本地存储路径
LOCAL_STORAGE_DOMAIN=https://your-domain.com  # 访问域名
LOCAL_STORAGE_SERVE=true  # 是否提供静态文件服务
LOCAL_STORAGE_URL_PREFIX=/files  # URL前缀

# S3 兼容存储配置
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_BUCKET=your-bucket
S3_REGION=your-region  # 例如: us-east-1
S3_ENDPOINT=https://s3.amazonaws.com  # 可选，自定义endpoint
S3_USE_SSL=true
S3_VERIFY_SSL=true
S3_URL_STYLE=path  # path 或 virtual
S3_PUBLIC_URL=https://your-bucket.s3.amazonaws.com  # 可选，自定义访问域名
S3_URL_EXPIRES=3600  # 预签名URL过期时间(秒)

# Azure Blob 存储配置
AZURE_ACCOUNT_NAME=your-account-name
AZURE_ACCOUNT_KEY=your-account-key
AZURE_CONTAINER=your-container
AZURE_CONNECTION_STRING=your-connection-string  # 可选，完整连接字符串
AZURE_ENDPOINT=https://your-account.blob.core.windows.net
AZURE_SAS_TOKEN=your-sas-token  # 可选，使用SAS令牌
AZURE_URL_EXPIRES=3600  # 预签名URL过期时间(秒)

# MinIO 存储配置
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_BUCKET=your-bucket
MINIO_ENDPOINT=http://localhost:9000
MINIO_REGION=us-east-1  # 可选
MINIO_SECURE=true  # 是否使用HTTPS
MINIO_URL_EXPIRES=3600  # 预签名URL过期时间(秒)

# Google Cloud Storage 配置
GCS_PROJECT_ID=your-project-id
GCS_BUCKET=your-bucket
GCS_CREDENTIALS_FILE=/path/to/credentials.json  # 服务账号密钥文件路径
GCS_CREDENTIALS_JSON={"type": "service_account", ...}  # 或直接提供服务账号JSON
GCS_PUBLIC_URL=https://storage.googleapis.com/your-bucket  # 可选，自定义访问域名
GCS_URL_EXPIRES=3600  # 预签名URL过期时间(秒)

# 文件API配置
FILE_API_ENDPOINT=https://api.example.com/files
FILE_API_KEY=your-api-key
FILE_API_SECRET=your-api-secret  # 可选
FILE_API_VERSION=v1  # 可选
FILE_API_TIMEOUT=30  # 请求超时时间(秒)

# 通用存储配置
STORAGE_PATH_STYLE=date  # 存储路径风格: date, hash, uuid
STORAGE_HASH_LENGTH=8  # 使用hash风格时的长度
STORAGE_DATE_FORMAT=%Y/%m/%d  # 使用date风格时的格式
STORAGE_DUPLICATE_POLICY=rename  # 重复文件处理策略: rename, overwrite, error
STORAGE_PRESERVE_FILENAME=true  # 是否保留原始文件名
STORAGE_URL_EXPIRES=3600  # 默认预签名URL过期时间(秒)
STORAGE_PUBLIC_ACCESS=false  # 是否允许公开访问
STORAGE_MAX_KEYS=1000  # 列表查询每页最大条数
STORAGE_CACHE_CONTROL=public, max-age=31536000  # 缓存控制
STORAGE_CONTENT_DISPOSITION=inline  # 内容处置方式
STORAGE_METADATA_KEYS=["creator", "project", "tags"]  # 允许的元数据键

# 高级配置
STORAGE_MULTIPART_THRESHOLD=100MB  # 分片上传阈值
STORAGE_MULTIPART_CHUNKSIZE=5MB  # 分片大小
STORAGE_MAX_CONCURRENCY=4  # 最大并发请求数
STORAGE_CONNECT_TIMEOUT=10  # 连接超时时间(秒)
STORAGE_READ_TIMEOUT=60  # 读取超时时间(秒)
STORAGE_RETRY_TIMES=3  # 失败重试次数
STORAGE_RETRY_DELAY=1  # 重试延迟时间(秒)
```

说明：

1. **存储类型**
   - `local`: 本地文件系统存储
   - `s3`: AWS S3 或兼容S3协议的存储
   - `azure`: Azure Blob Storage
   - `minio`: MinIO 对象存储
   - `gcs`: Google Cloud Storage
   - `file_api`: 自定义文件存储API

2. **路径风格**
   - `date`: 按日期格式生成路径，如 `2024/01/01/file.jpg`
   - `hash`: 使用文件哈希值生成路径，如 `ab/cd/abcdef1234.jpg`
   - `uuid`: 使用UUID生成路径，如 `550e8400/e29b/41d4/a716446655440000.jpg`

3. **重复文件策略**
   - `rename`: 自动重命名，如 `file(1).jpg`
   - `overwrite`: 覆盖已有文件
   - `error`: 返回错误

4. **安全说明**
   - 建议使用环境变量或配置文件管理敏感信息
   - 生产环境必须启用SSL/TLS
   - 建议使用临时凭证或SAS令牌
   - 定期轮换访问密钥
   - 遵循最小权限原则配置存储权限

5. **性能优化**
   - 合理配置分片上传参数
   - 根据实际需求调整并发数
   - 使用CDN加速文件访问
   - 配置适当的缓存策略
   - 监控存储性能指标
