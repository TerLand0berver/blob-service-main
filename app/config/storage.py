"""
Storage configuration settings.
"""
from typing import Dict, Any, List, Optional

# Default storage settings
DEFAULT_STORAGE_CONFIG: Dict[str, Any] = {
    # Storage backend type ('local', 's3', 'oss', 'cos', 'azure', 'gcs', 'alist', etc.)
    'backend': 'local',
    
    # Enable/disable storage
    'enabled': True,
    
    # Local storage settings
    'local': {
        'root_dir': 'storage',
        'max_size': 1024 * 1024 * 1024 * 1024,  # 1TB
        'create_dirs': True
    },
    
    # S3 compatible storage settings
    's3': {
        'endpoint': 'https://s3.amazonaws.com',
        'access_key': '',
        'secret_key': '',
        'bucket': '',
        'region': 'us-east-1',
        'path_style': False,
        'ssl_verify': True
    },
    
    # Alibaba Cloud OSS settings
    'oss': {
        'endpoint': '',
        'access_key': '',
        'secret_key': '',
        'bucket': '',
        'internal': False,
        'path_style': False
    },
    
    # Tencent Cloud COS settings
    'cos': {
        'endpoint': '',
        'secret_id': '',
        'secret_key': '',
        'bucket': '',
        'region': '',
        'scheme': 'https'
    },
    
    # Azure Blob Storage settings
    'azure': {
        'connection_string': '',
        'container': '',
        'sas_token': ''
    },
    
    # Google Cloud Storage settings
    'gcs': {
        'project_id': '',
        'credentials_file': '',
        'bucket': ''
    },
    
    # AList settings
    'alist': {
        'endpoint': 'http://localhost:5244',
        'username': 'admin',
        'password': '',
        'token': '',
        'root_folder': '/'
    },
    
    # WebDAV settings
    'webdav': {
        'endpoint': '',
        'username': '',
        'password': '',
        'root_path': '/'
    },
    
    # FTP settings
    'ftp': {
        'host': '',
        'port': 21,
        'username': '',
        'password': '',
        'root_path': '/',
        'passive_mode': True,
        'tls': False
    },
    
    # SFTP settings
    'sftp': {
        'host': '',
        'port': 22,
        'username': '',
        'password': '',
        'key_file': '',
        'root_path': '/'
    },
    
    # Common settings
    'timeout': 30,
    'max_retries': 3,
    'retry_delay': 1,
    'chunk_size': 8 * 1024 * 1024,  # 8MB
    'multipart_threshold': 100 * 1024 * 1024,  # 100MB
    'multipart_chunksize': 8 * 1024 * 1024,  # 8MB
    
    # Cache settings
    'cache': {
        'enabled': True,
        'ttl': 3600,  # 1 hour
        'max_size': 1024 * 1024 * 1024,  # 1GB
        'dir': '.storage_cache'
    },
    
    # Encryption settings
    'encryption': {
        'enabled': False,
        'algorithm': 'AES-256-GCM',
        'key': '',
        'key_file': ''
    },
    
    # Compression settings
    'compression': {
        'enabled': False,
        'algorithm': 'zstd',
        'level': 3
    },
    
    # Lifecycle settings
    'lifecycle': {
        'enabled': False,
        'rules': [
            {
                'prefix': '',
                'days': 30,
                'action': 'delete'
            }
        ]
    },
    
    # Versioning settings
    'versioning': {
        'enabled': False,
        'max_versions': 10
    },
    
    # Logging settings
    'logging': {
        'enabled': True,
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    }
}

# Storage backend types
STORAGE_BACKENDS = {
    'local': 'app.storage.local.LocalStorage',
    's3': 'app.storage.s3.S3Storage',
    'oss': 'app.storage.oss.OSSStorage',
    'cos': 'app.storage.cos.COSStorage',
    'azure': 'app.storage.azure.AzureStorage',
    'gcs': 'app.storage.gcs.GCSStorage',
    'alist': 'app.storage.alist.AListStorage',
    'webdav': 'app.storage.webdav.WebDAVStorage',
    'ftp': 'app.storage.ftp.FTPStorage',
    'sftp': 'app.storage.sftp.SFTPStorage'
}

