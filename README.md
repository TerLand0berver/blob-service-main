<div align="center">
    
# Chat Nio Blob Service

### File Service for Chat Nio

[![Deploy to Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/TerLand0berver/blob-service-main)

[![Deploy on Zeabur](https://zeabur.com/button.svg)](https://zeabur.com/templates/RWGFOH)

</div>

## Features
- Out-of-the-Box: No External Dependencies Required & Support Vercel/Render One-Click Deployment
- Multiple File Types: Support Text, Pdf, Docx, Excel, Image, Audio etc.
- Multiple Storage Options: Base64, Local, S3, Cloudflare R2, Min IO, Telegram CDN, File API etc.
- OCR Support: Extract Text from Image (Require Paddle OCR API)
- Audio Support: Convert Audio to Text (Require Azure Speech to Text Service)
- Authentication Support: Basic Authentication and Domain Whitelisting
- Dynamic Configuration: Web UI for Storage and Authentication Settings

## Recent Updates
### Authentication Enhancement
- Added basic authentication support with configurable username/password
- Implemented domain whitelisting for trusted access
- Added web-based configuration interface
- Runtime configuration updates without restart

### Storage Options Enhancement
- Added File API storage support for flexible file handling
- Improved Telegram CDN integration
- Enhanced S3-compatible storage configurations
- Added dynamic storage type switching

## Supported File Types
- Text
- Image (require vision models)
- Audio (require Azure Speech to Text Service)
- Docx (not support .doc)
- Pdf
- Pptx (not support .ppt)
- Xlsx (support .xls)

## Deploy by Docker
> Image: `teraccc/chatnio-blob-service`

```shell
docker run -p 8000:8000 teraccc/chatnio-blob-service

# with environment variables
# docker run -p 8000:8000 -e AZURE_SPEECH_KEY="..." -e AZURE_SPEECH_REGION="..." teraccc/chatnio-blob-service


# if you are using `local` storage type, you need to mount volume (/static) to the host
# docker run -p 8000:8000 -v /path/to/static:/static teraccc/chatnio-blob-service
```

> Deploy to [Render.com](https://render.com)
> 
> [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://dashboard.render.com/select-image?type=web&image=programzmh%2Fchatnio-blob-service)
>
> 
> Select **Web Service** and **Docker** Image, then input the image `teraccc/chatnio-blob-service` and click **Create Web Service**.
> > Render.com Includes Free **750 Hours** of Usage per Month 
> 

## Deploy by Source Code
The service will be running on `http://localhost:8000`
## Run
```shell
git clone --branch=main https://github.com/TerLand0berver/blob-service-main
cd chatnio-blob-service

pip install -r requirements.txt
uvicorn main:app

# enable hot reload
# uvicorn main:app --reload
```

## API
`POST` `/upload` Upload a file
```json
{
    "file": "[file]",
    "enable_ocr": false,
    "enable_vision": true,
    "save_all": false
}
```

| Parameter       | Type    | Description                                                                          |
|-----------------|---------|--------------------------------------------------------------------------------------|
| `file`          | *File   | File to Upload                                                                       |
| `enable_ocr`    | Boolean | Enable OCR (Default: `false`) <br/>**should configure OCR config*                    |
| `enable_vision` | Boolean | Enable Vision (Default: `true`) <br/>**skip if `enable_ocr` is true*                 |
| `save_all`      | Boolean | Save All Images (Default: `false`) <br/>**store all types of files without handling* |


Response

```json
{
  "status": true,
  "type": "pdf",
  "content": "...",
  "error": ""
}
```

| Parameter       | Type     | Description    |
|-----------------|----------|----------------|
| `status`        | Boolean  | Request Status |
| `type`          | String   | File Type      |
| `content`       | String   | File Data      |
| `error`         | String   | Error Message  |

## Environment Variables

### `1` General Config (Optional)

- `PDF_MAX_IMAGES`: Max Images Extracted from a PDF File (Default: `10`)
    - **0**: Never Extract Images
    - **-1**: Extract All Images
    - **other**: Extract Top N Images
    - *Tips: The extracted images will be **treated as a normal image** file and directly processed*.
- `MAX_FILE_SIZE`: Max Uploaded File Size MiB (Default: `-1`, No Limit)
  - *Tips: Size limit is also depend on the server configuration (e.g. Nginx/Apache Config, Vercel Free Plan Limit **5MB** Body Size)*
- `CORS_ALLOW_ORIGINS`: CORS Allow Origins (Default: `*`)
  - e.g.: *http://localhost:3000,https://example.com*

### `2` Audio Config (Optional)
- `AZURE_SPEECH_KEY`: Azure Speech to Text Service Key (Required for Audio Support)
- `AZURE_SPEECH_REGION`: Azure Speech to Text Service Region (Required for Audio Support)

### `3` Storage Config (Optional)
> [!NOTE]
> Storage Config Apply to **Image** Files And `Save All` Option Only.

1. No Storage (Default)
   - [x] **No Storage Required & No External Dependencies**
   - [x] Base64 Encoding/Decoding
   - [x] Do **Not** Store Anything
   - [x] Support Serverless Deployment **Without Storage** (e.g. Vercel)
   - [ ] No Direct URL Access *(Base64 not support models like `gpt-4-all`)*

2. Local Storage
   - [ ] **Require Server Environment** (e.g. VPS, Docker)
   - [x] Support Direct URL Access
   - [x] Payless Storage Cost
   - Config:
     - set env `STORAGE_TYPE` to `local` (e.g. `STORAGE_TYPE=local`)
     - set env `LOCAL_STORAGE_DOMAIN` to your deployment domain (e.g. `LOCAL_STORAGE_DOMAIN=http://blob-service.onrender.com`)
     - if you are using Docker, you need to mount volume `/app/static` to the host (e.g. `-v /path/to/static:/app/static`)
     
3. [AWS S3](https://aws.amazon.com/s3)
   - [ ] **Payment Storage Cost**
   - [x] Support Direct URL Access
   - [x] China Mainland User Friendly
   - Config:
     - set env `STORAGE_TYPE` to `s3` (e.g. `STORAGE_TYPE=s3`)
     - set env `S3_ACCESS_KEY` to your AWS Access Key ID
     - set env `S3_SECRET_KEY` to your AWS Secret Access Key
     - set env `S3_BUCKET` to your AWS S3 Bucket Name
     - set env `S3_REGION` to your AWS S3 Region

4. [Cloudflare R2](https://www.cloudflare.com/zh-cn/developer-platform/r2)
   - [x] **Free Storage Quota ([10GB Storage & Zero Outbound Cost]((https://developers.cloudflare.com/r2/pricing/)))**
   - [x] Support Direct URL Access
   - Config *(S3 Compatible)*:
     - set env `STORAGE_TYPE` to `s3` (e.g. `STORAGE_TYPE=s3`)
     - set env `S3_ACCESS_KEY` to your Cloudflare R2 Access Key ID
     - set env `S3_SECRET_KEY` to your Cloudflare R2 Secret Access Key
     - set env `S3_BUCKET` to your Cloudflare R2 Bucket Name
     - set env `S3_DOMAIN` to your Cloudflare R2 Domain Name (e.g. `https://<account-id>.r2.cloudflarestorage.com`)
     - set env `S3_DIRECT_URL_DOMAIN` to your Cloudflare R2 Public URL Access Domain Name ([Open Public URL Access](https://developers.cloudflare.com/r2/buckets/public-buckets/), e.g. `https://pub-xxx.r2.dev`)

5. [Min IO](https://min.io)
    - [x] **Self Hosted**
    - [x] Reliable & Flexible Storage
    - Config *(S3 Compatible)*:
      - set env `STORAGE_TYPE` to `s3` (e.g. `STORAGE_TYPE=s3`)
      - set env `S3_SIGN_VERSION` to `s3v4` (e.g. `S3_SIGN_VERSION=s3v4`)
      - set env `S3_ACCESS_KEY` to your Min IO Access Key ID
      - set env `S3_SECRET_KEY` to your Min IO Secret Access Key
      - set env `S3_BUCKET` to your Min IO Bucket Name
      - set env `S3_DOMAIN` to your Min IO Domain Name (e.g. `https://oss.example.com`)
      - *[Optional] If you are using CDN, you can set `S3_DIRECT_URL_DOMAIN` to your Min IO Public URL Access Domain Name (e.g. `https://cdn-hk.example.com`)*

6. [Telegram CDN](https://github.com/csznet/tgState)
    - [x] **Free Storage (Rate Limit)**
    - [x] Support Direct URL Access *(China Mainland User Unfriendly)*
    - [x] **Limited** File Type & Format
    - Config:
      - set env `STORAGE_TYPE` to `tg` (e.g. `STORAGE_TYPE=tg`)
      - set env `TG_ENDPOINT` to your TG-STATE Endpoint (e.g. `TG_ENDPOINT=https://tgstate.vercel.app`)
      - *[Optional] if you are using password authentication, you can set `TG_PASSWORD` to your TG-STATE Password*

7. File API
    - [x] **Custom File Storage API**
    - [x] Flexible Integration
    - [x] Support Direct URL Access
    - Config:
      - set env `STORAGE_TYPE` to `file_api` (e.g. `STORAGE_TYPE=file_api`)
      - set env `FILE_API_ENDPOINT` to your File API endpoint
      - set env `FILE_API_KEY` to your File API authentication key (optional)

### `4` Authentication Config (Optional)
> [!NOTE]
> Authentication can be managed through the web UI at `/config` or environment variables.

- `ADMIN_USER`: Admin username for authentication (Default: `telagod`)
- `ADMIN_PASSWORD`: Admin password (Default: randomly generated)
- `WHITELIST_DOMAINS`: Comma-separated list of allowed domains (Default: empty)
- `REQUIRE_AUTH`: Enable/disable authentication (Default: `true`)

### `5` OCR Config (Optional)
> [!NOTE]
> OCR Support is based on [PaddleOCR API](https://github.com/cgcel/PaddleOCRFastAPI) ( Self Hosted Open Source)

- `OCR_ENDPOINT` Paddle OCR Endpoint
    - *e.g.: *http://example.com:8000*

## Common Errors
- *Cannot Use `Save All` Options Without Storage Config*:
    - This error occurs when you enable `save_all` option without storage config. You need to set `STORAGE_TYPE` to `local` or other storage type to use this option.
- *Trying to upload image with Vision disabled. Enable Vision or OCR to process image*:
    - This error occurs when you disable `enable_vision` and `enable_ocr` at the same time. You need to enable at least one of them to process image files.
- *.ppt files are not supported, only .pptx files are supported*:
    - This error occurs when you upload a old version of Office PowerPoint file. You need to convert it to `.pptx` format to process it.
- *.doc files are not supported, only .docx files are supported*:
    - This error occurs when you upload a old version of Office Word file. You need to convert it to `.docx` format to process it.
- *File Size Limit Exceeded*:
    - This error occurs when you upload a file that exceeds the `MAX_FILE_SIZE` limit. You need to reduce the file size to upload it.

## Development
- **~/config.py**: Env Config
- **~/main.py**: Entry Point
- **~/utils.py**: Utilities
- **~/handlers**: File Handlers
- **~/store**: Storage Handlers
- **~/static**: Static Files (if using **local** storage)

## Tech Stack
- Python & FastAPI

## License
Apache License 2.0

# Blob Service

一个功能强大的文件处理服务，支持多种存储后端和灵活的配置管理。

## 功能特点

🚀 **多存储后端支持**
- 本地文件存储
- S3 兼容存储
- Telegram 存储
- Base64 编码
- 自定义文件 API

📝 **配置管理**
- 运行时配置更新
- 配置持久化
- 环境变量支持

🔒 **安全特性**
- 文件类型检测
- 大小限制
- 安全的文件名

## 快速开始

### Docker 部署

```bash
git clone https://github.com/yourusername/blob-service.git
cd blob-service
cp .env.example .env
docker-compose up -d
```

### 手动安装

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## 配置

### 环境变量
```env
STORAGE_TYPE=local
MAX_FILE_SIZE=10485760
ALLOWED_TYPES=image/*,application/pdf
S3_ACCESS_KEY=your_key
S3_SECRET_KEY=your_secret
TG_BOT_TOKEN=your_token
```

### 配置文件
```json
{
  "storage": {
    "type": "local",
    "path": "/data/files"
  },
  "limits": {
    "max_file_size": 10485760,
    "allowed_types": ["image/*"]
  }
}
```

## API

### 上传文件
```http
POST /upload
Content-Type: multipart/form-data
```

### 更新配置
```http
POST /config
Content-Type: application/json
```

## 存储后端

### 本地存储
- 本地文件系统
- 自定义路径
- 目录管理

### S3 存储
- 标准 S3 API
- 自定义域名
- 权限控制

### Telegram
- Bot API
- 大文件支持
- 自动生成访问链接

### Base64
- 编码存储
- 内联显示
- 小文件适用

## 开发

### 目录结构
```
blob-service/
├── config.py         # 配置管理
├── main.py          # 主程序入口
├── handlers/        # 处理器模块
│   ├── processor.py # 文件处理
│   └── response.py  # 响应格式化
├── store/          # 存储模块
│   ├── common.py   # 通用存储
│   ├── local.py    # 本地存储
│   ├── s3.py       # S3存储
│   └── telegram.py # Telegram存储
└── utils/          # 工具函数
```

### 添加新存储后端
1. 在 `store/` 创建新模块
2. 实现异步处理接口
   ```python
   async def process_file(file: UploadFile) -> str:
       """处理文件并返回URL"""
       pass
   ```
3. 注册处理器
4. 更新配置和文档

## 安全建议

### 配置安全
1. 使用环境变量存储敏感信息
2. 定期更新依赖包
3. 设置适当的文件权限

### 上传安全
1. 验证文件类型
2. 限制文件大小
3. 检查文件名安全性

### 访问控制
1. 配置跨域策略
2. 实施访问认证
3. 控制文件权限

## 常见问题

### 上传失败
- **问题**: 文件上传失败
- **解决方案**:
  1. 检查文件大小限制
  2. 验证文件类型
  3. 查看错误日志

### 配置问题
- **问题**: 配置无法更新
- **解决方案**:
  1. 检查配置文件权限
  2. 验证JSON格式
  3. 确认配置值类型

### 存储错误
- **问题**: 存储服务异常
- **解决方案**:
  1. 验证存储配置
  2. 检查网络连接
  3. 查看服务日志

## 许可证

MIT License
