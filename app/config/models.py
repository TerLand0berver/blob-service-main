"""
Configuration models.
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

class StorageType(str, Enum):
    """Storage backend types."""
    LOCAL = "local"
    S3 = "s3"
    ALIST = "alist"

class ResponseFormat(str, Enum):
    """Response format types."""
    STANDARD = "standard"
    LEGACY = "legacy"
    CUSTOM = "custom"

@dataclass
class AuthConfig:
    """Authentication configuration."""
    admin_user: str = "root"
    admin_password: str = "root123456"
    require_auth: bool = True
    whitelist_domains: List[str] = field(default_factory=list)
    whitelist_ips: List[str] = field(default_factory=list)
    jwt_secret: Optional[str] = None
    jwt_expires: int = 3600

@dataclass
class StorageConfig:
    """Storage configuration."""
    type: StorageType = StorageType.LOCAL
    local_path: str = "/data/files"
    local_domain: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket: str = ""
    s3_endpoint: str = ""
    s3_region: str = ""
    s3_sign_version: Optional[str] = None
    max_file_size: int = -1

@dataclass
class ResponseConfig:
    """Response format configuration."""
    format: ResponseFormat = ResponseFormat.STANDARD
    code_field: str = "code"
    message_field: str = "msg"
    data_field: str = "data"
    success_code: int = 0
    error_code: int = 1
    url_field: str = "url"
    filename_field: str = "filename"
    image_field: str = "image"

@dataclass
class FeatureConfig:
    """Feature flags configuration."""
    enable_ocr: bool = False
    enable_vision: bool = True
    enable_speech: bool = False
    pdf_max_images: int = 10

@dataclass
class AzureConfig:
    """Azure services configuration."""
    speech_key: str = ""
    speech_region: str = ""

@dataclass
class AppConfig:
    """Application configuration."""
    auth: AuthConfig = field(default_factory=AuthConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    response: ResponseConfig = field(default_factory=ResponseConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    azure: AzureConfig = field(default_factory=AzureConfig)
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    debug: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """Create config from dictionary.
        
        Args:
            data: Configuration dictionary
            
        Returns:
            AppConfig instance
        """
        auth_data = data.get('auth', {})
        storage_data = data.get('storage', {})
        response_data = data.get('response', {})
        features_data = data.get('features', {})
        azure_data = data.get('azure', {})
        
        return cls(
            auth=AuthConfig(**auth_data),
            storage=StorageConfig(
                type=StorageType(storage_data.get('type', 'local')),
                **{k: v for k, v in storage_data.items() if k != 'type'}
            ),
            response=ResponseConfig(
                format=ResponseFormat(response_data.get('format', 'standard')),
                **{k: v for k, v in response_data.items() if k != 'format'}
            ),
            features=FeatureConfig(**features_data),
            azure=AzureConfig(**azure_data),
            cors_origins=data.get('cors_origins', ["*"]),
            debug=data.get('debug', False)
        )
