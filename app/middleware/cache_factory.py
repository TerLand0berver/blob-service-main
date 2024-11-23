"""
Cache middleware factory implementation.
"""
from typing import Dict, Any, Optional, Type

from .base import BaseMiddleware
from .cache import CacheMiddleware
from .redis_cache import RedisCacheMiddleware
from ..config.cache import DEFAULT_CACHE_CONFIG

class CacheFactory:
    """Factory class for creating cache middleware instances."""
    
    _cache_backends: Dict[str, Type[BaseMiddleware]] = {
        'disk': CacheMiddleware,
        'redis': RedisCacheMiddleware
    }
    
    @classmethod
    def create(cls, backend: str = 'disk', config: Optional[Dict[str, Any]] = None) -> BaseMiddleware:
        """Create a cache middleware instance.
        
        Args:
            backend: Cache backend type ('disk' or 'redis')
            config: Cache configuration dictionary
            
        Returns:
            Cache middleware instance
            
        Raises:
            ValueError: If backend type is not supported
        """
        if backend not in cls._cache_backends:
            raise ValueError(f"Unsupported cache backend: {backend}")
        
        # Merge config with defaults
        merged_config = DEFAULT_CACHE_CONFIG.copy()
        if config:
            merged_config.update(config)
        
        # Create and return cache instance
        cache_class = cls._cache_backends[backend]
        return cache_class(merged_config)
    
    @classmethod
    def register_backend(cls, name: str, backend_class: Type[BaseMiddleware]):
        """Register a new cache backend.
        
        Args:
            name: Backend name
            backend_class: Backend class implementation
            
        Raises:
            ValueError: If backend name is already registered
        """
        if name in cls._cache_backends:
            raise ValueError(f"Cache backend already registered: {name}")
        
        cls._cache_backends[name] = backend_class
