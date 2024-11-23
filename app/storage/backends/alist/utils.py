"""
AList storage utilities.
"""
import os
from typing import Dict, Any, List
from datetime import datetime

def format_file_info(
    file_info: Dict[str, Any],
    root_dir: str = ""
) -> Dict[str, Any]:
    """Format AList file info to standard metadata format.
    
    Args:
        file_info: AList file info
        root_dir: Root directory path
    
    Returns:
        Formatted metadata
    """
    # Get relative path
    path = file_info['name']
    if root_dir:
        path = os.path.relpath(path, root_dir)
    
    return {
        'path': path,
        'size': file_info['size'],
        'content_type': file_info.get('type', 'application/octet-stream'),
        'created_at': datetime.fromtimestamp(
            file_info['modified']
        ).isoformat(),
        'metadata': {}
    }

def format_file_list(
    items: List[Dict[str, Any]],
    root_dir: str = ""
) -> List[Dict[str, Any]]:
    """Format AList file list to standard metadata format.
    
    Args:
        items: List of AList file info
        root_dir: Root directory path
    
    Returns:
        List of formatted metadata
    """
    files = []
    for item in items:
        if not item['is_dir']:
            files.append(format_file_info(item, root_dir))
    return files
