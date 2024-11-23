"""
Cache configuration utilities.
"""
import os
from typing import Dict, Any, Optional
import yaml

from ..config.cache import DEFAULT_CACHE_CONFIG

class CacheConfigError(Exception):
    """Cache configuration error."""
    pass

def load_cache_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load cache configuration from file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        CacheConfigError: If configuration is invalid
    """
    try:
        # Load configuration file
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        else:
            config = {}
        
        # Merge with defaults
        merged_config = DEFAULT_CACHE_CONFIG.copy()
        merged_config.update(config)
        
        # Validate configuration
        validate_cache_config(merged_config)
        
        return merged_config
        
    except Exception as e:
        raise CacheConfigError(f"Failed to load cache configuration: {e}")

def validate_cache_config(config: Dict[str, Any]):
    """Validate cache configuration.
    
    Args:
        config: Configuration dictionary
        
    Raises:
        CacheConfigError: If configuration is invalid
    """
    try:
        # Check required fields
        required_fields = ['backend', 'cache_dir', 'max_age', 'max_size']
        for field in required_fields:
            if field not in config:
                raise CacheConfigError(f"Missing required field: {field}")
        
        # Validate backend type
        if config['backend'] not in ['disk', 'redis']:
            raise CacheConfigError(f"Invalid backend type: {config['backend']}")
        
        # Validate numeric values
        numeric_fields = {
            'max_age': (0, None),
            'max_size': (0, None),
            'max_file_size': (0, None),
            'compression_level': (0, 9),
            'cleanup_interval': (0, None),
            'hit_threshold': (0.0, 1.0),
            'buffer_size': (0, None)
        }
        
        for field, (min_val, max_val) in numeric_fields.items():
            if field in config:
                value = config[field]
                if not isinstance(value, (int, float)):
                    raise CacheConfigError(f"Invalid type for {field}: {type(value)}")
                if min_val is not None and value < min_val:
                    raise CacheConfigError(f"{field} must be >= {min_val}")
                if max_val is not None and value > max_val:
                    raise CacheConfigError(f"{field} must be <= {max_val}")
        
        # Validate Redis configuration
        if config['backend'] == 'redis':
            redis_config = config.get('redis', {})
            required_redis_fields = ['host', 'port', 'db']
            for field in required_redis_fields:
                if field not in redis_config:
                    raise CacheConfigError(f"Missing required Redis field: {field}")
            
            # Validate Redis port
            if not isinstance(redis_config['port'], int) or not (0 <= redis_config['port'] <= 65535):
                raise CacheConfigError("Invalid Redis port number")
            
            # Validate Redis database
            if not isinstance(redis_config['db'], int) or redis_config['db'] < 0:
                raise CacheConfigError("Invalid Redis database number")
        
        # Validate cache types
        cache_types = config.get('cache_types', [])
        if not isinstance(cache_types, list):
            raise CacheConfigError("cache_types must be a list")
        
        for mime_type in cache_types:
            if not isinstance(mime_type, str) or '/' not in mime_type:
                raise CacheConfigError(f"Invalid MIME type: {mime_type}")
    
    except CacheConfigError:
        raise
    except Exception as e:
        raise CacheConfigError(f"Configuration validation failed: {e}")

def get_cache_config() -> Dict[str, Any]:
    """Get cache configuration.
    
    Returns:
        Cache configuration dictionary
    """
    # Try to load from environment variable
    config_path = os.environ.get('CACHE_CONFIG_PATH')
    
    # Try default locations
    if not config_path:
        default_locations = [
            'config/cache_config.yaml',
            'config/cache_config.yml',
            'cache_config.yaml',
            'cache_config.yml'
        ]
        
        for location in default_locations:
            if os.path.exists(location):
                config_path = location
                break
    
    return load_cache_config(config_path)
