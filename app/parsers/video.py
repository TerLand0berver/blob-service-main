"""
Video parser implementation - Link only version.
"""
from typing import Dict, Any, Optional
import magic

from .base import BaseParser, ParserError

class VideoParser(BaseParser):
    """Parser for video files - Link only version."""
    
    SUPPORTED_TYPES = {
        'video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo',
        'video/x-matroska', 'video/webm', 'video/x-flv'
    }
    
    SUPPORTED_EXTENSIONS = {
        '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.mpeg', '.mpg'
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize video parser."""
        super().__init__(config)

    async def can_handle(self, content_type: str, file_extension: str) -> bool:
        """Check if parser can handle this file type."""
        return (content_type.lower() in self.SUPPORTED_TYPES or
                file_extension.lower() in self.SUPPORTED_EXTENSIONS)

    async def validate(self, file_data: bytes, metadata: Dict[str, Any]) -> bool:
        """Validate video format."""
        try:
            mime = magic.Magic(mime=True)
            content_type = mime.from_buffer(file_data)
            return content_type.startswith('video/')
        except Exception:
            return False

    async def parse(self, file_data: bytes, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse video metadata."""
        try:
            mime = magic.Magic(mime=True)
            content_type = mime.from_buffer(file_data)
            
            metadata.update({
                'type': content_type,
                'size': len(file_data),
                'link_only': True  # 标记这是一个仅链接的视频文件
            })
            
            return metadata
        except Exception as e:
            raise ParserError(f"Failed to parse video: {e}")

    async def optimize(self, file_data: bytes, metadata: Dict[str, Any]) -> tuple[bytes, Dict[str, Any]]:
        """No optimization needed for link-only videos."""
        return file_data, metadata
