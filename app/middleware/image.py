"""
Image processing middleware.
"""
from typing import Dict, Any, Optional
from ..parsers.registry import ParserRegistry
from ..parsers.image import ImageParser
from .base import BaseMiddleware

class ImageMiddleware(BaseMiddleware):
    """Middleware for image processing."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize image middleware."""
        super().__init__(config)
        self.parser_registry = ParserRegistry.from_config()
    
    async def process_upload(self, file_data: bytes, metadata: Dict[str, Any]) -> tuple[bytes, Dict[str, Any]]:
        """Process image during upload."""
        content_type = metadata.get('content_type', '')
        file_extension = metadata.get('extension', '')
        
        parser = await self.parser_registry.get_parser(content_type, file_extension)
        if not isinstance(parser, ImageParser):
            return file_data, metadata
        
        # Validate image
        if not await parser.validate(file_data, metadata):
            return file_data, metadata
        
        # Parse image metadata
        metadata = await parser.parse(file_data, metadata)
        
        # Optimize image
        return await parser.optimize(file_data, metadata)
    
    async def process_download(self, file_data: bytes, metadata: Dict[str, Any]) -> tuple[bytes, Dict[str, Any]]:
        """Process image during download."""
        # No processing needed during download
        return file_data, metadata
    
    def validate(self) -> bool:
        """Validate middleware configuration."""
        return True
