from os import environ
import secrets
from typing import List, Dict, Any, Optional
import json
import os
from pathlib import Path

# 配置目录和文件
CONFIG_DIR = "/data"
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

class ConfigurationError(Exception):
    """配置错误异常"""
    pass

class Config:
    """配置管理类"""
    
    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置"""
        # 1. 加载默认值
        self._load_defaults()
        # 2. 加载环境变量
        self._load_env()
        # 3. 加载持久化配置
        self._load_persistent()
        # 4. 验证配置
        self._validate_config()
    
    def _load_defaults(self):
        """加载默认配置"""
        self._config.update({
            # Auth defaults
            "ADMIN_USER": "root",
            "ADMIN_PASSWORD": "root123456",
            "REQUIRE_AUTH": True,
            "WHITELIST_DOMAINS": [],
            "WHITELIST_IPS": [],
            
            # Storage defaults
            "STORAGE_TYPE": "local",
            "LOCAL_STORAGE_PATH": "/data/files",
            "LOCAL_STORAGE_DOMAIN": "",
            
            # S3 defaults
            "S3_ACCESS_KEY": "",
            "S3_SECRET_KEY": "",
            "S3_BUCKET_NAME": "",
            "S3_ENDPOINT_URL": "",
            "S3_REGION_NAME": "",
            "S3_SIGN_VERSION": None,
            
            # General defaults
            "CORS_ALLOW_ORIGINS": ["*"],
            "MAX_FILE_SIZE": -1,
            "PDF_MAX_IMAGES": 10,
            
            # Feature flags
            "ENABLE_OCR": False,
            "ENABLE_VISION": True,
            "ENABLE_AZURE_SPEECH": False,
            
            # Azure Speech defaults
            "AZURE_SPEECH_KEY": "",
            "AZURE_SPEECH_REGION": "",
            
            # Response Format Config
            "RESPONSE_CODE_FIELD": "code",
            "RESPONSE_MSG_FIELD": "msg",
            "RESPONSE_SN_FIELD": "sn",
            "RESPONSE_DATA_FIELD": "data",
            
            # Response Data Format Config
            "RESPONSE_URL_FIELD": "url",
            "RESPONSE_FILENAME_FIELD": "filename",
            "RESPONSE_IMAGE_FIELD": "image",
            
            # Response Code Config
            "RESPONSE_SUCCESS_CODE": 0,
            "RESPONSE_ERROR_CODE": 1,
        })
    
    def _load_env(self):
        """从环境变量加载配置"""
        env_mapping = {
            "ADMIN_USER": (str, None),
            "ADMIN_PASSWORD": (str, None),
            "REQUIRE_AUTH": (bool, True),
            "WHITELIST_DOMAINS": (list, []),
            "WHITELIST_IPS": (list, []),
            "STORAGE_TYPE": (str, "local"),
            "LOCAL_STORAGE_PATH": (str, "/data/files"),
            "LOCAL_STORAGE_DOMAIN": (str, ""),
            "S3_ACCESS_KEY": (str, ""),
            "S3_SECRET_KEY": (str, ""),
            "S3_BUCKET_NAME": (str, ""),
            "S3_ENDPOINT_URL": (str, ""),
            "S3_REGION_NAME": (str, ""),
            "S3_SIGN_VERSION": (str, None),
            "CORS_ALLOW_ORIGINS": (list, ["*"]),
            "MAX_FILE_SIZE": (float, -1),
            "PDF_MAX_IMAGES": (int, 10),
            "AZURE_SPEECH_KEY": (str, ""),
            "AZURE_SPEECH_REGION": (str, ""),
        }
        
        for key, (type_, default) in env_mapping.items():
            value = environ.get(key)
            if value is not None:
                if type_ == bool:
                    self._config[key] = value.lower() in ("true", "1", "yes")
                elif type_ == list:
                    self._config[key] = [x.strip() for x in value.split(",") if x.strip()]
                elif type_ == int:
                    self._config[key] = int(value)
                elif type_ == float:
                    self._config[key] = float(value)
                else:
                    self._config[key] = value.strip()
    
    def _load_persistent(self):
        """加载持久化配置"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    stored_config = json.load(f)
                    self._config.update(stored_config)
            except Exception as e:
                print(f"Error loading config file: {e}")
    
    def _validate_config(self):
        """验证配置有效性"""
        # 验证存储配置
        if self._config["STORAGE_TYPE"] == "s3":
            required_s3_keys = ["S3_ACCESS_KEY", "S3_SECRET_KEY", "S3_BUCKET_NAME"]
            missing_keys = [key for key in required_s3_keys if not self._config.get(key)]
            if missing_keys:
                raise ConfigurationError(f"Missing required S3 configuration: {', '.join(missing_keys)}")
        
        # 验证Azure Speech配置
        if self._config.get("ENABLE_AZURE_SPEECH"):
            if not (self._config.get("AZURE_SPEECH_KEY") and self._config.get("AZURE_SPEECH_REGION")):
                raise ConfigurationError("Azure Speech is enabled but missing required configuration")
    
    def save(self):
        """保存配置到文件"""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        self._config[key] = value
        self._validate_config()
    
    @property
    def storage_type(self) -> str:
        return self.get("STORAGE_TYPE", "local")
    
    @property
    def s3_config(self) -> Dict[str, str]:
        if self.storage_type != "s3":
            return {}
        return {
            "access_key": self.get("S3_ACCESS_KEY"),
            "secret_key": self.get("S3_SECRET_KEY"),
            "bucket_name": self.get("S3_BUCKET_NAME"),
            "endpoint_url": self.get("S3_ENDPOINT_URL"),
            "region_name": self.get("S3_REGION_NAME"),
            "sign_version": self.get("S3_SIGN_VERSION"),
        }
    
    @property
    def local_storage_config(self) -> Dict[str, str]:
        return {
            "path": self.get("LOCAL_STORAGE_PATH"),
            "domain": self.get("LOCAL_STORAGE_DOMAIN"),
        }
    
    @property
    def auth_config(self) -> Dict[str, Any]:
        return {
            "admin_user": self.get("ADMIN_USER"),
            "admin_password": self.get("ADMIN_PASSWORD"),
            "require_auth": self.get("REQUIRE_AUTH"),
            "whitelist_domains": self.get("WHITELIST_DOMAINS"),
            "whitelist_ips": self.get("WHITELIST_IPS"),
        }
    
    def is_ip_allowed(self, ip: str) -> bool:
        """检查IP是否在白名单中"""
        whitelist = self.get("WHITELIST_IPS", [])
        if not whitelist:
            return False
        return ip in whitelist or ip.startswith(tuple(whitelist))
    
    def is_domain_allowed(self, domain: str) -> bool:
        """检查域名是否在白名单中"""
        whitelist = self.get("WHITELIST_DOMAINS", [])
        if not whitelist:
            return False
        return domain in whitelist or domain.endswith(tuple(whitelist))

    def format_response(self, success: bool, message: str, data: dict = None) -> dict:
        """Format response according to configuration"""
        return {
            self.get("RESPONSE_CODE_FIELD"): self.get("RESPONSE_SUCCESS_CODE") if success else self.get("RESPONSE_ERROR_CODE"),
            self.get("RESPONSE_MSG_FIELD"): message,
            self.get("RESPONSE_SN_FIELD"): secrets.token_hex(8),
            self.get("RESPONSE_DATA_FIELD"): data or {}
        }

    def format_upload_data(self, url: str = "", filename: str = "", is_image: bool = False) -> dict:
        """Format upload response data according to configuration"""
        return {
            self.get("RESPONSE_URL_FIELD"): url,
            self.get("RESPONSE_FILENAME_FIELD"): filename,
            self.get("RESPONSE_IMAGE_FIELD"): is_image
        }

# 创建全局配置实例
config = Config()

# 导出常用配置
ADMIN_USER = config.get("ADMIN_USER")
ADMIN_PASSWORD = config.get("ADMIN_PASSWORD")
REQUIRE_AUTH = config.get("REQUIRE_AUTH")
STORAGE_TYPE = config.get("STORAGE_TYPE")
MAX_FILE_SIZE = config.get("MAX_FILE_SIZE")
CORS_ALLOW_ORIGINS = config.get("CORS_ALLOW_ORIGINS")