# Storage error codes
class StorageErrorCode:
    SUCCESS = 0
    UNKNOWN_ERROR = 1
    INVALID_CONFIG = 2
    CONNECTION_ERROR = 3
    AUTHENTICATION_ERROR = 4
    PERMISSION_ERROR = 5
    NOT_FOUND = 6
    ALREADY_EXISTS = 7
    QUOTA_EXCEEDED = 8
    INVALID_OPERATION = 9
    TIMEOUT = 10
    NETWORK_ERROR = 11
    ENCRYPTION_ERROR = 12
    COMPRESSION_ERROR = 13
    INTEGRITY_ERROR = 14

# Storage error messages
STORAGE_ERROR_MESSAGES = {
    StorageErrorCode.SUCCESS: 'Success',
    StorageErrorCode.UNKNOWN_ERROR: 'Unknown error occurred',
    StorageErrorCode.INVALID_CONFIG: 'Invalid storage configuration',
    StorageErrorCode.CONNECTION_ERROR: 'Failed to connect to storage backend',
    StorageErrorCode.AUTHENTICATION_ERROR: 'Authentication failed',
    StorageErrorCode.PERMISSION_ERROR: 'Permission denied',
    StorageErrorCode.NOT_FOUND: 'Resource not found',
    StorageErrorCode.ALREADY_EXISTS: 'Resource already exists',
    StorageErrorCode.QUOTA_EXCEEDED: 'Storage quota exceeded',
    StorageErrorCode.INVALID_OPERATION: 'Invalid operation',
    StorageErrorCode.TIMEOUT: 'Operation timed out',
    StorageErrorCode.NETWORK_ERROR: 'Network error occurred',
    StorageErrorCode.ENCRYPTION_ERROR: 'Encryption error occurred',
    StorageErrorCode.COMPRESSION_ERROR: 'Compression error occurred',
    StorageErrorCode.INTEGRITY_ERROR: 'Data integrity check failed'
}

class StorageError(Exception):
    """Storage error class."""
    
    def __init__(self, code: int, message: Optional[str] = None):
        self.code = code
        self.message = message or STORAGE_ERROR_MESSAGES.get(code, 'Unknown error')
        super().__init__(self.message)

def validate_storage_config(config: Dict[str, Any]) -> None:
    """Validate storage configuration.
    
    Args:
        config: Storage configuration dictionary
        
    Raises:
        StorageError: If configuration is invalid
    """
    try:
        # Check required fields
        if 'backend' not in config:
            raise StorageError(StorageErrorCode.INVALID_CONFIG, 'Missing backend type')
        
        # Check backend type
        if config['backend'] not in STORAGE_BACKENDS:
            raise StorageError(
                StorageErrorCode.INVALID_CONFIG,
                f"Unsupported backend type: {config['backend']}"
            )
        
        # Validate backend-specific configuration
        backend_config = config.get(config['backend'], {})
        if not backend_config:
            raise StorageError(
                StorageErrorCode.INVALID_CONFIG,
                f"Missing configuration for backend: {config['backend']}"
            )
        
        # Validate common settings
        numeric_fields = {
            'timeout': (0, None),
            'max_retries': (0, None),
            'retry_delay': (0, None),
            'chunk_size': (0, None),
            'multipart_threshold': (0, None),
            'multipart_chunksize': (0, None)
        }
        
        for field, (min_val, max_val) in numeric_fields.items():
            if field in config:
                value = config[field]
                if not isinstance(value, (int, float)):
                    raise StorageError(
                        StorageErrorCode.INVALID_CONFIG,
                        f"Invalid type for {field}: {type(value)}"
                    )
                if min_val is not None and value < min_val:
                    raise StorageError(
                        StorageErrorCode.INVALID_CONFIG,
                        f"{field} must be >= {min_val}"
                    )
                if max_val is not None and value > max_val:
                    raise StorageError(
                        StorageErrorCode.INVALID_CONFIG,
                        f"{field} must be <= {max_val}"
                    )
        
    except StorageError:
        raise
    except Exception as e:
        raise StorageError(
            StorageErrorCode.INVALID_CONFIG,
            f"Configuration validation failed: {str(e)}"
        )
