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
    """Get authentication configuration"""
    return {
        "admin_user": ADMIN_USER,
        "admin_password": ADMIN_PASSWORD,
        "require_auth": REQUIRE_AUTH,
        "whitelist_domains": WHITELIST_DOMAINS,
        "whitelist_ips": WHITELIST_IPS,
    }


@app.post("/root/config")
async def update_root_config(request: Request):
    """Update authentication configuration"""
    try:
        config = await request.json()
        
        # Update authentication environment variables
        os.environ["ADMIN_USER"] = config["admin_user"]
        os.environ["ADMIN_PASSWORD"] = config["admin_password"]
        os.environ["REQUIRE_AUTH"] = str(config["require_auth"]).lower()
        os.environ["WHITELIST_DOMAINS"] = ",".join(config["whitelist_domains"])
        os.environ["WHITELIST_IPS"] = ",".join(config["whitelist_ips"])
        
        # Reload authentication config module variables
        global ADMIN_USER, ADMIN_PASSWORD, REQUIRE_AUTH, WHITELIST_DOMAINS, WHITELIST_IPS
        
        ADMIN_USER = config["admin_user"]
        ADMIN_PASSWORD = config["admin_password"]
        REQUIRE_AUTH = config["require_auth"]
        WHITELIST_DOMAINS = config["whitelist_domains"]
        WHITELIST_IPS = config["whitelist_ips"]
        
        return {"status": "success"}
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
