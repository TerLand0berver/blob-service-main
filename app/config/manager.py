"""
Configuration manager.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from .models import AppConfig
from ..core.errors import ConfigError

class ConfigManager:
    """Configuration manager."""
    
    def __init__(self, config_dir: str = "/data"):
        """Initialize config manager.
        
        Args:
            config_dir: Configuration directory path
        """
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.json"
        self._config: Optional[AppConfig] = None
        
    def load(self) -> AppConfig:
        """Load configuration from all sources.
        
        Returns:
            AppConfig instance
        
        Raises:
            ConfigError: If configuration is invalid
        """
        # Load config in order: defaults -> env -> file
        config_data = {}
        
        # 1. Load environment variables
        config_data.update(self._load_from_env())
        
        # 2. Load from file if exists
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    file_data = json.load(f)
                config_data.update(file_data)
            except Exception as e:
                raise ConfigError(f"Failed to load config file: {e}")
        
        # 3. Create config instance
        try:
            self._config = AppConfig.from_dict(config_data)
        except Exception as e:
            raise ConfigError(f"Invalid configuration: {e}")
            
        return self._config
    
    def save(self) -> None:
        """Save current configuration to file.
        
        Raises:
            ConfigError: If saving fails
        """
        if not self._config:
            raise ConfigError("No configuration loaded")
            
        # Create config directory if needed
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Convert config to dict
            config_data = self._config_to_dict(self._config)
            
            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            raise ConfigError(f"Failed to save config: {e}")
    
    def get_config(self) -> AppConfig:
        """Get current configuration.
        
        Returns:
            AppConfig instance
            
        Raises:
            ConfigError: If no configuration is loaded
        """
        if not self._config:
            raise ConfigError("No configuration loaded")
        return self._config
    
    def update(self, data: Dict[str, Any]) -> AppConfig:
        """Update configuration with new data.
        
        Args:
            data: New configuration data
            
        Returns:
            Updated AppConfig instance
            
        Raises:
            ConfigError: If update fails
        """
        if not self._config:
            raise ConfigError("No configuration loaded")
            
        try:
            # Merge new data with existing config
            config_dict = self._config_to_dict(self._config)
            config_dict.update(data)
            
            # Create new config instance
            self._config = AppConfig.from_dict(config_dict)
            return self._config
        except Exception as e:
            raise ConfigError(f"Failed to update config: {e}")
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables.
        
        Returns:
            Dictionary of configuration values from environment
        """
        config = {}
        
        # Auth config
        if admin_user := os.environ.get('ADMIN_USER'):
            config.setdefault('auth', {})['admin_user'] = admin_user
        if admin_pass := os.environ.get('ADMIN_PASSWORD'):
            config.setdefault('auth', {})['admin_password'] = admin_pass
        if require_auth := os.environ.get('REQUIRE_AUTH'):
            config.setdefault('auth', {})['require_auth'] = require_auth.lower() == 'true'
            
        # Storage config
        if storage_type := os.environ.get('STORAGE_TYPE'):
            config.setdefault('storage', {})['type'] = storage_type
        if storage_path := os.environ.get('LOCAL_STORAGE_PATH'):
            config.setdefault('storage', {})['local_path'] = storage_path
        if storage_domain := os.environ.get('LOCAL_STORAGE_DOMAIN'):
            config.setdefault('storage', {})['local_domain'] = storage_domain
            
        # S3 config
        if s3_key := os.environ.get('S3_ACCESS_KEY'):
            config.setdefault('storage', {})['s3_access_key'] = s3_key
        if s3_secret := os.environ.get('S3_SECRET_KEY'):
            config.setdefault('storage', {})['s3_secret_key'] = s3_secret
        if s3_bucket := os.environ.get('S3_BUCKET_NAME'):
            config.setdefault('storage', {})['s3_bucket'] = s3_bucket
        if s3_endpoint := os.environ.get('S3_ENDPOINT_URL'):
            config.setdefault('storage', {})['s3_endpoint'] = s3_endpoint
        if s3_region := os.environ.get('S3_REGION_NAME'):
            config.setdefault('storage', {})['s3_region'] = s3_region
            
        # Feature flags
        if enable_ocr := os.environ.get('ENABLE_OCR'):
            config.setdefault('features', {})['enable_ocr'] = enable_ocr.lower() == 'true'
        if enable_vision := os.environ.get('ENABLE_VISION'):
            config.setdefault('features', {})['enable_vision'] = enable_vision.lower() == 'true'
        if enable_speech := os.environ.get('ENABLE_SPEECH'):
            config.setdefault('features', {})['enable_speech'] = enable_speech.lower() == 'true'
            
        # Azure config
        if speech_key := os.environ.get('AZURE_SPEECH_KEY'):
            config.setdefault('azure', {})['speech_key'] = speech_key
        if speech_region := os.environ.get('AZURE_SPEECH_REGION'):
            config.setdefault('azure', {})['speech_region'] = speech_region
            
        return config
    
    def _config_to_dict(self, config: AppConfig) -> Dict[str, Any]:
        """Convert AppConfig to dictionary.
        
        Args:
            config: AppConfig instance
            
        Returns:
            Dictionary representation of config
        """
        return {
            'auth': {
                'admin_user': config.auth.admin_user,
                'admin_password': config.auth.admin_password,
                'require_auth': config.auth.require_auth,
                'whitelist_domains': config.auth.whitelist_domains,
                'whitelist_ips': config.auth.whitelist_ips,
                'jwt_secret': config.auth.jwt_secret,
                'jwt_expires': config.auth.jwt_expires,
            },
            'storage': {
                'type': config.storage.type.value,
                'local_path': config.storage.local_path,
                'local_domain': config.storage.local_domain,
                's3_access_key': config.storage.s3_access_key,
                's3_secret_key': config.storage.s3_secret_key,
                's3_bucket': config.storage.s3_bucket,
                's3_endpoint': config.storage.s3_endpoint,
                's3_region': config.storage.s3_region,
                's3_sign_version': config.storage.s3_sign_version,
                'max_file_size': config.storage.max_file_size,
            },
            'response': {
                'format': config.response.format.value,
                'code_field': config.response.code_field,
                'message_field': config.response.message_field,
                'data_field': config.response.data_field,
                'success_code': config.response.success_code,
                'error_code': config.response.error_code,
                'url_field': config.response.url_field,
                'filename_field': config.response.filename_field,
                'image_field': config.response.image_field,
            },
            'features': {
                'enable_ocr': config.features.enable_ocr,
                'enable_vision': config.features.enable_vision,
                'enable_speech': config.features.enable_speech,
                'pdf_max_images': config.features.pdf_max_images,
            },
            'azure': {
                'speech_key': config.azure.speech_key,
                'speech_region': config.azure.speech_region,
            },
            'cors_origins': config.cors_origins,
            'debug': config.debug,
        }
