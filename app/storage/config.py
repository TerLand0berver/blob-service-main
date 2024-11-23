"""
Storage configuration module.
Provides unified configuration management for all storage backends.
"""
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from urllib.parse import urlparse, ParseResult

@dataclass
class StorageCredentials:
    """Storage credentials configuration."""
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    access_token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

@dataclass
class StorageEndpoint:
    """Storage endpoint configuration."""
    url: str
    path: Optional[str] = None
    scheme: Optional[str] = None
    verify_ssl: bool = True
    timeout: int = 30
    
    @classmethod
    def from_url(cls, url: str, **kwargs) -> 'StorageEndpoint':
        """Create endpoint from URL string.
        
        Args:
            url: Endpoint URL
            **kwargs: Additional endpoint options
        
        Returns:
            StorageEndpoint instance
        """
        parsed: ParseResult = urlparse(url)
        return cls(
            url=url,
            path=parsed.path or kwargs.get('path'),
            scheme=parsed.scheme or kwargs.get('scheme'),
            verify_ssl=kwargs.get('verify_ssl', True),
            timeout=kwargs.get('timeout', 30)
        )

@dataclass
class StorageConfig:
    """Unified storage configuration."""
    backend: str
    endpoint: StorageEndpoint
    credentials: Optional[StorageCredentials] = None
    bucket: Optional[str] = None
    root_dir: Optional[str] = None
    max_retries: int = 3
    retry_delay: int = 1
    chunk_size: int = 8192
    options: Dict[str, Any] = None
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'StorageConfig':
        """Create config from dictionary.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            StorageConfig instance
        """
        endpoint = StorageEndpoint.from_url(
            config.get('url', ''),
            **config.get('endpoint', {})
        )
        
        credentials = StorageCredentials(
            **config.get('credentials', {})
        )
        
        return cls(
            backend=config['backend'],
            endpoint=endpoint,
            credentials=credentials,
            bucket=config.get('bucket'),
            root_dir=config.get('root_dir'),
            max_retries=config.get('max_retries', 3),
            retry_delay=config.get('retry_delay', 1),
            chunk_size=config.get('chunk_size', 8192),
            options=config.get('options', {})
        )

def create_storage_config(
    backend: str,
    url: str,
    **kwargs
) -> StorageConfig:
    """Create storage configuration.
    
    Args:
        backend: Storage backend type
        url: Storage endpoint URL
        **kwargs: Additional configuration options
    
    Returns:
        StorageConfig instance
    """
    config = {
        'backend': backend,
        'url': url,
        **kwargs
    }
    return StorageConfig.from_dict(config)

# Example configurations
LOCAL_CONFIG = {
    'backend': 'local',
    'url': 'file:///storage',
    'root_dir': '/storage'
}

S3_CONFIG = {
    'backend': 's3',
    'url': 'https://s3.amazonaws.com',
    'credentials': {
        'api_key': 'access_key',
        'api_secret': 'secret_key'
    },
    'bucket': 'my-bucket'
}

ALIST_CONFIG = {
    'backend': 'alist',
    'url': 'https://alist.example.com',
    'credentials': {
        'username': 'user',
        'password': 'pass'
    },
    'endpoint': {
        'verify_ssl': True,
        'timeout': 30
    }
}
