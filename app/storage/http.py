"""
HTTP client for storage backends.
Provides a unified interface for making HTTP requests with authentication and error handling.
"""
import json
import asyncio
from typing import Dict, Any, Optional, Union
import aiohttp
from aiohttp import ClientResponse, ClientError
from urllib.parse import urljoin

from .config import StorageConfig, StorageEndpoint
from .errors import StorageError, StorageAuthError, StorageConnectionError

class StorageHttpClient:
    """HTTP client for storage backends."""
    
    def __init__(
        self,
        config: StorageConfig,
        session: Optional[aiohttp.ClientSession] = None
    ):
        """Initialize client.
        
        Args:
            config: Storage configuration
            session: Optional aiohttp session
        """
        self.config = config
        self._session = session
        self._auth_token: Optional[str] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        if not self._session:
            self._session = await self._create_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
            self._session = None
            
    async def _create_session(self) -> aiohttp.ClientSession:
        """Create new aiohttp session.
        
        Returns:
            aiohttp.ClientSession
        """
        return aiohttp.ClientSession(
            headers=self._get_default_headers(),
            timeout=aiohttp.ClientTimeout(
                total=self.config.endpoint.timeout
            )
        )
        
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default request headers.
        
        Returns:
            Default headers dict
        """
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'StorageClient/1.0'
        }
        
        if self._auth_token:
            headers['Authorization'] = f'Bearer {self._auth_token}'
            
        return headers
        
    def _get_endpoint_url(self, path: str) -> str:
        """Get full endpoint URL.
        
        Args:
            path: URL path
            
        Returns:
            Full URL
        """
        return urljoin(self.config.endpoint.url, path)
        
    async def _handle_response(
        self,
        response: ClientResponse,
        expected_status: Optional[int] = None
    ) -> Dict[str, Any]:
        """Handle API response.
        
        Args:
            response: aiohttp response
            expected_status: Expected HTTP status code
            
        Returns:
            Response data
            
        Raises:
            StorageError: On unexpected response
        """
        try:
            data = await response.json()
        except (json.JSONDecodeError, aiohttp.ContentTypeError):
            data = await response.text()
            
        if expected_status and response.status != expected_status:
            raise StorageError(
                f"Unexpected status code: {response.status}",
                status_code=response.status,
                details={'response': data}
            )
            
        return data
        
    async def request(
        self,
        method: str,
        path: str,
        expected_status: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request.
        
        Args:
            method: HTTP method
            path: URL path
            expected_status: Expected HTTP status code
            **kwargs: Additional request options
            
        Returns:
            Response data
            
        Raises:
            StorageError: On request failure
        """
        if not self._session:
            self._session = await self._create_session()
            
        url = self._get_endpoint_url(path)
        
        try:
            async with self._session.request(method, url, **kwargs) as response:
                return await self._handle_response(response, expected_status)
                
        except asyncio.TimeoutError:
            raise StorageConnectionError(
                f"Request timeout: {method} {url}"
            )
        except ClientError as e:
            raise StorageConnectionError(
                f"Request failed: {method} {url}",
                details={'error': str(e)}
            )
            
    async def get(
        self,
        path: str,
        expected_status: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make GET request.
        
        Args:
            path: URL path
            expected_status: Expected HTTP status code
            **kwargs: Additional request options
            
        Returns:
            Response data
        """
        return await self.request('GET', path, expected_status, **kwargs)
        
    async def post(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        expected_status: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make POST request.
        
        Args:
            path: URL path
            data: Request data
            expected_status: Expected HTTP status code
            **kwargs: Additional request options
            
        Returns:
            Response data
        """
        return await self.request(
            'POST',
            path,
            expected_status,
            json=data,
            **kwargs
        )
        
    async def put(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        expected_status: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make PUT request.
        
        Args:
            path: URL path
            data: Request data
            expected_status: Expected HTTP status code
            **kwargs: Additional request options
            
        Returns:
            Response data
        """
        return await self.request(
            'PUT',
            path,
            expected_status,
            json=data,
            **kwargs
        )
        
    async def delete(
        self,
        path: str,
        expected_status: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make DELETE request.
        
        Args:
            path: URL path
            expected_status: Expected HTTP status code
            **kwargs: Additional request options
            
        Returns:
            Response data
        """
        return await self.request(
            'DELETE',
            path,
            expected_status,
            **kwargs
        )
        
    def set_auth_token(self, token: str):
        """Set authentication token.
        
        Args:
            token: Auth token
        """
        self._auth_token = token
        
    def clear_auth_token(self):
        """Clear authentication token."""
        self._auth_token = None
