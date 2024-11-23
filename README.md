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
  - 图片处理和 OCR
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
docker pull your-registry/blob-service:latest

# 运行容器
docker run -d \
  -p 8000:8000 \
  -v /path/to/data:/app/data \
  -e ADMIN_USER=admin \
  -e ADMIN_PASSWORD=your-secure-password \
  -e JWT_SECRET_KEY=your-secret-key \
  your-registry/blob-service:latest
```

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
STORAGE_TYPE=local  # local, s3, azure
STORAGE_PATH=/app/data
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

- 作者：Your Name
- 邮箱：your.email@example.com
- GitHub：https://github.com/yourusername
