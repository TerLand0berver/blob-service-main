"""
AList API client implementation.
"""
import os
import json
from typing import Optional, Dict, Any, List, BinaryIO
from datetime import datetime
import aiohttp
from ...exceptions import StorageError, StorageErrorCode

class AListClient:
    """AList API client."""
    
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        verify_ssl: bool = True
    ):
        """Initialize AList client.
        
        Args:
            base_url: AList server base URL
            username: AList username
            password: AList password
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.token = None
        self._session = None
    
    async def __aenter__(self):
        """Enter async context."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        await self.close()
    
    async def connect(self):
        """Connect to AList server and get token."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        
        try:
            # Login and get token
            async with self._session.post(
                f"{self.base_url}/api/auth/login",
                json={
                    "username": self.username,
                    "password": self.password
                },
                ssl=self.verify_ssl
            ) as resp:
                if resp.status != 200:
                    raise StorageError(
                        StorageErrorCode.AUTH_ERROR,
                        f"Failed to login to AList: {resp.status}"
                    )
                
                data = await resp.json()
                if not data.get("token"):
                    raise StorageError(
                        StorageErrorCode.AUTH_ERROR,
                        "No token in AList login response"
                    )
                
                self.token = data["token"]
                
        except aiohttp.ClientError as e:
            raise StorageError(
                StorageErrorCode.CONNECTION_ERROR,
                f"Failed to connect to AList: {str(e)}"
            )
    
    async def close(self):
        """Close client session."""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def _request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> Any:
        """Make API request.
        
        Args:
            method: HTTP method
            path: API path
            **kwargs: Request arguments
        
        Returns:
            Response data
        """
        if not self._session:
            await self.connect()
        
        headers = kwargs.pop('headers', {})
        if self.token:
            headers['Authorization'] = self.token
        
        try:
            async with self._session.request(
                method,
                f"{self.base_url}{path}",
                headers=headers,
                ssl=self.verify_ssl,
                **kwargs
            ) as resp:
                if resp.status == 401:
                    # Token expired, try to reconnect
                    await self.connect()
                    headers['Authorization'] = self.token
                    async with self._session.request(
                        method,
                        f"{self.base_url}{path}",
                        headers=headers,
                        ssl=self.verify_ssl,
                        **kwargs
                    ) as retry_resp:
                        return await self._handle_response(retry_resp)
                
                return await self._handle_response(resp)
                
        except aiohttp.ClientError as e:
            raise StorageError(
                StorageErrorCode.CONNECTION_ERROR,
                f"Failed to make AList request: {str(e)}"
            )
    
    async def _handle_response(self, resp: aiohttp.ClientResponse) -> Any:
        """Handle API response.
        
        Args:
            resp: Response object
        
        Returns:
            Response data
        """
        if resp.status >= 400:
            raise StorageError(
                StorageErrorCode.API_ERROR,
                f"AList API error: {resp.status}"
            )
        
        try:
            data = await resp.json()
        except ValueError:
            return await resp.read()
        
        if not data.get("code") == 200:
            raise StorageError(
                StorageErrorCode.API_ERROR,
                f"AList API error: {data.get('message')}"
            )
        
        return data.get("data")
    
    async def list_files(
        self,
        path: str,
        password: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List files in directory.
        
        Args:
            path: Directory path
            password: Directory password
        
        Returns:
            List of file metadata
        """
        data = {
            "path": path,
            "password": password or "",
            "page": 1,
            "per_page": 0,  # No pagination
            "refresh": False
        }
        
        return await self._request(
            "POST",
            "/api/fs/list",
            json=data
        )
    
    async def get_file(
        self,
        path: str,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get file info and download URL.
        
        Args:
            path: File path
            password: File password
        
        Returns:
            File metadata with download URL
        """
        data = {
            "path": path,
            "password": password or ""
        }
        
        return await self._request(
            "POST",
            "/api/fs/get",
            json=data
        )
    
    async def mkdir(
        self,
        path: str,
        password: Optional[str] = None
    ) -> None:
        """Create directory.
        
        Args:
            path: Directory path
            password: Directory password
        """
        data = {
            "path": path,
            "password": password or ""
        }
        
        await self._request(
            "POST",
            "/api/fs/mkdir",
            json=data
        )
    
    async def remove(
        self,
        path: str,
        password: Optional[str] = None
    ) -> None:
        """Remove file or directory.
        
        Args:
            path: File path
            password: File password
        """
        data = {
            "path": path,
            "password": password or ""
        }
        
        await self._request(
            "POST", 
            "/api/fs/remove",
            json=data
        )
    
    async def move(
        self,
        src_path: str,
        dst_path: str,
        password: Optional[str] = None
    ) -> None:
        """Move/rename file or directory.
        
        Args:
            src_path: Source path
            dst_path: Destination path
            password: File password
        """
        data = {
            "src_dir": os.path.dirname(src_path),
            "dst_dir": os.path.dirname(dst_path),
            "names": [os.path.basename(src_path)],
            "password": password or ""
        }
        
        await self._request(
            "POST",
            "/api/fs/move",
            json=data
        )
    
    async def put_file(
        self,
        path: str,
        file: BinaryIO,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload file.
        
        Args:
            path: File path
            file: File object
            password: File password
        
        Returns:
            File metadata
        """
        # Get upload info
        data = {
            "path": path,
            "size": file.seek(0, 2),  # Get file size
            "password": password or ""
        }
        file.seek(0)
        
        upload_info = await self._request(
            "POST",
            "/api/fs/put",
            json=data
        )
        
        # Upload file
        headers = {}
        if upload_info.get("header"):
            headers.update(upload_info["header"])
        
        async with self._session.put(
            upload_info["upload_url"],
            data=file,
            headers=headers,
            ssl=self.verify_ssl
        ) as resp:
            if resp.status >= 400:
                raise StorageError(
                    StorageErrorCode.UPLOAD_ERROR,
                    f"Failed to upload file to AList: {resp.status}"
                )
        
        return await self.get_file(path, password)
