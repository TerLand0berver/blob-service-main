"""
Configuration module.
"""
from .models import (
    AppConfig,
    AuthConfig,
    StorageConfig,
    ResponseConfig,
    FeatureConfig,
    AzureConfig,
    StorageType,
    ResponseFormat,
)
from .manager import ConfigManager

# Create global config manager instance
config_manager = ConfigManager()

# Export for convenience
config = config_manager.get_config

__all__ = [
    'AppConfig',
    'AuthConfig',
    'StorageConfig',
    'ResponseConfig',
    'FeatureConfig',
    'AzureConfig',
    'StorageType',
    'ResponseFormat',
    'ConfigManager',
    'config_manager',
    'config',
]
