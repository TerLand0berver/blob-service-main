"""
Base storage interface.
"""
from abc import ABC, abstractmethod
from typing import BinaryIO, Optional, Dict, Any, List, Union, Tuple
from datetime import datetime
import hashlib
import logging
from ..core.schemas import FileInfo, FileMetadata
from ..core.config import config

logger = logging.getLogger(__name__)

class StorageError(Exception):
    """Storage error exception"""
    pass

class BaseStorage(ABC):
    """Base storage interface."""
    
    def __init__(self):
        self.stats = {
            'uploads': 0,
            'downloads': 0,
            'deletes': 0,
            'errors': 0,
            'bytes_uploaded': 0,
            'bytes_downloaded': 0
        }
    
    @abstractmethod
    async def save(
        self,
        file: BinaryIO,
        path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FileInfo:
        """Save file to storage
        
        Args:
            file: File-like object
            path: Optional storage path
            metadata: Optional metadata
            
        Returns:
            FileInfo object
            
        Raises:
            StorageError: If save fails
        """
        pass
    
    @abstractmethod
    async def get(
        self,
        path: str,
        include_metadata: bool = True
    ) -> Union[BinaryIO, Tuple[BinaryIO, FileMetadata]]:
        """Get file from storage
        
        Args:
            path: Storage path
            include_metadata: Include metadata in response
            
        Returns:
            File content and optional metadata
            
        Raises:
            StorageError: If get fails
        """
        pass
    
    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Delete file from storage
        
        Args:
            path: Storage path
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            StorageError: If delete fails
        """
        pass
    
    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Check if file exists
        
        Args:
            path: Storage path
            
        Returns:
            True if exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def list_files(
        self,
        path: Optional[str] = None,
        recursive: bool = False,
        include_metadata: bool = False
    ) -> List[Union[str, FileInfo]]:
        """List files in storage
        
        Args:
            path: Optional path prefix
            recursive: List files recursively
            include_metadata: Include file metadata
            
        Returns:
            List of file paths or FileInfo objects
        """
        pass
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics
        
        Returns:
            Dictionary of storage statistics
        """
        return {
            **self.stats,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _update_stats(self, operation: str, size: int = 0):
        """Update storage statistics
        
        Args:
            operation: Operation type (upload/download/delete/error)
            size: Size of data transferred
        """
        if operation == 'upload':
            self.stats['uploads'] += 1
            self.stats['bytes_uploaded'] += size
        elif operation == 'download':
            self.stats['downloads'] += 1
            self.stats['bytes_downloaded'] += size
        elif operation == 'delete':
            self.stats['deletes'] += 1
        elif operation == 'error':
            self.stats['errors'] += 1
    
    def _calculate_checksum(self, file: BinaryIO) -> str:
        """Calculate file checksum
        
        Args:
            file: File-like object
            
        Returns:
            File checksum
        """
        hasher = hashlib.sha256()
        for chunk in iter(lambda: file.read(65536), b''):
            hasher.update(chunk)
        file.seek(0)
        return hasher.hexdigest()
    
    def _create_metadata(
        self,
        file: BinaryIO,
        content_type: str,
        custom: Optional[Dict[str, Any]] = None
    ) -> FileMetadata:
        """Create file metadata
        
        Args:
            file: File-like object
            content_type: Content type
            custom: Custom metadata
            
        Returns:
            FileMetadata object
        """
        now = datetime.utcnow()
        return FileMetadata(
            content_type=content_type,
            size=file.tell(),
            created_at=now,
            updated_at=now,
            checksum=self._calculate_checksum(file),
            custom=custom or {}
        )
