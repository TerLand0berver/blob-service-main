from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from app.parsers.processor import process_file, read_file_size
from app.core.response import ResponseFormatter
from app.config import config
from app.parsers.ocr import create_ocr_task, deprecated_could_enable_ocr
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.core.security import SecurityValidator
import os
import secrets
from datetime import datetime
import jwt
from datetime import timedelta

app = FastAPI()

# Add CORS middleware with secure settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOW_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
    max_age=3600,
)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=config.RATE_LIMIT_PER_MINUTE,
    burst_limit=config.RATE_LIMIT_BURST
)

# Add authentication middleware
app.add_middleware(AuthMiddleware)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
async def root():
    """Redirect to login page if not authenticated, otherwise show index page"""
    return FileResponse("app/static/login.html")


@app.get("/index")
async def index_page():
    """Main page for file upload and management"""
    return FileResponse("app/static/index.html")


@app.get("/config")
async def config_page():
    """Configuration page"""
    return FileResponse("app/static/config.html")


@app.get("/api/config")
async def get_config():
    """Get basic configuration parameters"""
    return ResponseFormatter.success(
        message="Configuration retrieved successfully",
        data={
            "storage_type": config.STORAGE_TYPE,
            "api_endpoint": config.FILE_API_ENDPOINT,
            "api_key": config.FILE_API_KEY
        }
    )


@app.post("/api/config")
async def update_config(request: Request):
    """Update configuration parameters"""
    try:
        data = await request.json()
        # Update configuration
        if "storage_type" in data:
            config.STORAGE_TYPE = data["storage_type"]
        if "api_endpoint" in data:
            config.FILE_API_ENDPOINT = data["api_endpoint"]
        if "api_key" in data:
            config.FILE_API_KEY = data["api_key"]
        
        return ResponseFormatter.success(
            message="Configuration updated successfully"
        )
    except Exception as e:
        return ResponseFormatter.error(
            message=f"Failed to update configuration: {str(e)}",
            status_code=400
        )


@app.get("/favicon.ico")
async def favicon():
    """Serve favicon"""
    return FileResponse("app/static/favicon.ico")


@app.get("/login")
async def login_page():
    """Login page"""
    return FileResponse("app/static/login.html")


@app.post("/api/auth/login")
async def login(request: Request):
    try:
        data = await request.json()
        username = data.get("username")
        password = data.get("password")
        
        if not username or not password:
            return ResponseFormatter.error(
                message="Username and password are required",
                status_code=400
            )
            
        # Validate credentials
        if username != config.ADMIN_USER:
            # Use constant time comparison to prevent timing attacks
            from hmac import compare_digest
            compare_digest(password, "dummy")  # Prevent timing attacks
            return ResponseFormatter.error(
                message="Invalid credentials",
                status_code=401
            )
            
        # Validate password strength for new password
        if "new_password" in data:
            is_valid, error_msg = SecurityValidator.validate_password(data["new_password"])
            if not is_valid:
                return ResponseFormatter.error(
                    message=error_msg,
                    status_code=400
                )
            password = data["new_password"]
            
        # Verify password using secure hash comparison
        if not SecurityValidator.verify_password(password, config.ADMIN_PASSWORD):
            return ResponseFormatter.error(
                message="Invalid credentials",
                status_code=401
            )
        
        # Generate JWT token with roles and permissions
        token = jwt.encode(
            {
                "sub": username,
                "exp": datetime.utcnow() + timedelta(hours=24),
                "iat": datetime.utcnow(),
                "jti": secrets.token_hex(16),
                "roles": ["admin"],
                "permissions": ["upload", "download", "delete", "configure"]
            },
            config.JWT_SECRET_KEY,
            algorithm="HS256"
        )
        
        response = ResponseFormatter.success(
            message="Login successful",
            data={"token": token}
        )
        
        # Set secure cookie
        response.set_cookie(
            key="auth_token",
            value=token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=86400,  # 24 hours
            path="/"
        )
        
        return response
    except Exception as e:
        return ResponseFormatter.error(
            message=str(e),
            status_code=500
        )


@app.post("/api/auth/logout")
async def logout():
    """Handle logout request"""
    response = ResponseFormatter.success(message="Logout successful")
    response.delete_cookie(key="auth_token")
    return response


@app.post("/api/upload")
async def upload(
    file: UploadFile = File(...),
    enable_ocr: bool = Form(default=False),
    enable_vision: bool = Form(default=True),
    save_all: bool = Form(default=False),
):
    try:
        # Validate file
        is_valid, error_msg = await SecurityValidator.validate_file(file, config.MAX_FILE_SIZE)
        if not is_valid:
            return ResponseFormatter.error(
                message=error_msg,
                status_code=400
            )
        
        if not file or not file.filename:
            return ResponseFormatter.error(
                message="No file provided",
                status_code=400,
                data={
                    "url": "",
                    "filename": "",
                    "image": False
                }
            )

        # 验证文件类型
        filename = file.filename.lower()
        allowed_extensions = {
            '.txt', '.pdf', '.doc', '.docx', 
            '.xls', '.xlsx', '.csv', '.tsv',
            '.py', '.js', '.java', '.cpp', '.c',
            '.h', '.cs', '.php', '.rb', '.go',
            '.rs', '.swift', '.kt', '.scala'
        }
        
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in allowed_extensions:
            return ResponseFormatter.error(
                message=f"Unsupported file type: {file_ext}",
                status_code=400,
                data={
                    "url": "",
                    "filename": filename,
                    "image": False
                }
            )

        if len(config.OCR_ENDPOINT) == 0:
            enable_ocr = False

        # 检查文件大小
        if config.MAX_FILE_SIZE > 0:
            file_size = await read_file_size(file)
            if file_size > config.MAX_FILE_SIZE:
                return ResponseFormatter.error(
                    message=f"File size {file_size:.2f} MiB exceeds the limit of {config.MAX_FILE_SIZE} MiB",
                    status_code=400,
                    data={
                        "url": "",
                        "filename": file.filename,
                        "image": False
                    }
                )

        filetype, contents = await process_file(
            file,
            enable_ocr=enable_ocr,
            enable_vision=enable_vision,
            save_all=save_all,
        )

        # 检查是否是图片类型
        is_image = filetype in ["image", "png", "jpg", "jpeg", "gif", "webp"]

        # 检查返回的URL是否有效
        if not contents or len(contents.strip()) == 0:
            return ResponseFormatter.error(
                message="Failed to process file: empty URL returned",
                status_code=500,
                data={
                    "url": "",
                    "filename": file.filename,
                    "image": is_image
                }
            )

        return ResponseFormatter.success(
            message="File processed successfully",
            data={
                "url": contents.strip(),
                "filename": file.filename,
                "image": is_image
            }
        )
    except Exception as e:
        error_msg = str(e)
        print(f"Error processing file {file.filename if file else 'unknown'}: {error_msg}")
        return ResponseFormatter.error(
            message=error_msg,
            status_code=500,
            data={
                "url": "",
                "filename": file.filename if file else "",
                "image": False
            }
        )


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
