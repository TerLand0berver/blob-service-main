"""
Image parser implementation.
"""
import io
from typing import Dict, Any, Set, Optional
from PIL import Image, ImageOps
import pillow_avif_plugin  # For AVIF support
import magic

from .base import BaseParser, ParserError

class ImageParser(BaseParser):
    """Parser for image files."""
    
    SUPPORTED_TYPES = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'image/tiff', 'image/bmp', 'image/avif'
    }
    
    SUPPORTED_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.gif', '.webp',
        '.tiff', '.bmp', '.avif'
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize image parser."""
        super().__init__(config)
        self.max_dimension = self.config.get('max_dimension', 4096)
        self.quality = self.config.get('quality', 85)
        self.force_webp = self.config.get('force_webp', True)
        self.preserve_animation = self.config.get('preserve_animation', True)
    
    async def can_handle(self, content_type: str, file_extension: str) -> bool:
        """Check if parser can handle this image type."""
        return (content_type.lower() in self.SUPPORTED_TYPES or
                file_extension.lower() in self.SUPPORTED_EXTENSIONS)
    
    async def parse(self, file_data: bytes, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse image and extract metadata."""
        try:
            with Image.open(io.BytesIO(file_data)) as img:
                metadata.update({
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'is_animated': getattr(img, 'is_animated', False),
                    'n_frames': getattr(img, 'n_frames', 1)
                })
                
                if 'dpi' in img.info:
                    metadata['dpi'] = img.info['dpi']
                if 'exif' in img.info:
                    metadata['has_exif'] = True
                
                return metadata
        except Exception as e:
            raise ParserError(f"Failed to parse image: {e}")
    
    async def validate(self, file_data: bytes, metadata: Dict[str, Any]) -> bool:
        """Validate image format."""
        try:
            mime = magic.Magic(mime=True)
            content_type = mime.from_buffer(file_data)
            
            if content_type not in self.SUPPORTED_TYPES:
                return False
            
            with Image.open(io.BytesIO(file_data)) as img:
                # Check dimensions
                if img.width > self.max_dimension or img.height > self.max_dimension:
                    return False
                return True
        except Exception:
            return False
    
    async def optimize(self, file_data: bytes, metadata: Dict[str, Any]) -> tuple[bytes, Dict[str, Any]]:
        """Optimize image format and size."""
        try:
            with Image.open(io.BytesIO(file_data)) as img:
                # Handle animated images
                if getattr(img, 'is_animated', False) and self.preserve_animation:
                    if self.force_webp and img.format != 'WEBP':
                        # Convert to animated WebP
                        output = io.BytesIO()
                        img.save(output, format='WEBP', save_all=True, quality=self.quality,
                               method=6, minimize_size=True, lossless=False)
                        metadata['format'] = 'WEBP'
                        return output.getvalue(), metadata
                    return file_data, metadata
                
                # Process single image
                # Auto-orient image based on EXIF
                img = ImageOps.exif_transpose(img)
                
                # Convert to RGB/RGBA if necessary
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGBA' if img.mode == 'P' else 'RGB')
                
                # Resize if needed
                if img.width > self.max_dimension or img.height > self.max_dimension:
                    img.thumbnail((self.max_dimension, self.max_dimension), Image.Resampling.LANCZOS)
                    metadata.update({
                        'width': img.width,
                        'height': img.height
                    })
                
                # Convert to WebP if forced or if it would save space
                output = io.BytesIO()
                if self.force_webp:
                    img.save(output, format='WEBP', quality=self.quality,
                           method=6, lossless=False)
                    metadata['format'] = 'WEBP'
                else:
                    img.save(output, format=img.format, quality=self.quality,
                           optimize=True)
                
                optimized_data = output.getvalue()
                if len(optimized_data) >= len(file_data):
                    return file_data, metadata
                    
                return optimized_data, metadata
                
        except Exception as e:
            raise ParserError(f"Failed to optimize image: {e}")
