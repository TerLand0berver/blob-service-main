"""
Cache middleware implementation.
"""
import hashlib
import json
import time
from typing import Dict, Any, Optional, Tuple
import aiofiles
import os

from .base import BaseMiddleware

class CacheMiddleware(BaseMiddleware):
    """Middleware for caching file processing results."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize cache middleware."""
        super().__init__(config)
        self.cache_dir = self.config.get('cache_dir', 'cache')
        self.max_age = self.config.get('max_age', 3600)  # 1 hour
        self.max_size = self.config.get('max_size', 1024 * 1024 * 1024)  # 1GB
        self.enabled = self.config.get('enabled', True)
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize cache stats
        self.stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'size': 0
        }
    
    async def process_upload(self, file_data: bytes, metadata: Dict[str, Any]) -> Tuple[bytes, Dict[str, Any]]:
        """Process file during upload."""
        if not self.enabled:
            return file_data, metadata
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(file_data, metadata)
            
            # Try to get from cache
            cached_data = await self._get_from_cache(cache_key)
            if cached_data:
                self.stats['hits'] += 1
                return cached_data['file_data'], cached_data['metadata']
            
            self.stats['misses'] += 1
            
            # Store in cache for future use
            await self._store_in_cache(cache_key, file_data, metadata)
            
            return file_data, metadata
            
        except Exception as e:
            self.stats['errors'] += 1
            print(f"Cache error during upload: {e}")
            return file_data, metadata
    
    async def process_download(self, file_data: bytes, metadata: Dict[str, Any]) -> Tuple[bytes, Dict[str, Any]]:
        """Process file during download."""
        if not self.enabled:
            return file_data, metadata
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(file_data, metadata)
            
            # Try to get from cache
            cached_data = await self._get_from_cache(cache_key)
            if cached_data:
                self.stats['hits'] += 1
                return cached_data['file_data'], cached_data['metadata']
            
            self.stats['misses'] += 1
            
            # Store in cache for future use
            await self._store_in_cache(cache_key, file_data, metadata)
            
            return file_data, metadata
            
        except Exception as e:
            self.stats['errors'] += 1
            print(f"Cache error during download: {e}")
            return file_data, metadata
    
    def _generate_cache_key(self, file_data: bytes, metadata: Dict[str, Any]) -> str:
        """Generate a unique cache key based on file data and metadata."""
        # Create a hash of the file data
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        # Create a hash of relevant metadata
        meta_dict = {
            'content_type': metadata.get('content_type', ''),
            'extension': metadata.get('extension', ''),
            'size': len(file_data)
        }
        meta_hash = hashlib.sha256(
            json.dumps(meta_dict, sort_keys=True).encode()
        ).hexdigest()
        
        return f"{file_hash}_{meta_hash}"
    
    async def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get file data and metadata from cache."""
        try:
            cache_path = os.path.join(self.cache_dir, cache_key)
            meta_path = cache_path + '.meta'
            
            # Check if cache files exist
            if not (os.path.exists(cache_path) and os.path.exists(meta_path)):
                return None
            
            # Check if cache is expired
            if time.time() - os.path.getmtime(cache_path) > self.max_age:
                # Remove expired cache
                os.remove(cache_path)
                os.remove(meta_path)
                return None
            
            # Read file data
            async with aiofiles.open(cache_path, 'rb') as f:
                file_data = await f.read()
            
            # Read metadata
            async with aiofiles.open(meta_path, 'r') as f:
                metadata = json.loads(await f.read())
            
            return {
                'file_data': file_data,
                'metadata': metadata
            }
            
        except Exception as e:
            print(f"Cache read error: {e}")
            return None
    
    async def _store_in_cache(self, cache_key: str, file_data: bytes, metadata: Dict[str, Any]):
        """Store file data and metadata in cache."""
        try:
            # Check cache size
            await self._cleanup_cache()
            
            cache_path = os.path.join(self.cache_dir, cache_key)
            meta_path = cache_path + '.meta'
            
            # Write file data
            async with aiofiles.open(cache_path, 'wb') as f:
                await f.write(file_data)
            
            # Write metadata
            async with aiofiles.open(meta_path, 'w') as f:
                await f.write(json.dumps(metadata))
            
            # Update cache size
            self.stats['size'] += len(file_data) + os.path.getsize(meta_path)
            
        except Exception as e:
            print(f"Cache write error: {e}")
    
    async def _cleanup_cache(self):
        """Clean up old cache entries if cache size exceeds limit."""
        try:
            # Get list of cache files
            cache_files = []
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith('.meta'):
                    path = os.path.join(self.cache_dir, filename)
                    cache_files.append({
                        'path': path,
                        'size': os.path.getsize(path),
                        'atime': os.path.getatime(path)
                    })
            
            # Sort by access time (oldest first)
            cache_files.sort(key=lambda x: x['atime'])
            
            # Remove old files until we're under the limit
            current_size = sum(f['size'] for f in cache_files)
            for file in cache_files:
                if current_size <= self.max_size:
                    break
                    
                try:
                    # Remove data file
                    os.remove(file['path'])
                    # Remove metadata file
                    os.remove(file['path'] + '.meta')
                    current_size -= file['size']
                except Exception as e:
                    print(f"Error removing cache file: {e}")
            
            # Update cache size
            self.stats['size'] = current_size
            
        except Exception as e:
            print(f"Cache cleanup error: {e}")
    
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
