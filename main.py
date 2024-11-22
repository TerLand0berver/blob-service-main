from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from handlers.processor import process_file
from config import *
from handlers.ocr import create_ocr_task, deprecated_could_enable_ocr
from middleware.auth import AuthMiddleware
import os

app = FastAPI()

# Add authentication middleware
app.add_middleware(AuthMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.get("/config")
async def config_page():
    return FileResponse("static/config.html")


@app.get("/api/config")
async def get_config():
    return {
        "storage_type": STORAGE_TYPE,
        "api_endpoint": FILE_API_ENDPOINT,
        "api_key": FILE_API_KEY
    }


@app.post("/api/config")
async def update_config(request: Request):
    try:
        config = await request.json()
        
        # Update environment variables
        os.environ["STORAGE_TYPE"] = config["storage_type"]
        os.environ["FILE_API_ENDPOINT"] = config["api_endpoint"]
        os.environ["FILE_API_KEY"] = config["api_key"]
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/root")
async def root_page():
    """Root page for authentication and configuration"""
    return FileResponse("static/root.html")


@app.get("/root/config")
async def get_root_config():
    """Get all configuration parameters"""
    return {
        # Auth settings
        "admin_user": ADMIN_USER,
        "admin_password": ADMIN_PASSWORD,
        "require_auth": REQUIRE_AUTH,
        "whitelist_domains": WHITELIST_DOMAINS,
        "whitelist_ips": WHITELIST_IPS,
        
        # General settings
        "cors_allow_origins": CORS_ALLOW_ORIGINS,
        "max_file_size": MAX_FILE_SIZE,
        "pdf_max_images": PDF_MAX_IMAGES,
        
        # Azure Speech settings
        "azure_speech_key": AZURE_SPEECH_KEY,
        "azure_speech_region": AZURE_SPEECH_REGION,
        "enable_azure_speech": ENABLE_AZURE_SPEECH,
        
        # Storage settings
        "storage_type": STORAGE_TYPE,
        "local_storage_domain": LOCAL_STORAGE_DOMAIN,
        
        # S3 settings
        "s3_bucket": S3_BUCKET,
        "s3_access_key": S3_ACCESS_KEY,
        "s3_secret_key": S3_SECRET_KEY,
        "s3_region": S3_REGION,
        "s3_domain": S3_DOMAIN,
        "s3_direct_url_domain": S3_DIRECT_URL_DOMAIN,
        "s3_sign_version": S3_SIGN_VERSION,
        "s3_api": S3_API,
        "s3_space": S3_SPACE,
        
        # Telegram settings
        "tg_endpoint": TG_ENDPOINT,
        "tg_password": TG_PASSWORD,
        "tg_api": TG_API,
        
        # File API settings
        "file_api_endpoint": FILE_API_ENDPOINT,
        "file_api_key": FILE_API_KEY,
        
        # OCR settings
        "ocr_endpoint": OCR_ENDPOINT,
        "ocr_skip_models": OCR_SKIP_MODELS,
        "ocr_spec_models": OCR_SPEC_MODELS,
    }


@app.post("/root/config")
async def update_root_config(request: Request):
    """Update all configuration parameters"""
    try:
        config = await request.json()
        
        # Helper function to safely update environment variables
        def update_env(key: str, value, is_list: bool = False):
            if value is not None:
                if is_list and isinstance(value, list):
                    os.environ[key] = ",".join(str(x) for x in value)
                elif isinstance(value, bool):
                    os.environ[key] = str(value).lower()
                else:
                    os.environ[key] = str(value)

        # Update Auth settings
        update_env("ADMIN_USER", config.get("admin_user"))
        update_env("ADMIN_PASSWORD", config.get("admin_password"))
        update_env("REQUIRE_AUTH", config.get("require_auth"))
        update_env("WHITELIST_DOMAINS", config.get("whitelist_domains"), True)
        update_env("WHITELIST_IPS", config.get("whitelist_ips"), True)
        
        # Update General settings
        update_env("CORS_ALLOW_ORIGINS", config.get("cors_allow_origins"), True)
        update_env("MAX_FILE_SIZE", config.get("max_file_size"))
        update_env("PDF_MAX_IMAGES", config.get("pdf_max_images"))
        
        # Update Azure Speech settings
        update_env("AZURE_SPEECH_KEY", config.get("azure_speech_key"))
        update_env("AZURE_SPEECH_REGION", config.get("azure_speech_region"))
        
        # Update Storage settings
        update_env("STORAGE_TYPE", config.get("storage_type"))
        update_env("LOCAL_STORAGE_DOMAIN", config.get("local_storage_domain"))
        
        # Update S3 settings
        update_env("S3_BUCKET", config.get("s3_bucket"))
        update_env("S3_ACCESS_KEY", config.get("s3_access_key"))
        update_env("S3_SECRET_KEY", config.get("s3_secret_key"))
        update_env("S3_REGION", config.get("s3_region"))
        update_env("S3_DOMAIN", config.get("s3_domain"))
        update_env("S3_DIRECT_URL_DOMAIN", config.get("s3_direct_url_domain"))
        update_env("S3_SIGN_VERSION", config.get("s3_sign_version"))
        
        # Update Telegram settings
        update_env("TG_ENDPOINT", config.get("tg_endpoint"))
        update_env("TG_PASSWORD", config.get("tg_password"))
        
        # Update File API settings
        update_env("FILE_API_ENDPOINT", config.get("file_api_endpoint"))
        update_env("FILE_API_KEY", config.get("file_api_key"))
        
        # Update OCR settings
        update_env("OCR_ENDPOINT", config.get("ocr_endpoint"))
        update_env("OCR_SKIP_MODELS", config.get("ocr_skip_models"), True)
        update_env("OCR_SPEC_MODELS", config.get("ocr_spec_models"), True)
        
        # Reload config module variables
        reload_config_vars = [
            # Auth settings
            "ADMIN_USER", "ADMIN_PASSWORD", "REQUIRE_AUTH", "WHITELIST_DOMAINS", "WHITELIST_IPS",
            # General settings
            "CORS_ALLOW_ORIGINS", "MAX_FILE_SIZE", "PDF_MAX_IMAGES",
            # Azure Speech settings
            "AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION", "ENABLE_AZURE_SPEECH",
            # Storage settings
            "STORAGE_TYPE", "LOCAL_STORAGE_DOMAIN",
            # S3 settings
            "S3_BUCKET", "S3_ACCESS_KEY", "S3_SECRET_KEY", "S3_REGION",
            "S3_DOMAIN", "S3_DIRECT_URL_DOMAIN", "S3_SIGN_VERSION",
            "S3_API", "S3_SPACE",
            # Telegram settings
            "TG_ENDPOINT", "TG_PASSWORD", "TG_API",
            # File API settings
            "FILE_API_ENDPOINT", "FILE_API_KEY",
            # OCR settings
            "OCR_ENDPOINT", "OCR_SKIP_MODELS", "OCR_SPEC_MODELS"
        ]
        
        # Update global variables
        global_dict = globals()
        for var in reload_config_vars:
            if var in config:
                global_dict[var] = config[var]
            elif var == "ENABLE_AZURE_SPEECH":
                global_dict[var] = bool(config.get("azure_speech_key") and config.get("azure_speech_region"))
            elif var == "S3_API":
                global_dict[var] = config.get("s3_domain") or f"https://{config.get('s3_bucket')}.s3.{config.get('s3_region')}.amazonaws.com"
            elif var == "S3_SPACE":
                global_dict[var] = config.get("s3_direct_url_domain") or global_dict["S3_API"]
            elif var == "TG_API":
                tg_endpoint = config.get("tg_endpoint", "").rstrip("/")
                tg_password = config.get("tg_password", "")
                global_dict[var] = tg_endpoint + "/api" + (f"?pass={tg_password}" if tg_password else "")
        
        return {"status": "success", "message": "Configuration updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/favicon.ico")
def favicon():
    return FileResponse("favicon.ico")


@app.post("/upload")
async def upload(
        file: UploadFile = File(...),
        enable_ocr: bool = Form(default=False),
        enable_vision: bool = Form(default=True),
        save_all: bool = Form(default=False),
        model: str = Form(default=""),  # deprecated
):
    """Accepts file and returns its contents."""

    if model and len(model) > 0:
        # compatibility with deprecated model parameter
        enable_ocr = deprecated_could_enable_ocr(model)
        enable_vision = not enable_ocr

    if len(OCR_ENDPOINT) == 0:
        enable_ocr = False

    try:
        filetype, contents = await process_file(
            file,
            enable_ocr=enable_ocr,
            enable_vision=enable_vision,
            save_all=save_all,
        )
        return {
            "status": True,
            "content": contents,
            "type": filetype,
            "error": "",
        }
    except Exception as e:
        return {
            "status": False,
            "content": "",
            "type": "error",
            "error": str(e),
        }
