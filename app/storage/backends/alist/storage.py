"""
AList storage implementation.
"""
import os
import io
from typing import BinaryIO, Optional, Dict, Any, List, Tuple
from datetime import datetime
import aiohttp

from ...base import BaseStorage
from ...exceptions import StorageError, StorageErrorCode
from .client import AListClient

class AListStorage(BaseStorage):
    """AList storage implementation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize AList storage.
        
        Args:
            config: Storage configuration
        """
        super().__init__(config)
        
        # Get AList config
        alist_config = self.config.get('alist', {})
        
        # Required config
        self.base_url = alist_config.get('base_url')
        self.username = alist_config.get('username')
        self.password = alist_config.get('password')
        
        if not all([self.base_url, self.username, self.password]):
            raise StorageError(
                StorageErrorCode.CONFIG_ERROR,
                "Missing required AList configuration"
            )
        
        # Optional config
        self.root_dir = alist_config.get('root_dir', '')
        self.verify_ssl = alist_config.get('verify_ssl', True)
        self.file_password = alist_config.get('file_password')
        
        # Initialize client
        self.client = AListClient(
            self.base_url,
            self.username,
            self.password,
            self.verify_ssl
        )
    
    async def _get_full_path(self, path: str) -> str:
        """Get full path including root directory.
        
        Args:
            path: File path
        
        Returns:
            Full path
        """
        path = self._get_normalized_path(path)
        if self.root_dir:
            return f"{self.root_dir.rstrip('/')}/{path}"
        return path
    
    async def save(
        self,
        file: BinaryIO,
        path: str,
        metadata: Optional[Dict[str, Any]] = None,
        content_type: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Save file to AList storage."""
        try:
            # Get full path
            full_path = await self._get_full_path(path)
            
            # Create parent directory if needed
            parent_dir = os.path.dirname(full_path)
            if parent_dir:
                try:
                    await self.client.mkdir(
                        parent_dir,
                        self.file_password
                    )
                except StorageError as e:
                    if e.code != StorageErrorCode.API_ERROR:
                        raise
            
            # Get file size
            file_size = file.seek(0, 2)
            file.seek(0)
            
            # Upload file
            file_info = await self.client.put_file(
                full_path,
                file,
                self.file_password
            )
            
            # Update stats
            self._update_stats('upload', True, file_size)
            
            # Format metadata
            return {
                'path': path,
                'size': file_info['size'],
                'content_type': content_type or self._get_content_type(path),
                'created_at': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
        except StorageError:
            self._update_stats('upload', False)
            raise
        except Exception as e:
            self._update_stats('upload', False)
            raise StorageError(
                StorageErrorCode.UNKNOWN_ERROR,
                f"Failed to save file to AList: {str(e)}"
            )
    
    async def get(
        self,
        path: str,
        **kwargs
    ) -> Tuple[BinaryIO, Dict[str, Any]]:
        """Get file from AList storage."""
        try:
            # Get full path
            full_path = await self._get_full_path(path)
            
            # Get file info
            file_info = await self.client.get_file(
                full_path,
                self.file_password
            )
            
            # Download file
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    file_info['raw_url'],
                    ssl=self.verify_ssl
                ) as resp:
                    if resp.status >= 400:
                        raise StorageError(
                            StorageErrorCode.DOWNLOAD_ERROR,
                            f"Failed to download file from AList: {resp.status}"
                        )
                    
                    content = await resp.read()
            
            # Create file object
            file = io.BytesIO(content)
            
            # Format metadata
            metadata = {
                'path': path,
                'size': file_info['size'],
                'content_type': self._get_content_type(path),
                'created_at': datetime.fromtimestamp(
                    file_info['modified']
                ).isoformat(),
                'metadata': {}
            }
            
            # Update stats
            self._update_stats('download', True, file_info['size'])
            
            return file, metadata
            
        except StorageError:
            self._update_stats('download', False)
            raise
        except Exception as e:
            self._update_stats('download', False)
            raise StorageError(
                StorageErrorCode.UNKNOWN_ERROR,
                f"Failed to get file from AList: {str(e)}"
            )
    
    async def delete(
        self,
        path: str,
        **kwargs
    ) -> bool:
        """Delete file from AList storage."""
        try:
            # Get full path
            full_path = await self._get_full_path(path)
            
            try:
                # Delete file
                await self.client.remove(
                    full_path,
                    self.file_password
                )
                
                # Update stats
                self._update_stats('delete', True)
                
                return True
                
            except StorageError as e:
                if e.code == StorageErrorCode.NOT_FOUND:
                    return False
                raise
            
        except StorageError:
            self._update_stats('delete', False)
            raise
        except Exception as e:
            self._update_stats('delete', False)
            raise StorageError(
                StorageErrorCode.UNKNOWN_ERROR,
                f"Failed to delete file from AList: {str(e)}"
            )
    
    async def exists(
        self,
        path: str,
        **kwargs
    ) -> bool:
        """Check if file exists in AList storage."""
        try:
            # Get full path
            full_path = await self._get_full_path(path)
            
            try:
                await self.client.get_file(
                    full_path,
                    self.file_password
                )
                return True
            except StorageError as e:
                if e.code == StorageErrorCode.NOT_FOUND:
                    return False
                raise
            
        except StorageError as e:
            if e.code == StorageErrorCode.NOT_FOUND:
                return False
            raise
        except Exception as e:
            raise StorageError(
                StorageErrorCode.UNKNOWN_ERROR,
                f"Failed to check file existence in AList: {str(e)}"
            )
    
    async def get_url(
        self,
        path: str,
        expires: Optional[int] = None,
        **kwargs
    ) -> str:
        """Get URL for file in AList storage."""
        try:
            # Get full path
            full_path = await self._get_full_path(path)
            
            # Get file info
            file_info = await self.client.get_file(
                full_path,
                self.file_password
            )
            
            return file_info['raw_url']
            
        except StorageError:
            raise
        except Exception as e:
            raise StorageError(
                StorageErrorCode.UNKNOWN_ERROR,
                f"Failed to get URL from AList: {str(e)}"
            )
    
    async def list(
        self,
        path: str = "",
        recursive: bool = False,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """List files in AList storage."""
        try:
            # Get full path
            full_path = await self._get_full_path(path)
            
            # List files
            items = await self.client.list_files(
                full_path,
                self.file_password
            )
            
            # Format items
            files = []
            for item in items:
                if not item['is_dir']:
                    try:
                        rel_path = os.path.relpath(
                            item['name'],
                            self.root_dir
                        )
                        files.append({
                            'path': rel_path,
                            'size': item['size'],
                            'content_type': self._get_content_type(item['name']),
                            'created_at': datetime.fromtimestamp(
                                item['modified']
                            ).isoformat(),
                            'metadata': {}
                        })
                    except StorageError:
                        continue
            
            return files
            
        except StorageError:
            raise
        except Exception as e:
            raise StorageError(
                StorageErrorCode.UNKNOWN_ERROR,
                f"Failed to list files in AList: {str(e)}"
            )
    
    async def get_metadata(
        self,
        path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Get file metadata from AList storage."""
        try:
            # Get full path
            full_path = await self._get_full_path(path)
            
            # Get file info
            file_info = await self.client.get_file(
                full_path,
                self.file_password
            )
            
            return {
                'path': path,
                'size': file_info['size'],
                'content_type': self._get_content_type(path),
                'created_at': datetime.fromtimestamp(
                    file_info['modified']
                ).isoformat(),
                'metadata': {}
            }
            
        except StorageError:
            raise
        except Exception as e:
            raise StorageError(
                StorageErrorCode.UNKNOWN_ERROR,
                f"Failed to get metadata from AList: {str(e)}"
            )
    
    async def update_metadata(
        self,
        path: str,
        metadata: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Update file metadata in AList storage."""
        # AList doesn't support custom metadata
        return await self.get_metadata(path)
    
    async def copy(
        self,
        src_path: str,
        dst_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Copy file within AList storage."""
        try:
            # Get full paths
            src_full_path = await self._get_full_path(src_path)
            dst_full_path = await self._get_full_path(dst_path)
            
            # Create parent directory if needed
            parent_dir = os.path.dirname(dst_full_path)
            if parent_dir:
                try:
                    await self.client.mkdir(
                        parent_dir,
                        self.file_password
                    )
                except StorageError as e:
                    if e.code != StorageErrorCode.API_ERROR:
                        raise
            
            # Get source file
            file, metadata = await self.get(src_path)
            
            try:
                # Upload to destination
                return await self.save(
                    file,
                    dst_path,
                    metadata.get('metadata')
                )
            finally:
                file.close()
            
        except StorageError:
            raise
        except Exception as e:
            raise StorageError(
                StorageErrorCode.UNKNOWN_ERROR,
                f"Failed to copy file in AList: {str(e)}"
            )
    
    async def move(
        self,
        src_path: str,
        dst_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Move file within AList storage."""
        try:
            # Get full paths
            src_full_path = await self._get_full_path(src_path)
            dst_full_path = await self._get_full_path(dst_path)
            
            # Create parent directory if needed
            parent_dir = os.path.dirname(dst_full_path)
            if parent_dir:
                try:
                    await self.client.mkdir(
                        parent_dir,
                        self.file_password
                    )
                except StorageError as e:
                    if e.code != StorageErrorCode.API_ERROR:
                        raise
            
            # Move file
            await self.client.move(
                src_full_path,
                dst_full_path,
                self.file_password
            )
            
            # Get updated metadata
            return await self.get_metadata(dst_path)
            
        except StorageError:
            raise
        except Exception as e:
            raise StorageError(
                StorageErrorCode.UNKNOWN_ERROR,
                f"Failed to move file in AList: {str(e)}"
            )
