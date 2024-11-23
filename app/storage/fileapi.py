"""File API storage backend."""
import os
import io
import aiohttp
import logging
from datetime import datetime
from typing import BinaryIO, Optional, Dict, Any, List, Union, Tuple
import mimetypes
from urllib.parse import urljoin

from .base import StorageBackend, StorageError
from ..core.schemas import FileInfo, FileMetadata
from ..core.config import config

logger = logging.getLogger(__name__)

class FileAPIResponse:
    """File API response model."""
    
    def __init__(
        self,
        code: int,
        msg: str,
        sn: str,
        data: Dict[str, Any]
    ):
        """Initialize response.
        
        Args:
            code: Response code
            msg: Response message
            sn: Serial number
            data: Response data
        """
        self.code = code
        self.msg = msg
        self.sn = sn
        self.data = data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileAPIResponse":
        """Create response from dictionary.
        
        Args:
            data: Response dictionary
            
        Returns:
            FileAPIResponse object
        """
        return cls(
            code=data['code'],
            msg=data['msg'],
            sn=data['sn'],
            data=data['data']
        )
        
    def is_success(self) -> bool:
        """Check if response is successful.
        
        Returns:
            True if successful, False otherwise
        """
        return self.code == 0

class FileAPIStorageBackend(StorageBackend):
    """File API storage backend."""
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """Initialize File API storage.
        
        Args:
            api_url: API base URL
            api_key: API key
        """
        super().__init__()
        
        self.api_url = api_url or config.storage.fileapi_url
        self.api_key = api_key or config.storage.fileapi_key
        
        if not self.api_url:
            raise StorageError("File API URL not configured")
            
        # Initialize HTTP session
        self.session = aiohttp.ClientSession(
            headers={
                'Authorization': f'Bearer {self.api_key}' if self.api_key else None
            }
        )
        
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> FileAPIResponse:
        """Make HTTP request to File API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional arguments for request
            
        Returns:
            FileAPIResponse object
            
        Raises:
            StorageError: If request fails
        """
        try:
            url = urljoin(self.api_url, endpoint)
            async with self.session.request(method, url, **kwargs) as response:
                data = await response.json()
                api_response = FileAPIResponse.from_dict(data)
                
                if not api_response.is_success():
                    raise StorageError(
                        f"API request failed: {api_response.msg}"
                    )
                    
                return api_response
                
        except Exception as e:
            raise StorageError(f"Failed to make API request: {str(e)}")
            
    async def save(
        self,
        file: BinaryIO,
        path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FileInfo:
        """Save file using File API.
        
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
            # Create form data
            form = aiohttp.FormData()
            form.add_field(
                'file',
                file,
                filename=path or os.path.basename(getattr(file, 'name', '')),
                content_type=metadata.get('content_type') if metadata else None
            )
            
            # Upload file
            response = await self._make_request(
                'POST',
                '/upload',
                data=form
            )
            
            # Create metadata
            file_metadata = self._create_metadata(
                file,
                response.data.get('content_type', 'application/octet-stream'),
                metadata
            )
            
            # Update stats
            self._update_stats('upload', file_metadata.size)
            
            return FileInfo(
                path=response.data['filename'],
                metadata=file_metadata,
                url=response.data['url']
            )
            
        except Exception as e:
            self._update_stats('error')
            raise StorageError(f"Failed to save file: {str(e)}")
            
    async def get(
        self,
        path: str,
        include_metadata: bool = True
    ) -> Union[BinaryIO, Tuple[BinaryIO, FileMetadata]]:
        """Get file using File API.
        
        Args:
            path: Storage path
            include_metadata: Include metadata in response
            
        Returns:
            File content and optional metadata
            
        Raises:
            StorageError: If get fails
        """
        try:
            # Get file info
            response = await self._make_request(
                'GET',
                f'/info/{path}'
            )
            
            # Download file
            async with self.session.get(response.data['url']) as file_response:
                if file_response.status != 200:
                    raise StorageError("Failed to download file")
                    
                content = await file_response.read()
                file = io.BytesIO(content)
                
            if not include_metadata:
                return file
                
            # Create metadata
            metadata = FileMetadata(
                content_type=response.data.get('content_type', 'application/octet-stream'),
                size=len(content),
                created_at=datetime.fromisoformat(response.data['created_at']),
                updated_at=datetime.fromisoformat(response.data['updated_at']),
                checksum=response.data.get('checksum'),
                custom=response.data.get('metadata', {})
            )
            
            # Update stats
            self._update_stats('download', metadata.size)
            
            return file, metadata
            
        except Exception as e:
            self._update_stats('error')
            raise StorageError(f"Failed to get file: {str(e)}")
            
    async def delete(self, path: str) -> bool:
        """Delete file using File API.
        
        Args:
            path: Storage path
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            StorageError: If delete fails
        """
        try:
            await self._make_request(
                'DELETE',
                f'/delete/{path}'
            )
            self._update_stats('delete')
            return True
            
        except StorageError as e:
            if "not found" in str(e).lower():
                return False
            raise
            
    async def exists(self, path: str) -> bool:
        """Check if file exists using File API.
        
        Args:
            path: Storage path
            
        Returns:
            True if exists, False otherwise
        """
        try:
            await self._make_request(
                'GET',
                f'/info/{path}'
            )
            return True
        except StorageError:
            return False
            
    async def list_files(
        self,
        path: Optional[str] = None,
        recursive: bool = False,
        include_metadata: bool = False
    ) -> List[Union[str, FileInfo]]:
        """List files using File API.
        
        Args:
            path: Optional path prefix
            recursive: List files recursively
            include_metadata: Include file metadata
            
        Returns:
            List of file paths or FileInfo objects
        """
        try:
            # List files
            response = await self._make_request(
                'GET',
                '/list',
                params={
                    'prefix': path,
                    'recursive': recursive
                }
            )
            
            files = []
            for file_info in response.data['files']:
                if include_metadata:
                    metadata = FileMetadata(
                        content_type=file_info.get('content_type', 'application/octet-stream'),
                        size=file_info['size'],
                        created_at=datetime.fromisoformat(file_info['created_at']),
                        updated_at=datetime.fromisoformat(file_info['updated_at']),
                        checksum=file_info.get('checksum'),
                        custom=file_info.get('metadata', {})
                    )
                    files.append(FileInfo(
                        path=file_info['filename'],
                        metadata=metadata,
                        url=file_info['url']
                    ))
                else:
                    files.append(file_info['filename'])
                    
            return files
            
        except Exception as e:
            raise StorageError(f"Failed to list files: {str(e)}")
            
    async def close(self):
        """Close storage backend."""
        await self.session.close()
