"""
API utility functions.
"""
import time
import mimetypes
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import aiofiles
from fastapi import UploadFile
from ..config import config
from ..core.errors import ValidationError
from .models import FileInfo

# Start time for uptime calculation
START_TIME = time.time()

def get_uptime() -> float:
    """Get application uptime in seconds.
    
    Returns:
        Uptime in seconds
    """
    return time.time() - START_TIME

def get_content_type(filename: str) -> str:
    """Get file content type.
    
    Args:
        filename: Filename to check
        
    Returns:
        Content type string
    """
    content_type, _ = mimetypes.guess_type(filename)
    return content_type or 'application/octet-stream'

def is_image_file(content_type: str) -> bool:
    """Check if content type is an image.
    
    Args:
        content_type: Content type to check
        
    Returns:
        True if content type is an image
    """
    return content_type.startswith('image/')

async def save_upload_file(
    file: UploadFile,
    directory: Path,
    chunk_size: int = 1024 * 1024
) -> Tuple[Path, int]:
    """Save uploaded file.
    
    Args:
        file: File to save
        directory: Directory to save to
        chunk_size: Read chunk size
        
    Returns:
        Tuple of (file path, file size)
        
    Raises:
        ValidationError: If file save fails
    """
    try:
        # Create directory if needed
        directory.mkdir(parents=True, exist_ok=True)
        
        # Generate file path
        file_path = directory / file.filename
        
        # Save file
        size = 0
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(chunk_size):
                await f.write(chunk)
                size += len(chunk)
                
        return file_path, size
        
    except Exception as e:
        raise ValidationError(f"Failed to save file: {e}")

def create_file_info(
    filename: str,
    size: int,
    url: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> FileInfo:
    """Create file information.
    
    Args:
        filename: Original filename
        size: File size in bytes
        url: Optional file URL
        metadata: Optional file metadata
        
    Returns:
        FileInfo instance
    """
    # Get content type
    content_type = get_content_type(filename)
    
    # Create file info
    return FileInfo(
        filename=filename,
        size=size,
        content_type=content_type,
        url=url,
        is_image=is_image_file(content_type),
        metadata=metadata or {}
    )

def format_size(size: int) -> str:
    """Format file size.
    
    Args:
        size: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"
