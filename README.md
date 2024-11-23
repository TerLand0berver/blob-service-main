<div align="center">
    
# Secure Blob Service

### 安全的文件存储和处理服务

[![Deploy to Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/TerLand0berver/blob-service-main)
[![Deploy on Zeabur](https://zeabur.com/button.svg)](https://zeabur.com/templates/RWGFOH)

</div>

## 功能特点

### 核心功能
- 开箱即用：支持 Vercel/Render 一键部署
- 多文件类型：支持文本、PDF、Word、Excel、图片、音频等
- 多存储选项：Base64、本地存储、S3、Cloudflare R2、MinIO等
- OCR支持：从图片中提取文本（需要 Paddle OCR API）
- 音频支持：音频转文本（需要 Azure Speech to Text 服务）

### 安全特性
- JWT 认证：安全的令牌管理和刷新机制
- 密码策略：强密码要求和密码复杂度验证
- 访问控制：IP和域名白名单
- 速率限制：防止暴力攻击和DoS
- 审计日志：详细的操作记录和安全事件跟踪
- 内容安全：CSP和安全响应头
- 会话管理：自动会话超时和并发限制

## 最近更新

### 安全增强
- 增加了完整的JWT认证系统
- 实现了强密码策略和账户锁定机制
- 添加了详细的审计日志功能
- 增强了访问控制和速率限制
- 实现了安全响应头和CSP策略

### 存储增强
- 改进了S3兼容存储的配置
- 优化了本地存储的安全性
- 增加了存储访问的审计功能

## 支持的文件类型
- 文本文件
- 图片（需要vision模型）
- 音频（需要Azure Speech服务）
- Word文档（.docx）
- PDF文件
- PowerPoint文档（.pptx）
- Excel表格（.xlsx/.xls）

## Docker部署

### 使用预构建镜像
```shell
docker run -p 8000:8000 teraccc/chatnio-blob-service

# 使用环境变量
docker run -p 8000:8000 \
  -e ADMIN_USER=admin \
  -e ADMIN_PASSWORD=your_secure_password \
  -e JWT_SECRET_KEY=your_jwt_secret \
  teraccc/chatnio-blob-service

# 使用本地存储
docker run -p 8000:8000 \
  -v /path/to/data:/data \
  -e STORAGE_TYPE=local \
  teraccc/chatnio-blob-service
```

### 使用Docker Compose
```yaml
version: '3.8'
services:
  blob-service:
    image: teraccc/chatnio-blob-service
    ports:
      - "8000:8000"
    environment:
      - ADMIN_USER=admin
      - ADMIN_PASSWORD=your_secure_password
      - JWT_SECRET_KEY=your_jwt_secret
      - STORAGE_TYPE=local
    volumes:
      - ./data:/data
```

## 源码部署
```shell
git clone https://github.com/TerLand0berver/blob-service-main
cd blob-service-main

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件设置必要的配置

# 启动服务
uvicorn main:app --host 0.0.0.0 --port 8000

# 开发模式（热重载）
uvicorn main:app --reload
```

## API接口

### 认证接口
`POST /auth/login` - 用户登录
```json
{
    "username": "admin",
    "password": "your_password"
}
```

`POST /auth/refresh` - 刷新访问令牌
```json
{
    "refresh_token": "your_refresh_token"
}
```

`POST /auth/logout` - 注销登录

### 文件接口
`POST /upload` - 上传文件
```json
{
    "file": "[file]",
    "enable_ocr": false,
    "enable_vision": true,
    "save_all": false
}
```

#### 参数说明
| 参数 | 类型 | 说明 |
|------|------|------|
| `file` | File | 要上传的文件 |
| `enable_ocr` | Boolean | 启用OCR（默认：false） |
| `enable_vision` | Boolean | 启用视觉处理（默认：true） |
| `save_all` | Boolean | 保存所有文件（默认：false） |

#### 响应格式
```json
{
    "status": true,
    "type": "pdf",
    "content": "...",
    "error": ""
}
```

## API 详细文档

### 认证 API

#### 1. 用户登录
```http
POST /auth/login
Content-Type: application/json

{
    "username": "admin",
    "password": "your_secure_password"
}
```

响应示例：
```json
{
    "status": true,
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 86400
}
```

#### 2. 刷新令牌
```http
POST /auth/refresh
Authorization: Bearer your_refresh_token
Content-Type: application/json

{
    "refresh_token": "your_refresh_token"
}
```

响应示例：
```json
{
    "status": true,
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 86400
}
```

#### 3. 注销登录
```http
POST /auth/logout
Authorization: Bearer your_access_token
```

响应示例：
```json
{
    "status": true,
    "message": "Successfully logged out"
}
```

### 文件处理 API

#### 1. 上传文本文件
```http
POST /upload
Authorization: Bearer your_access_token
Content-Type: multipart/form-data

Form Data:
- file: [text_file.txt]
- save_all: false
```

响应示例：
```json
{
    "status": true,
    "type": "text",
    "content": "文件内容...",
    "error": ""
}
```

#### 2. 上传并处理图片
```http
POST /upload
Authorization: Bearer your_access_token
Content-Type: multipart/form-data

Form Data:
- file: [image.jpg]
- enable_vision: true
- enable_ocr: false
- save_all: true
```

响应示例：
```json
{
    "status": true,
    "type": "image",
    "content": {
        "text": "图片中识别的文本",
        "url": "https://your-domain.com/static/images/xxx.jpg",
        "metadata": {
            "width": 800,
            "height": 600,
            "format": "JPEG"
        }
    },
    "error": ""
}
```

#### 3. 上传 PDF 文件
```http
POST /upload
Authorization: Bearer your_access_token
Content-Type: multipart/form-data

Form Data:
- file: [document.pdf]
- save_all: true
```

响应示例：
```json
{
    "status": true,
    "type": "pdf",
    "content": {
        "text": "PDF文档内容...",
        "pages": 5,
        "images": [
            {
                "url": "https://your-domain.com/static/images/page1.jpg",
                "page": 1
            }
        ],
        "metadata": {
            "title": "文档标题",
            "author": "作者",
            "creation_date": "2024-01-01"
        }
    },
    "error": ""
}
```

#### 4. 处理音频文件
```http
POST /upload
Authorization: Bearer your_access_token
Content-Type: multipart/form-data

Form Data:
- file: [audio.mp3]
- save_all: true
```

响应示例：
```json
{
    "status": true,
    "type": "audio",
    "content": {
        "text": "音频转写文本...",
        "url": "https://your-domain.com/static/audio/xxx.mp3",
        "duration": 120,
        "language": "zh-CN"
    },
    "error": ""
}
```

#### 5. 处理 Office 文档
```http
POST /upload
Authorization: Bearer your_access_token
Content-Type: multipart/form-data

Form Data:
- file: [document.docx]
- save_all: true
```

响应示例：
```json
{
    "status": true,
    "type": "docx",
    "content": {
        "text": "文档内容...",
        "images": [
            {
                "url": "https://your-domain.com/static/images/image1.jpg",
                "description": "图片描述"
            }
        ],
        "metadata": {
            "title": "文档标题",
            "author": "作者",
            "last_modified": "2024-01-01"
        }
    },
    "error": ""
}
```

### 错误处理

#### 1. 认证错误
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

#### 2. 文件处理错误
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

#### 3. 存储错误
```json
{
    "status": false,
    "error": "Storage error",
    "error_code": "STOR_001",
    "details": {
        "message": "存储服务不可用",
        "storage_type": "s3"
    }
}
```

### 使用示例

#### Python
```python
import requests

def upload_file(file_path, token):
    url = "http://your-domain.com/upload"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    with open(file_path, "rb") as f:
        files = {"file": f}
        data = {
            "enable_vision": "true",
            "save_all": "true"
        }
        response = requests.post(url, headers=headers, files=files, data=data)
    
    return response.json()

def login(username, password):
    url = "http://your-domain.com/auth/login"
    data = {
        "username": username,
        "password": password
    }
    response = requests.post(url, json=data)
    return response.json()

# 使用示例
token = login("admin", "password")["access_token"]
result = upload_file("image.jpg", token)
print(result)
```

#### JavaScript
```javascript
async function login(username, password) {
    const response = await fetch('http://your-domain.com/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username,
            password
        })
    });
    return await response.json();
}

async function uploadFile(file, token) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('enable_vision', 'true');
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
async function example() {
    try {
        const auth = await login('admin', 'password');
        const fileInput = document.querySelector('input[type="file"]');
        const result = await uploadFile(fileInput.files[0], auth.access_token);
        console.log(result);
    } catch (error) {
        console.error('Error:', error);
    }
}
```

#### cURL
```bash
# 登录
curl -X POST http://your-domain.com/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"your_password"}'

# 上传文件
curl -X POST http://your-domain.com/upload \
    -H "Authorization: Bearer your_token" \
    -F "file=@/path/to/file.pdf" \
    -F "save_all=true"
```

### WebSocket 支持

对于需要实时进度反馈的大文件上传，我们也提供了 WebSocket 接口：

```javascript
const ws = new WebSocket('ws://your-domain.com/ws/upload');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Upload progress:', data.progress);
    console.log('Status:', data.status);
};

ws.onopen = () => {
    // 发送文件数据
    ws.send(JSON.stringify({
        type: 'start_upload',
        filename: 'large_file.pdf'
    }));
};
```

响应示例：
```json
{
    "type": "progress",
    "data": {
        "filename": "large_file.pdf",
        "progress": 45,
        "bytes_uploaded": 1048576,
        "total_bytes": 2097152,
        "status": "uploading"
    }
}
```

## 配置说明

### 基础配置
- `ADMIN_USER`: 管理员用户名（默认：admin）
- `ADMIN_PASSWORD`: 管理员密码
- `MAX_FILE_SIZE`: 最大文件大小（MB）
- `CORS_ALLOW_ORIGINS`: CORS允许的源

### 安全配置
- `JWT_SECRET_KEY`: JWT密钥（至少32字符）
- `JWT_ALGORITHM`: JWT算法（默认：HS256）
- `TOKEN_EXPIRY`: 访问令牌过期时间（秒）
- `REFRESH_TOKEN_EXPIRY`: 刷新令牌过期时间（秒）
- `MAX_FAILED_ATTEMPTS`: 最大失败尝试次数
- `LOCKOUT_DURATION`: 账户锁定时间（秒）
- `SESSION_TIMEOUT`: 会话超时时间（秒）

### 存储配置
- `STORAGE_TYPE`: 存储类型（local/s3）
- `LOCAL_STORAGE_PATH`: 本地存储路径
- `S3_ACCESS_KEY`: S3访问密钥
- `S3_SECRET_KEY`: S3密钥
- `S3_BUCKET_NAME`: S3存储桶名称
- `S3_ENDPOINT_URL`: S3端点URL

### 功能配置
- `ENABLE_OCR`: 启用OCR功能
- `OCR_ENDPOINT`: OCR服务端点
- `ENABLE_VISION`: 启用视觉处理
- `AZURE_SPEECH_KEY`: Azure语音服务密钥
- `AZURE_SPEECH_REGION`: Azure语音服务区域

## 常见问题

### 安装问题
- *依赖安装失败*：
  - 确保已安装Python 3.9或更高版本
  - 在Windows上可能需要安装Visual C++ Build Tools
  - 某些依赖可能需要额外的系统库

### 运行问题
- *存储相关错误*：
  - 确保存储路径具有正确的权限
  - S3配置需要正确的访问凭证
  - 本地存储需要足够的磁盘空间

### 安全问题
- *认证失败*：
  - 检查JWT密钥配置
  - 确保密码符合复杂度要求
  - 检查IP白名单配置

## 安全建议

### 生产环境部署
1. 使用强密码和长JWT密钥
2. 启用所有安全特性
3. 配置适当的速率限制
4. 使用HTTPS
5. 定期更新依赖
6. 监控审计日志

### 访问控制
1. 限制允许的IP和域名
2. 设置合理的会话超时
3. 启用账户锁定机制
4. 定期轮换密钥和凭证

## 贡献指南
1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证
MIT License
