"""
Redis cache backend implementation.
"""
import json
import time
from typing import Dict, Any, Optional, Tuple
import redis

from .base import BaseMiddleware
from ..config.cache import DEFAULT_CACHE_CONFIG

class RedisCacheMiddleware(BaseMiddleware):
    """Redis-based cache middleware implementation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Redis cache middleware."""
        super().__init__(config or DEFAULT_CACHE_CONFIG)
        
        # Initialize Redis connection
        redis_config = self.config.get('redis', {})
        self.redis = redis.Redis(
            host=redis_config.get('host', 'localhost'),
            port=redis_config.get('port', 6379),
            db=redis_config.get('db', 0),
            password=redis_config.get('password'),
            decode_responses=True
        )
        
        self.prefix = redis_config.get('prefix', 'blob_service_cache:')
        self.max_age = self.config.get('max_age', 3600)
        self.max_file_size = self.config.get('max_file_size', 100 * 1024 * 1024)
        self.enabled = self.config.get('enabled', True)
        
        # Initialize stats
        self.stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'size': 0
        }
    
    async def process_upload(self, file_data: bytes, metadata: Dict[str, Any]) -> Tuple[bytes, Dict[str, Any]]:
        """Process file during upload."""
        if not self.enabled or len(file_data) > self.max_file_size:
            return file_data, metadata
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(file_data, metadata)
            
            # Try to get from cache
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                self.stats['hits'] += 1
                return cached_data['file_data'], cached_data['metadata']
            
            self.stats['misses'] += 1
            
            # Store in cache
            self._store_in_cache(cache_key, file_data, metadata)
            
            return file_data, metadata
            
        except Exception as e:
            self.stats['errors'] += 1
            print(f"Redis cache error during upload: {e}")
            return file_data, metadata
    
    async def process_download(self, file_data: bytes, metadata: Dict[str, Any]) -> Tuple[bytes, Dict[str, Any]]:
        """Process file during download."""
        if not self.enabled or len(file_data) > self.max_file_size:
            return file_data, metadata
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(file_data, metadata)
            
            # Try to get from cache
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                self.stats['hits'] += 1
                return cached_data['file_data'], cached_data['metadata']
            
            self.stats['misses'] += 1
            
            # Store in cache
            self._store_in_cache(cache_key, file_data, metadata)
            
            return file_data, metadata
            
        except Exception as e:
            self.stats['errors'] += 1
            print(f"Redis cache error during download: {e}")
            return file_data, metadata
    
    def _generate_cache_key(self, file_data: bytes, metadata: Dict[str, Any]) -> str:
        """Generate a unique cache key."""
        import hashlib
        
        # Create hash of file data
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        # Create hash of metadata
        meta_dict = {
            'content_type': metadata.get('content_type', ''),
            'extension': metadata.get('extension', ''),
            'size': len(file_data)
        }
        meta_hash = hashlib.sha256(
            json.dumps(meta_dict, sort_keys=True).encode()
        ).hexdigest()
        
        return f"{self.prefix}{file_hash}_{meta_hash}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from Redis cache."""
        try:
            # Get data and metadata
            pipe = self.redis.pipeline()
            pipe.get(f"{cache_key}:data")
            pipe.get(f"{cache_key}:meta")
            pipe.get(f"{cache_key}:time")
            data, meta, timestamp = pipe.execute()
            
            if not all([data, meta, timestamp]):
                return None
            
            # Check expiration
            if time.time() - float(timestamp) > self.max_age:
                self._remove_from_cache(cache_key)
                return None
            
            return {
                'file_data': data.encode(),
                'metadata': json.loads(meta)
            }
            
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    def _store_in_cache(self, cache_key: str, file_data: bytes, metadata: Dict[str, Any]):
        """Store data in Redis cache."""
        try:
            pipe = self.redis.pipeline()
            
            # Store file data
            pipe.set(f"{cache_key}:data", file_data)
            
            # Store metadata
            pipe.set(f"{cache_key}:meta", json.dumps(metadata))
            
            # Store timestamp
            pipe.set(f"{cache_key}:time", time.time())
            
            # Set expiration
            pipe.expire(f"{cache_key}:data", self.max_age)
            pipe.expire(f"{cache_key}:meta", self.max_age)
            pipe.expire(f"{cache_key}:time", self.max_age)
            
            pipe.execute()
            
            # Update stats
            self.stats['size'] += len(file_data) + len(json.dumps(metadata))
            
        except Exception as e:
            print(f"Redis store error: {e}")
    
    def _remove_from_cache(self, cache_key: str):
        """Remove data from Redis cache."""
        try:
            pipe = self.redis.pipeline()
            pipe.delete(f"{cache_key}:data")
            pipe.delete(f"{cache_key}:meta")
            pipe.delete(f"{cache_key}:time")
            pipe.execute()
        except Exception as e:
            print(f"Redis remove error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'errors': self.stats['errors'],
            'size': self.stats['size'],
            'hit_ratio': self.stats['hits'] / (self.stats['hits'] + self.stats['misses']) if (self.stats['hits'] + self.stats['misses']) > 0 else 0,
            'error_rate': self.stats['errors'] / (self.stats['hits'] + self.stats['misses']) if (self.stats['hits'] + self.stats['misses']) > 0 else 0
        }
