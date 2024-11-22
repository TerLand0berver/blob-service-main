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
        
        # Reload config module to update all variables
        import importlib
        import config
        importlib.reload(config)
        
        # Update global variables from reloaded config
        global ADMIN_USER, ADMIN_PASSWORD, REQUIRE_AUTH, WHITELIST_DOMAINS, WHITELIST_IPS
        global CORS_ALLOW_ORIGINS, MAX_FILE_SIZE, PDF_MAX_IMAGES
        global AZURE_SPEECH_KEY, AZURE_SPEECH_REGION, ENABLE_AZURE_SPEECH
        global STORAGE_TYPE, LOCAL_STORAGE_DOMAIN
        global S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY, S3_REGION, S3_DOMAIN
        global S3_DIRECT_URL_DOMAIN, S3_SIGN_VERSION, S3_API, S3_SPACE
        global TG_ENDPOINT, TG_PASSWORD, TG_API
        global FILE_API_ENDPOINT, FILE_API_KEY
        global OCR_ENDPOINT, OCR_SKIP_MODELS, OCR_SPEC_MODELS
        
        ADMIN_USER = config.ADMIN_USER
        ADMIN_PASSWORD = config.ADMIN_PASSWORD
        REQUIRE_AUTH = config.REQUIRE_AUTH
        WHITELIST_DOMAINS = config.WHITELIST_DOMAINS
        WHITELIST_IPS = config.WHITELIST_IPS
        
        CORS_ALLOW_ORIGINS = config.CORS_ALLOW_ORIGINS
        MAX_FILE_SIZE = config.MAX_FILE_SIZE
        PDF_MAX_IMAGES = config.PDF_MAX_IMAGES
        
        AZURE_SPEECH_KEY = config.AZURE_SPEECH_KEY
        AZURE_SPEECH_REGION = config.AZURE_SPEECH_REGION
        ENABLE_AZURE_SPEECH = config.ENABLE_AZURE_SPEECH
        
        STORAGE_TYPE = config.STORAGE_TYPE
        LOCAL_STORAGE_DOMAIN = config.LOCAL_STORAGE_DOMAIN
        
        S3_BUCKET = config.S3_BUCKET
        S3_ACCESS_KEY = config.S3_ACCESS_KEY
        S3_SECRET_KEY = config.S3_SECRET_KEY
        S3_REGION = config.S3_REGION
        S3_DOMAIN = config.S3_DOMAIN
        S3_DIRECT_URL_DOMAIN = config.S3_DIRECT_URL_DOMAIN
        S3_SIGN_VERSION = config.S3_SIGN_VERSION
        S3_API = config.S3_API
        S3_SPACE = config.S3_SPACE
        
        TG_ENDPOINT = config.TG_ENDPOINT
        TG_PASSWORD = config.TG_PASSWORD
        TG_API = config.TG_API
        
        FILE_API_ENDPOINT = config.FILE_API_ENDPOINT
        FILE_API_KEY = config.FILE_API_KEY
        
        OCR_ENDPOINT = config.OCR_ENDPOINT
        OCR_SKIP_MODELS = config.OCR_SKIP_MODELS
        OCR_SPEC_MODELS = config.OCR_SPEC_MODELS
        
        # Also update CORS middleware
        app.user_middleware[0].options["allow_origins"] = CORS_ALLOW_ORIGINS
        
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
