from os import environ
import secrets
from typing import List
import json
import os

# 使用容器中的持久化目录
CONFIG_DIR = "/data"
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def to_str(key: str, default: str = "") -> str:
    """Converts string to string."""

    value = environ.get(key, default)
    return value.strip()


def to_none_str(key: str, default: str = None) -> str:
    """Converts string to string."""

    value = environ.get(key, default)
    return value.strip() if value else None


def to_endpoint(key: str, default: str = "") -> str:
    """Converts string to string."""
    return to_str(key, default).rstrip("/")


def to_list(key: str, default: list) -> list:
    """Converts comma-separated string to list."""
    key = to_str(key, "")
    if not key:
        return default

    return [item for item in key.split(",") if item]


def to_bool(key: str, default: bool) -> bool:
    """Converts string to bool."""
    value = to_str(key, "")
    if not value:
        return default

    return value.lower() == "true" or value == "1"


def to_float(key: str, default: float) -> float:
    """Converts string to float."""
    value = to_str(key, "")
    if not value:
        return default

    return float(value)


def to_int(value: str, default: int) -> int:
    """Converts string to int."""
    value = to_str(value, "")
    if not value:
        return default

    return int(value)


# Auth Config
ADMIN_USER = to_str("ADMIN_USER", "root")  # Default admin username
ADMIN_PASSWORD = to_str("ADMIN_PASSWORD", "root123456")  # Default admin password
WHITELIST_DOMAINS = to_list("WHITELIST_DOMAINS", [])  # Whitelisted domains
WHITELIST_IPS = to_list("WHITELIST_IPS", [])  # Whitelisted IP addresses
REQUIRE_AUTH = to_bool("REQUIRE_AUTH", True)  # Default to require auth

def is_ip_allowed(ip: str) -> bool:
    """Check if IP is in whitelist."""
    if not WHITELIST_IPS:
        return False
    return ip in WHITELIST_IPS or ip.startswith(tuple(WHITELIST_IPS))

def is_domain_allowed(domain: str) -> bool:
    """Check if domain is in whitelist."""
    if not WHITELIST_DOMAINS:
        return False
    return domain in WHITELIST_DOMAINS or domain.endswith(tuple(WHITELIST_DOMAINS))

# General Config
CORS_ALLOW_ORIGINS = to_list("CORS_ALLOW_ORIGINS", ["*"])  # CORS Allow Origins
MAX_FILE_SIZE = to_float("MAX_FILE_SIZE", -1)  # Max File Size
PDF_MAX_IMAGES = to_int("PDF_MAX_IMAGES", 10)  # PDF Max Images
AZURE_SPEECH_KEY = to_str("AZURE_SPEECH_KEY")  # Azure Speech Key
AZURE_SPEECH_REGION = to_str("AZURE_SPEECH_REGION")  # Azure Speech Region
ENABLE_AZURE_SPEECH = AZURE_SPEECH_KEY and AZURE_SPEECH_REGION  # Enable Azure Speech

# Storage Config
STORAGE_TYPE = to_str("STORAGE_TYPE", "common")  # Storage Type
LOCAL_STORAGE_DOMAIN = to_str("LOCAL_STORAGE_DOMAIN", "").rstrip("/")  # Local Storage Domain
S3_BUCKET = to_str("S3_BUCKET", "")  # S3 Bucket
S3_ACCESS_KEY = to_str("S3_ACCESS_KEY", "")  # S3 Access Key
S3_SECRET_KEY = to_str("S3_SECRET_KEY", "")  # S3 Secret Key
S3_REGION = to_str("S3_REGION", "")  # S3 Region
S3_DOMAIN = to_endpoint("S3_DOMAIN", "")  # S3 Domain (Optional)
S3_DIRECT_URL_DOMAIN = to_endpoint("S3_DIRECT_URL_DOMAIN", "")  # S3 Direct/Proxy URL Domain (Optional)
S3_SIGN_VERSION = to_none_str("S3_SIGN_VERSION")  # S3 Sign Version
S3_API = S3_DOMAIN or f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com"  # S3 API
S3_SPACE = S3_DIRECT_URL_DOMAIN or S3_API  # S3 Image URL Domain
TG_ENDPOINT = to_endpoint("TG_ENDPOINT", "")  # Telegram Endpoint
TG_PASSWORD = to_str("TG_PASSWORD", "")  # Telegram Password
TG_API = TG_ENDPOINT + "/api" + (f"?pass={TG_PASSWORD}" if TG_PASSWORD and len(TG_PASSWORD) > 0 else "")  # Telegram API

# File API Configuration
FILE_API_ENDPOINT = to_str("FILE_API_ENDPOINT", "")  # File API Endpoint
FILE_API_KEY = to_str("FILE_API_KEY", "")  # File API Key

# OCR Config
OCR_ENDPOINT = to_endpoint("OCR_ENDPOINT", "")  # OCR Endpoint
OCR_SKIP_MODELS = to_list("OCR_SKIP_MODELS", [])  # OCR Skip Models
OCR_SPEC_MODELS = to_list("OCR_SPEC_MODELS", [])  # OCR Specific Models

