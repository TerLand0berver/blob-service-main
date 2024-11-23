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
