"""
Storage validation functions.
"""
import os
from typing import List, Set, Optional
import magic
from ..core.config import config

def validate_file_size(file_size: int) -> bool:
    """Validate file size against configured limits."""
    max_size = config.storage_config["max_file_size"]
    return file_size <= max_size

def validate_file_type(file_path: str, allowed_types: Optional[Set[str]] = None) -> bool:
    """Validate file type using magic numbers."""
    if allowed_types is None:
        allowed_types = set(config.storage_config["allowed_types"])
    
    mime = magic.Magic(mime=True)
    file_type = mime.from_file(file_path)
    return file_type in allowed_types

def validate_file_extension(filename: str, allowed_extensions: Optional[Set[str]] = None) -> bool:
    """Validate file extension against allowed list."""
    if allowed_extensions is None:
        allowed_extensions = set(config.storage_config["allowed_extensions"])
    
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed_extensions

def validate_storage_quota(new_file_size: int) -> bool:
    """Validate if adding new file would exceed storage quota."""
    quota = config.storage_config["storage_quota"]
    if quota is None:  # No quota limit
        return True
    
    current_usage = get_current_storage_usage()
    return (current_usage + new_file_size) <= quota

def get_current_storage_usage() -> int:
    """Get current storage usage in bytes."""
    storage_path = config.storage_config["path"]
    total_size = 0
    
    for root, _, files in os.walk(storage_path):
        for file in files:
            file_path = os.path.join(root, file)
            total_size += os.path.getsize(file_path)
    
    return total_size

def validate_file(
    file_path: str,
    filename: str,
    allowed_types: Optional[Set[str]] = None,
    allowed_extensions: Optional[Set[str]] = None
) -> List[str]:
    """Validate file against all constraints."""
    errors = []
    
    # Check file size
    file_size = os.path.getsize(file_path)
    if not validate_file_size(file_size):
        errors.append("File size exceeds maximum allowed size")
    
    # Check file type
    if not validate_file_type(file_path, allowed_types):
        errors.append("File type not allowed")
    
    # Check file extension
    if not validate_file_extension(filename, allowed_extensions):
        errors.append("File extension not allowed")
    
    # Check storage quota
    if not validate_storage_quota(file_size):
        errors.append("Storage quota would be exceeded")
    
    return errors
