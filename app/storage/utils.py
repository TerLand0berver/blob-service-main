"""
Storage utility functions.
"""
import os
import hashlib
import mimetypes
from typing import Tuple, Optional
from pathlib import Path

def get_file_hash(file_path: str) -> str:
    """Calculate file hash using SHA-256."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_file_info(file_path: str) -> Tuple[int, str, Optional[str]]:
    """Get file size, extension and mime type."""
    size = os.path.getsize(file_path)
    ext = Path(file_path).suffix.lower()
    mime_type = mimetypes.guess_type(file_path)[0]
    return size, ext, mime_type

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and invalid characters."""
    # Remove path components
    filename = os.path.basename(filename)
    
    # Replace potentially dangerous characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    return filename

def generate_unique_filename(original_filename: str, exists_func) -> str:
    """Generate unique filename by appending number if file exists."""
    filename = sanitize_filename(original_filename)
    name, ext = os.path.splitext(filename)
    counter = 1
    
    while exists_func(filename):
        filename = f"{name}_{counter}{ext}"
        counter += 1
    
    return filename

def get_storage_stats(directory: str) -> dict:
    """Get storage statistics for a directory."""
    total_size = 0
    file_count = 0
    extension_stats = {}
    
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            size = os.path.getsize(file_path)
            total_size += size
            file_count += 1
            
            ext = Path(file).suffix.lower()
            if ext not in extension_stats:
                extension_stats[ext] = {"count": 0, "size": 0}
            extension_stats[ext]["count"] += 1
            extension_stats[ext]["size"] += size
    
    return {
        "total_size": total_size,
        "file_count": file_count,
        "extension_stats": extension_stats
    }