# Response Format Config
RESPONSE_CODE_FIELD = to_str("RESPONSE_CODE_FIELD", "code")  # Response code field name
RESPONSE_MSG_FIELD = to_str("RESPONSE_MSG_FIELD", "msg")    # Response message field name
RESPONSE_SN_FIELD = to_str("RESPONSE_SN_FIELD", "sn")      # Response serial number field name
RESPONSE_DATA_FIELD = to_str("RESPONSE_DATA_FIELD", "data") # Response data field name

# Response Data Format Config
RESPONSE_URL_FIELD = to_str("RESPONSE_URL_FIELD", "url")        # URL field in data
RESPONSE_FILENAME_FIELD = to_str("RESPONSE_FILENAME_FIELD", "filename")  # Filename field in data
RESPONSE_IMAGE_FIELD = to_str("RESPONSE_IMAGE_FIELD", "image")  # Image flag field in data

# Response Code Config
RESPONSE_SUCCESS_CODE = to_int("RESPONSE_SUCCESS_CODE", 0)  # Success response code
RESPONSE_ERROR_CODE = to_int("RESPONSE_ERROR_CODE", 1)    # Error response code

def format_response(success: bool, message: str, data: dict = None) -> dict:
    """Format response according to configuration"""
    return {
        RESPONSE_CODE_FIELD: RESPONSE_SUCCESS_CODE if success else RESPONSE_ERROR_CODE,
        RESPONSE_MSG_FIELD: message,
        RESPONSE_SN_FIELD: secrets.token_hex(8),
        RESPONSE_DATA_FIELD: data or {}
    }

def format_upload_data(url: str = "", filename: str = "", is_image: bool = False) -> dict:
    """Format upload response data according to configuration"""
    return {
        RESPONSE_URL_FIELD: url,
        RESPONSE_FILENAME_FIELD: filename,
        RESPONSE_IMAGE_FIELD: is_image
    }

def load_config_file():
    """Load configuration from file."""
    # 确保配置目录存在
    os.makedirs(CONFIG_DIR, exist_ok=True)
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for key, value in config.items():
                    if isinstance(value, list):
                        environ[key] = ",".join(str(x) for x in value)
                    elif isinstance(value, bool):
                        environ[key] = str(value).lower()
                    elif value is not None:  # 只设置非None的值
                        environ[key] = str(value)
        except Exception as e:
            print(f"Error loading config file: {e}")

def save_config_file():
    """Save configuration to file."""
    # 确保配置目录存在
    os.makedirs(CONFIG_DIR, exist_ok=True)
    
    config = {
        # Auth Config
        "ADMIN_USER": ADMIN_USER,
        "ADMIN_PASSWORD": ADMIN_PASSWORD,
        "WHITELIST_DOMAINS": WHITELIST_DOMAINS,
        "WHITELIST_IPS": WHITELIST_IPS,
        "REQUIRE_AUTH": REQUIRE_AUTH,
        
        # General Config
        "CORS_ALLOW_ORIGINS": CORS_ALLOW_ORIGINS,
        "MAX_FILE_SIZE": MAX_FILE_SIZE,
        "PDF_MAX_IMAGES": PDF_MAX_IMAGES,
        "AZURE_SPEECH_KEY": AZURE_SPEECH_KEY,
        "AZURE_SPEECH_REGION": AZURE_SPEECH_REGION,
        
        # Storage Config
        "STORAGE_TYPE": STORAGE_TYPE,
        "LOCAL_STORAGE_DOMAIN": LOCAL_STORAGE_DOMAIN,
        "S3_BUCKET": S3_BUCKET,
        "S3_ACCESS_KEY": S3_ACCESS_KEY,
        "S3_SECRET_KEY": S3_SECRET_KEY,
        "S3_REGION": S3_REGION,
        "S3_DOMAIN": S3_DOMAIN,
        "S3_DIRECT_URL_DOMAIN": S3_DIRECT_URL_DOMAIN,
        "S3_SIGN_VERSION": S3_SIGN_VERSION,
        
        # Telegram Config
        "TG_ENDPOINT": TG_ENDPOINT,
        "TG_PASSWORD": TG_PASSWORD,
        
        # File API Config
        "FILE_API_ENDPOINT": FILE_API_ENDPOINT,
        "FILE_API_KEY": FILE_API_KEY,
        
        # OCR Config
        "OCR_ENDPOINT": OCR_ENDPOINT,
        "OCR_SKIP_MODELS": OCR_SKIP_MODELS,
        "OCR_SPEC_MODELS": OCR_SPEC_MODELS,
        
        # Response Format Config
        "RESPONSE_CODE_FIELD": RESPONSE_CODE_FIELD,
        "RESPONSE_MSG_FIELD": RESPONSE_MSG_FIELD,
        "RESPONSE_SN_FIELD": RESPONSE_SN_FIELD,
        "RESPONSE_DATA_FIELD": RESPONSE_DATA_FIELD,
        "RESPONSE_URL_FIELD": RESPONSE_URL_FIELD,
        "RESPONSE_FILENAME_FIELD": RESPONSE_FILENAME_FIELD,
        "RESPONSE_IMAGE_FIELD": RESPONSE_IMAGE_FIELD,
        "RESPONSE_SUCCESS_CODE": RESPONSE_SUCCESS_CODE,
        "RESPONSE_ERROR_CODE": RESPONSE_ERROR_CODE
    }
    
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
            # 确保写入到磁盘
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        print(f"Error saving config file: {e}")

# Load config from file at startup
load_config_file()
