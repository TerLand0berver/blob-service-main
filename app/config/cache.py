"""
Cache configuration settings.
"""
from typing import Dict, Any

# Default cache settings
DEFAULT_CACHE_CONFIG: Dict[str, Any] = {
    # Cache directory path (relative to app root)
    'cache_dir': 'cache',
    
    # Maximum age of cached items in seconds (default: 1 hour)
    'max_age': 3600,
    
    # Maximum size of cache in bytes (default: 1GB)
    'max_size': 1024 * 1024 * 1024,
    
    # Enable/disable caching
    'enabled': True,
    
    # Cache backend ('disk' or 'redis')
    'backend': 'disk',
    
    # Redis configuration (if using redis backend)
    'redis': {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'password': None,
        'prefix': 'blob_service_cache:'
    },
    
    # File types to cache (empty list means cache all)
    'cache_types': [],
    
    # Maximum file size to cache in bytes (default: 100MB)
    'max_file_size': 100 * 1024 * 1024,
    
    # Cache compression level (0-9, 0=disabled)
    'compression_level': 6,
    
    # Cache statistics collection
    'collect_stats': True,
    
    # Cache cleanup interval in seconds
    'cleanup_interval': 3600,
    
    # Cache hit threshold for keeping items (0.0-1.0)
    'hit_threshold': 0.1,
    
    # Cache memory buffer size in bytes (default: 64MB)
    'buffer_size': 64 * 1024 * 1024
}
