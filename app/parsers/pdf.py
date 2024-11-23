"""
PDF parser implementation.
"""
import io
from typing import Dict, Any, Optional
import fitz  # PyMuPDF
from PIL import Image
import magic

from .base import BaseParser, ParserError

class PDFParser(BaseParser):
    """Parser for PDF files."""
    
    SUPPORTED_TYPES = {'application/pdf'}
    SUPPORTED_EXTENSIONS = {'.pdf'}
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize PDF parser."""
        super().__init__(config)
        self.image_quality = self.config.get('image_quality', 85)
        self.max_image_size = self.config.get('max_image_size', 2048)
        self.optimize_images = self.config.get('optimize_images', True)
        self.extract_text = self.config.get('extract_text', True)
        self.max_text_length = self.config.get('max_text_length', 10000)
    
    async def can_handle(self, content_type: str, file_extension: str) -> bool:
        """Check if parser can handle this file type."""
        return (content_type.lower() in self.SUPPORTED_TYPES or
                file_extension.lower() in self.SUPPORTED_EXTENSIONS)
    
    async def parse(self, file_data: bytes, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse PDF and extract metadata."""
        try:
            with fitz.open(stream=file_data, filetype="pdf") as doc:
                metadata.update({
                    'page_count': len(doc),
                    'title': doc.metadata.get('title', ''),
                    'author': doc.metadata.get('author', ''),
                    'subject': doc.metadata.get('subject', ''),
                    'keywords': doc.metadata.get('keywords', ''),
                    'creator': doc.metadata.get('creator', ''),
                    'producer': doc.metadata.get('producer', ''),
                    'creation_date': doc.metadata.get('creationDate', ''),
                    'modification_date': doc.metadata.get('modDate', ''),
                    'format': 'PDF',
                    'version': doc.version,
                    'is_encrypted': doc.isEncrypted,
                    'can_print': doc.permissions.get('print', False),
                    'can_modify': doc.permissions.get('modify', False),
                    'can_copy': doc.permissions.get('copy', False),
                })
                
                if self.extract_text:
                    # Extract text from first few pages
                    text = ""
                    for page in doc:
                        text += page.get_text()
                        if len(text) > self.max_text_length:
                            text = text[:self.max_text_length] + "..."
                            break
                    metadata['text_preview'] = text
                
                # Count images
                image_count = 0
                for page in doc:
                    image_list = page.get_images()
                    image_count += len(image_list)
                metadata['image_count'] = image_count
                
                return metadata
        except Exception as e:
            raise ParserError(f"Failed to parse PDF: {e}")
    
    async def validate(self, file_data: bytes, metadata: Dict[str, Any]) -> bool:
        """Validate PDF format."""
        try:
            mime = magic.Magic(mime=True)
            content_type = mime.from_buffer(file_data)
            
            if content_type not in self.SUPPORTED_TYPES:
                return False
            
            # Try to open the PDF
            with fitz.open(stream=file_data, filetype="pdf") as doc:
                # Check if encrypted and we can't access it
                if doc.isEncrypted and not doc.permissions.get('read', False):
                    return False
                return True
        except Exception:
            return False
    
    async def optimize(self, file_data: bytes, metadata: Dict[str, Any]) -> tuple[bytes, Dict[str, Any]]:
        """Optimize PDF file."""
        try:
            with fitz.open(stream=file_data, filetype="pdf") as doc:
                if not self.optimize_images:
                    return file_data, metadata
                
                # Track optimization stats
                original_size = len(file_data)
                images_optimized = 0
                
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    image_list = page.get_images()
                    
                    for img_index, img in enumerate(image_list):
                        xref = img[0]
                        
                        # Extract image
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        
                        # Open with PIL
                        with Image.open(io.BytesIO(image_bytes)) as img:
                            # Skip small images
                            if img.width <= self.max_image_size and img.height <= self.max_image_size:
                                continue
                            
                            # Resize if too large
                            if img.width > self.max_image_size or img.height > self.max_image_size:
                                img.thumbnail((self.max_image_size, self.max_image_size), 
                                           Image.Resampling.LANCZOS)
                            
                            # Convert to RGB if necessary
                            if img.mode in ('RGBA', 'LA'):
                                background = Image.new('RGB', img.size, (255, 255, 255))
                                background.paste(img, mask=img.split()[-1])
                                img = background
                            elif img.mode not in ('RGB'):
                                img = img.convert('RGB')
                            
                            # Save optimized image
                            output = io.BytesIO()
                            img.save(output, format='JPEG', quality=self.image_quality, 
                                   optimize=True)
                            optimized_bytes = output.getvalue()
                            
                            # Replace image in PDF if smaller
                            if len(optimized_bytes) < len(image_bytes):
                                page.replace_image(xref, stream=optimized_bytes)
                                images_optimized += 1
                
                if images_optimized > 0:
                    # Save optimized PDF
                    output = io.BytesIO()
                    doc.save(output, garbage=4, deflate=True, clean=True)
                    optimized_data = output.getvalue()
                    
                    # Update metadata
                    metadata['optimized'] = True
                    metadata['original_size'] = original_size
                    metadata['images_optimized'] = images_optimized
                    
                    return optimized_data, metadata
                
                return file_data, metadata
                
        except Exception as e:
            raise ParserError(f"Failed to optimize PDF: {e}")
