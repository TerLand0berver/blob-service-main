"""
Configuration module for the Blob Service.
"""
import os
from typing import List, Optional, Dict
import json
import secrets

class Config:
    def __init__(self):
        # Auth settings
        self.ADMIN_USER: str = os.getenv("ADMIN_USER", "admin")
        self.ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD")  
        if not self.ADMIN_PASSWORD:
            raise ValueError("ADMIN_PASSWORD environment variable must be set")
            
        self.REQUIRE_AUTH: bool = os.getenv("REQUIRE_AUTH", "true").lower() == "true"
        self.JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
        if not self.JWT_SECRET_KEY:
            self.JWT_SECRET_KEY = secrets.token_urlsafe(32)
            os.environ["JWT_SECRET_KEY"] = self.JWT_SECRET_KEY
            
        self.JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
        self.TOKEN_EXPIRY: int = int(os.getenv("TOKEN_EXPIRY", "86400"))  # 24 hours
        self.REFRESH_TOKEN_EXPIRY: int = int(os.getenv("REFRESH_TOKEN_EXPIRY", "604800"))  # 7 days
        self.MAX_FAILED_ATTEMPTS: int = int(os.getenv("MAX_FAILED_ATTEMPTS", "5"))
        self.LOCKOUT_DURATION: int = int(os.getenv("LOCKOUT_DURATION", "900"))  # 15 minutes
        self.PASSWORD_MIN_LENGTH: int = int(os.getenv("PASSWORD_MIN_LENGTH", "12"))
        self.PASSWORD_REQUIRE_SPECIAL: bool = os.getenv("PASSWORD_REQUIRE_SPECIAL", "true").lower() == "true"
        self.PASSWORD_REQUIRE_NUMBERS: bool = os.getenv("PASSWORD_REQUIRE_NUMBERS", "true").lower() == "true"
        self.PASSWORD_REQUIRE_UPPERCASE: bool = os.getenv("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true"
        self.PASSWORD_REQUIRE_LOWERCASE: bool = os.getenv("PASSWORD_REQUIRE_LOWERCASE", "true").lower() == "true"
        self.MAX_SESSIONS_PER_USER: int = int(os.getenv("MAX_SESSIONS_PER_USER", "5"))
            
        # Security settings
        self.RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        self.RATE_LIMIT_BURST: int = int(os.getenv("RATE_LIMIT_BURST", "10"))
        self.SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT", "3600"))
        self.ENABLE_AUDIT_LOG: bool = os.getenv("ENABLE_AUDIT_LOG", "true").lower() == "true"
        self.AUDIT_LOG_PATH: str = os.getenv("AUDIT_LOG_PATH", "logs/audit.log")
        self.ENABLE_REQUEST_VALIDATION: bool = os.getenv("ENABLE_REQUEST_VALIDATION", "true").lower() == "true"
        self.ENABLE_RESPONSE_VALIDATION: bool = os.getenv("ENABLE_RESPONSE_VALIDATION", "true").lower() == "true"
        self.ENABLE_CONTENT_SECURITY_POLICY: bool = os.getenv("ENABLE_CONTENT_SECURITY_POLICY", "true").lower() == "true"

        # Content Security Policy settings
        self.CONTENT_SECURITY_POLICY: Dict[str, List[str]] = self._parse_json(os.getenv("CONTENT_SECURITY_POLICY", """{
            "default-src": ["'self'"],
            "script-src": ["'self'"],
            "style-src": ["'self'"],
            "img-src": ["'self'", "data:"],
            "font-src": ["'self'"],
            "connect-src": ["'self'"]
        }"""))

        # Secure headers
        self.SECURE_HEADERS: Dict[str, str] = self._parse_json(os.getenv("SECURE_HEADERS", """{
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }"""))

        # Whitelist settings
        self.WHITELIST_DOMAINS: List[str] = self._parse_list(os.getenv("WHITELIST_DOMAINS", ""))
        self.WHITELIST_IPS: List[str] = self._parse_list(os.getenv("WHITELIST_IPS", ""))
        
        # CORS settings
        self.CORS_ALLOW_ORIGINS: List[str] = self._parse_list(
            os.getenv("CORS_ALLOW_ORIGINS", ""),  
            default=[]  
        )
        if not self.CORS_ALLOW_ORIGINS:
            raise ValueError("CORS_ALLOW_ORIGINS environment variable must be set")
        
        # File settings
        self.MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  
        self.PDF_MAX_IMAGES: int = int(os.getenv("PDF_MAX_IMAGES", "20"))
        
        # Storage settings
        self.STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "local")
        self.LOCAL_STORAGE_DOMAIN: Optional[str] = os.getenv("LOCAL_STORAGE_DOMAIN")
        
        # API settings
        self.FILE_API_ENDPOINT: Optional[str] = os.getenv("FILE_API_ENDPOINT")
        self.FILE_API_KEY: Optional[str] = os.getenv("FILE_API_KEY")
        
        # OCR settings
        self.OCR_ENDPOINT: Optional[str] = os.getenv("OCR_ENDPOINT")
        self.OCR_SKIP_MODELS: List[str] = self._parse_list(os.getenv("OCR_SKIP_MODELS", ""))
        self.OCR_SPEC_MODELS: List[str] = self._parse_list(os.getenv("OCR_SPEC_MODELS", ""))

        # Text extraction settings
        self.TEXT_EXTRACTION = self._parse_json(os.getenv("TEXT_EXTRACTION", """{
            "pdf": {
                "max_pages": 1000
            },
            "spreadsheet": {
                "max_rows": 10000,
                "max_cols": 1000,
                "supported_formats": ["xlsx", "xls", "csv", "tsv"]
            },
            "document": {
                "supported_formats": ["doc", "docx", "txt", "rtf"],
                "max_size_mb": 50
            },
            "code": {
                "supported_formats": ["py", "js", "java", "cpp", "c", "cs", "php", "rb", "go", "sql"],
                "max_size_mb": 10
            },
            "encodings": ["utf-8", "ascii", "iso-8859-1", "cp1252", "utf-16"],
            "general": {
                "timeout_seconds": 300,
                "fallback_encoding": "utf-8"
            }
        }"""))

        # Response Format settings
        self.RESPONSE_FORMAT = self._parse_json(os.getenv("RESPONSE_FORMAT", """{
            "markdown": {
                "link": "[ {text} ]( {url} )",
                "image": "![ {text} ]( {url} )",
                "heading": "### {text}",
                "list_item": "- {text}",
                "quote": "> {text}",
                "code": "`{text}`",
                "bold": "**{text}**",
                "newline": "\\n"
            },
            "templates": {
                "file_link": "[ {filename} ]( {url} ) ({size})",
                "file_text": "{content}",
                "image_link": "![ {filename} ]( {url} )",
                "image_text": "{ocr_text}",
                "list": "{items}"
            }
        }"""))

        # File type mappings with descriptions
        self.FILE_TYPE_MAPPINGS = self._parse_json(os.getenv("FILE_TYPE_MAPPINGS", """{
            "image": {
                "extensions": ["jpg", "jpeg", "png", "gif", "bmp", "webp", "tiff", "svg", "ico"],
                "icon": "",
                "description": "Image",
                "processors": ["ocr", "vision"]
            },
            "document": {
                "extensions": ["pdf", "doc", "docx", "txt", "rtf", "odt", "md", "rst", "tex"],
                "icon": "",
                "description": "Document",
                "processors": ["text", "ocr"]
            },
            "code": {
                "extensions": [
                    "py", "pyi", "pyx", "pyd", "ipynb",  
                    "js", "jsx", "ts", "tsx", "mjs", "cjs",  
                    "java", "class", "jar",  
                    "c", "cpp", "cxx", "cc", "h", "hpp", "hxx",  
                    "cs", "csx", "vb",  
                    "go", "mod",  
                    "rs", "rlib",  
                    "php", "phtml", "php3", "php4", "php5", "php7",  
                    "rb", "rbw", "rake", "gemspec",  
                    "swift",  
                    "kt", "kts",  
                    "scala", "sc",  
                    "pl", "pm", "t",  
                    "sh", "bash", "zsh", "fish",  
                    "sql", "mysql", "pgsql",  
                    "r", "rmd",  
                    "lua",  
                    "m", "mm",  
                    "dart",  
                    "ex", "exs",  
                    "elm",  
                    "erl", "hrl",  
                    "fs", "fsi", "fsx", "fsscript",  
                    "hs", "lhs",  
                    "html", "htm", "xhtml", "shtml",  
                    "css", "scss", "sass", "less", "styl",  
                    "xml", "xsl", "xslt", "wsdl", "yml", "yaml", "json", "toml"  
                ],
                "icon": "",
                "description": "Code",
                "processors": ["text"]
            },
            "spreadsheet": {
                "extensions": ["xls", "xlsx", "csv", "tsv", "ods"],
                "icon": "",
                "description": "Spreadsheet",
                "processors": ["text"]
            },
            "presentation": {
                "extensions": ["ppt", "pptx", "odp", "key"],
                "icon": "",
                "description": "Presentation",
                "processors": ["text", "ocr"]
            },
            "audio": {
                "extensions": ["mp3", "wav", "ogg", "m4a", "flac", "aac", "wma", "aiff", "alac"],
                "icon": "",
                "description": "Audio",
                "processors": []
            },
            "video": {
                "extensions": ["mp4", "avi", "mov", "wmv", "flv", "mkv", "webm", "m4v", "mpeg", "3gp"],
                "icon": "",
                "description": "Video",
                "processors": []
            },
            "archive": {
                "extensions": ["zip", "rar", "7z", "tar", "gz", "bz2", "xz", "iso"],
                "icon": "",
                "description": "Archive",
                "processors": []
            }
        }"""))

        # File processing settings
        self.FILE_PROCESSING = self._parse_json(os.getenv("FILE_PROCESSING", """{
            "save_all": {
                "link_only": true,
                "extract_images": true
            },
            "default": {
                "extract_text_types": ["document", "code", "spreadsheet"],
                "ignore_types": ["video", "audio", "archive"]
            }
        }"""))

    def _parse_list(self, value: Optional[str], default: List[str] = None) -> List[str]:
        """Parse comma-separated string into list"""
        if not value:
            return default if default is not None else []
        return [x.strip() for x in value.split(",") if x.strip()]
        
    def _parse_json(self, value: Optional[str], default: Dict = None) -> Dict:
        """Parse JSON string into dictionary"""
        if not value:
            return default if default is not None else {}
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default if default is not None else {}

    def save_config_file(self, filepath: str = ".env"):
        """Save current configuration to file"""
        config_dict = {
            "ADMIN_USER": self.ADMIN_USER,
            "ADMIN_PASSWORD": self.ADMIN_PASSWORD,
            "REQUIRE_AUTH": str(self.REQUIRE_AUTH).lower(),
            "JWT_SECRET_KEY": self.JWT_SECRET_KEY,
            "WHITELIST_DOMAINS": ",".join(self.WHITELIST_DOMAINS),
            "WHITELIST_IPS": ",".join(self.WHITELIST_IPS),
            "CORS_ALLOW_ORIGINS": ",".join(self.CORS_ALLOW_ORIGINS),
            "MAX_FILE_SIZE": str(self.MAX_FILE_SIZE),
            "PDF_MAX_IMAGES": str(self.PDF_MAX_IMAGES),
            "STORAGE_TYPE": self.STORAGE_TYPE,
            "LOCAL_STORAGE_DOMAIN": self.LOCAL_STORAGE_DOMAIN or "",
            "FILE_API_ENDPOINT": self.FILE_API_ENDPOINT or "",
            "FILE_API_KEY": self.FILE_API_KEY or "",
            "OCR_ENDPOINT": self.OCR_ENDPOINT or "",
            "OCR_SKIP_MODELS": ",".join(self.OCR_SKIP_MODELS),
            "OCR_SPEC_MODELS": ",".join(self.OCR_SPEC_MODELS),
            "RESPONSE_FORMAT": json.dumps(self.RESPONSE_FORMAT),
            "TEXT_EXTRACTION": json.dumps(self.TEXT_EXTRACTION),
            "FILE_PROCESSING": json.dumps(self.FILE_PROCESSING),
            "FILE_TYPE_MAPPINGS": json.dumps(self.FILE_TYPE_MAPPINGS),
            "RATE_LIMIT_PER_MINUTE": str(self.RATE_LIMIT_PER_MINUTE),
            "RATE_LIMIT_BURST": str(self.RATE_LIMIT_BURST),
            "SESSION_TIMEOUT": str(self.SESSION_TIMEOUT),
            "JWT_ALGORITHM": self.JWT_ALGORITHM,
            "TOKEN_EXPIRY": str(self.TOKEN_EXPIRY),
            "REFRESH_TOKEN_EXPIRY": str(self.REFRESH_TOKEN_EXPIRY),
            "MAX_FAILED_ATTEMPTS": str(self.MAX_FAILED_ATTEMPTS),
            "LOCKOUT_DURATION": str(self.LOCKOUT_DURATION),
            "PASSWORD_MIN_LENGTH": str(self.PASSWORD_MIN_LENGTH),
            "PASSWORD_REQUIRE_SPECIAL": str(self.PASSWORD_REQUIRE_SPECIAL).lower(),
            "PASSWORD_REQUIRE_NUMBERS": str(self.PASSWORD_REQUIRE_NUMBERS).lower(),
            "PASSWORD_REQUIRE_UPPERCASE": str(self.PASSWORD_REQUIRE_UPPERCASE).lower(),
            "PASSWORD_REQUIRE_LOWERCASE": str(self.PASSWORD_REQUIRE_LOWERCASE).lower(),
            "MAX_SESSIONS_PER_USER": str(self.MAX_SESSIONS_PER_USER),
            "ENABLE_AUDIT_LOG": str(self.ENABLE_AUDIT_LOG).lower(),
            "AUDIT_LOG_PATH": self.AUDIT_LOG_PATH,
            "ENABLE_REQUEST_VALIDATION": str(self.ENABLE_REQUEST_VALIDATION).lower(),
            "ENABLE_RESPONSE_VALIDATION": str(self.ENABLE_RESPONSE_VALIDATION).lower(),
            "ENABLE_CONTENT_SECURITY_POLICY": str(self.ENABLE_CONTENT_SECURITY_POLICY).lower(),
            "CONTENT_SECURITY_POLICY": json.dumps(self.CONTENT_SECURITY_POLICY),
            "SECURE_HEADERS": json.dumps(self.SECURE_HEADERS),
        }
        
        with open(filepath, "w") as f:
            for key, value in config_dict.items():
                f.write(f"{key}={value}\n")

# Create global config instance
config = Config()
