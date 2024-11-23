"""
Compression middleware.
"""
import gzip
import zlib
from typing import Dict, Any, Optional

from .base import BaseMiddleware
from ..core.config import config

class CompressionMiddleware(BaseMiddleware):
    """Middleware for file compression."""
    
    COMPRESSION_METHODS = {
        'gzip': (gzip.compress, gzip.decompress),
        'zlib': (zlib.compress, zlib.decompress),
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize compression middleware."""
        super().__init__(config)
        self.method = self.config.get('method', 'gzip')
        self.level = self.config.get('level', 6)
        self.min_size = self.config.get('min_size', 1024)  # 1KB
        self.compressible_types = set(self.config.get(
            'compressible_types',
            ['text/', 'application/json', 'application/xml', 'application/javascript']
        ))
    
    def should_compress(self, size: int, content_type: str) -> bool:
        """Check if file should be compressed."""
        if size < self.min_size:
            return False
            
        return any(t in content_type for t in self.compressible_types)
    
    async def process_upload(self, file_data: bytes, metadata: Dict[str, Any]) -> tuple[bytes, Dict[str, Any]]:
        """Compress file during upload if applicable."""
        size = len(file_data)
        content_type = metadata.get('content_type', '')
        
        if not self.should_compress(size, content_type):
            return file_data, metadata
        
        compress_func = self.COMPRESSION_METHODS[self.method][0]
        compressed_data = compress_func(file_data, level=self.level)
        
        # Only use compression if it actually reduces size
        if len(compressed_data) < size:
            metadata['compressed'] = True
            metadata['compression_method'] = self.method
            metadata['original_size'] = size
            return compressed_data, metadata
        
        return file_data, metadata
    
    async def process_download(self, file_data: bytes, metadata: Dict[str, Any]) -> tuple[bytes, Dict[str, Any]]:
        """Decompress file during download if it was compressed."""
        if not metadata.get('compressed'):
            return file_data, metadata
        
        method = metadata['compression_method']
        decompress_func = self.COMPRESSION_METHODS[method][1]
        decompressed_data = decompress_func(file_data)
        
        # Remove compression metadata
        metadata.pop('compressed', None)
        metadata.pop('compression_method', None)
        metadata.pop('original_size', None)
        
        return decompressed_data, metadata
    
    def validate(self) -> bool:
        """Validate compression configuration."""
        if self.method not in self.COMPRESSION_METHODS:
            return False
        if not isinstance(self.level, int) or not 0 <= self.level <= 9:
            return False
        if not isinstance(self.min_size, int) or self.min_size < 0:
            return False
        return True
