"""
Core configuration management.
"""
from typing import Dict, Any, Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field
import json
import os
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DynamicConfig(BaseSettings):
    """Dynamic configuration that can be updated at runtime"""
    
    # Storage settings
    storage_type: str = Field(default="local", env="STORAGE_TYPE")
    storage_path: str = Field(default="./data", env="STORAGE_PATH")
    s3_bucket: Optional[str] = Field(None, env="S3_BUCKET")
    s3_endpoint: Optional[str] = Field(None, env="S3_ENDPOINT")
    
    # Processing settings
    max_file_size: int = Field(default=10*1024*1024, env="MAX_FILE_SIZE")  # 10MB
    allowed_extensions: List[str] = Field(
        default=["jpg", "png", "pdf", "doc", "docx"],
        env="ALLOWED_EXTENSIONS"
    )
    extract_text_enabled: bool = Field(default=True, env="EXTRACT_TEXT_ENABLED")
    ocr_enabled: bool = Field(default=False, env="OCR_ENABLED")
    
    # Security settings
    whitelist_ips: List[str] = Field(default=[], env="WHITELIST_IPS")
    whitelist_domains: List[str] = Field(default=[], env="WHITELIST_DOMAINS")
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # Response settings
    response_format: Dict[str, Any] = Field(
        default={
            "success_template": "{message}",
            "error_template": "Error: {message}",
            "file_template": "File: {name} ({size})"
        },
        env="RESPONSE_FORMAT"
    )
    
    class Config:
        env_file = ".env"
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_dynamic_config()
        
    def _load_dynamic_config(self):
        """Load dynamic configuration from file"""
        config_path = Path("config/dynamic.json")
        try:
            if config_path.exists():
                with open(config_path) as f:
                    dynamic_config = json.load(f)
                    for key, value in dynamic_config.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
        except Exception as e:
            logger.error(f"Error loading dynamic config: {e}")
            
    async def update(self, updates: Dict[str, Any]) -> bool:
        """Update dynamic configuration
        
        Args:
            updates: Dictionary of configuration updates
            
        Returns:
            bool: True if update successful
        """
        try:
            # Validate updates
            for key, value in updates.items():
                if not hasattr(self, key):
                    raise ValueError(f"Invalid configuration key: {key}")
                    
            # Apply updates
            for key, value in updates.items():
                setattr(self, key, value)
                
            # Save to file
            await self._save_dynamic_config()
            return True
        except Exception as e:
            logger.error(f"Error updating config: {e}")
            return False
            
    async def _save_dynamic_config(self):
        """Save dynamic configuration to file"""
        config_path = Path("config/dynamic.json")
        config_path.parent.mkdir(exist_ok=True)
        
        # Get dynamic config as dict
        config_dict = {
            key: getattr(self, key)
            for key in self.__fields__
            if not key.startswith("_")
        }
        
        # Add metadata
        config_dict["_updated_at"] = datetime.utcnow().isoformat()
        
        # Save to file
        with open(config_path, "w") as f:
            json.dump(config_dict, f, indent=2)
            
    def get_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration"""
        return {
            "type": self.storage_type,
            "path": self.storage_path,
            "s3_bucket": self.s3_bucket,
            "s3_endpoint": self.s3_endpoint
        }
        
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return {
            "whitelist_ips": self.whitelist_ips,
            "whitelist_domains": self.whitelist_domains,
            "rate_limit_enabled": self.rate_limit_enabled,
            "rate_limit_per_minute": self.rate_limit_per_minute
        }
        
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration"""
        return {
            "max_file_size": self.max_file_size,
            "allowed_extensions": self.allowed_extensions,
            "extract_text_enabled": self.extract_text_enabled,
            "ocr_enabled": self.ocr_enabled
        }

# Create global config instance
config = DynamicConfig()
