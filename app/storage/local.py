"""Local filesystem storage backend."""
import os
import shutil
import aiofiles
import aiofiles.os
from datetime import datetime
from typing import BinaryIO, Optional, Dict, Any, List, Union, Tuple
import mimetypes
import logging
from pathlib import Path

from .base import StorageBackend, StorageError
from ..core.schemas import FileInfo, FileMetadata
from ..core.config import config

logger = logging.getLogger(__name__)

class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend."""
    
    def __init__(self, base_path: Optional[str] = None):
        """Initialize local storage.
        
        Args:
            base_path: Base storage path
        """
        super().__init__()
        self.base_path = Path(base_path or config.storage.local_path).resolve()
        self._ensure_base_path()
        
    def _ensure_base_path(self):
        """Ensure base path exists."""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise StorageError(f"Failed to create base path: {str(e)}")
            
    def _get_full_path(self, path: str) -> Path:
        """Get full filesystem path.
        
        Args:
            path: Storage path
            
        Returns:
            Full filesystem path
        """
        full_path = (self.base_path / path).resolve()
        if not str(full_path).startswith(str(self.base_path)):
            raise StorageError("Path traversal detected")
        return full_path
        
    async def save(
        self,
        file: BinaryIO,
        path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FileInfo:
        """Save file to local storage.
        
        Args:
            file: File-like object
            path: Optional storage path
            metadata: Optional metadata
            
        Returns:
            FileInfo object
            
        Raises:
            StorageError: If save fails
        """
        try:
            if path is None:
                # Generate unique filename if not provided
                ext = mimetypes.guess_extension(metadata.get("content_type", "")) if metadata else ""
                path = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}{ext}"
                
            full_path = self._get_full_path(path)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save file
            async with aiofiles.open(full_path, 'wb') as f:
                while chunk := file.read(65536):
                    await f.write(chunk)
                    
            # Create metadata
            file_metadata = self._create_metadata(
                file,
                metadata.get("content_type", "application/octet-stream") if metadata else "application/octet-stream",
                metadata
            )
            
            # Update stats
            self._update_stats('upload', file_metadata.size)
            
            return FileInfo(
                path=str(path),
                metadata=file_metadata
            )
            
        except Exception as e:
            self._update_stats('error')
            raise StorageError(f"Failed to save file: {str(e)}")
            
    async def get(
        self,
        path: str,
        include_metadata: bool = True
    ) -> Union[BinaryIO, Tuple[BinaryIO, FileMetadata]]:
        """Get file from local storage.
        
        Args:
            path: Storage path
            include_metadata: Include metadata in response
            
        Returns:
            File content and optional metadata
            
        Raises:
            StorageError: If get fails
        """
        try:
            full_path = self._get_full_path(path)
            if not full_path.exists():
                raise StorageError("File not found")
                
            # Open file
            file = open(full_path, 'rb')
            
            if not include_metadata:
                return file
                
            # Get metadata
            stat = full_path.stat()
            metadata = FileMetadata(
                content_type=mimetypes.guess_type(str(full_path))[0] or "application/octet-stream",
                size=stat.st_size,
                created_at=datetime.fromtimestamp(stat.st_ctime),
                updated_at=datetime.fromtimestamp(stat.st_mtime),
                checksum=self._calculate_checksum(file)
            )
            
            # Update stats
            self._update_stats('download', metadata.size)
            
            return file, metadata
            
        except Exception as e:
            self._update_stats('error')
            raise StorageError(f"Failed to get file: {str(e)}")
            
    async def delete(self, path: str) -> bool:
        """Delete file from local storage.
        
        Args:
            path: Storage path
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            StorageError: If delete fails
        """
        try:
            full_path = self._get_full_path(path)
            if not full_path.exists():
                return False
                
            await aiofiles.os.remove(full_path)
            self._update_stats('delete')
            return True
            
        except Exception as e:
            self._update_stats('error')
            raise StorageError(f"Failed to delete file: {str(e)}")
            
    async def exists(self, path: str) -> bool:
        """Check if file exists in local storage.
        
        Args:
            path: Storage path
            
        Returns:
            True if exists, False otherwise
        """
        try:
            return self._get_full_path(path).exists()
        except Exception:
            return False
            
    async def list_files(
        self,
        path: Optional[str] = None,
        recursive: bool = False,
        include_metadata: bool = False
    ) -> List[Union[str, FileInfo]]:
        """List files in local storage.
        
        Args:
            path: Optional path prefix
            recursive: List files recursively
            include_metadata: Include file metadata
            
        Returns:
            List of file paths or FileInfo objects
        """
        try:
            base = self._get_full_path(path or "")
            if not base.exists():
                return []
                
            pattern = "**/*" if recursive else "*"
            files = []
            
            for file_path in base.glob(pattern):
                if file_path.is_file():
                    rel_path = str(file_path.relative_to(self.base_path))
                    
                    if include_metadata:
                        _, metadata = await self.get(rel_path)
                        files.append(FileInfo(
                            path=rel_path,
                            metadata=metadata
                        ))
                    else:
                        files.append(rel_path)
                        
            return files
            
        except Exception as e:
            raise StorageError(f"Failed to list files: {str(e)}")
