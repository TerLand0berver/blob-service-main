"""
Base middleware interface.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict

class BaseMiddleware(ABC):
    """Base middleware interface."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize middleware with optional configuration."""
        self.config = config or {}
    
    @abstractmethod
    async def process_upload(self, file_data: bytes, metadata: Dict[str, Any]) -> tuple[bytes, Dict[str, Any]]:
        """Process file during upload.
        
        Args:
            file_data: Raw file data
            metadata: File metadata
            
        Returns:
            Tuple of (processed file data, updated metadata)
        """
        pass
    
    @abstractmethod
    async def process_download(self, file_data: bytes, metadata: Dict[str, Any]) -> tuple[bytes, Dict[str, Any]]:
        """Process file during download.
        
        Args:
            file_data: Raw file data
            metadata: File metadata
            
        Returns:
            Tuple of (processed file data, updated metadata)
        """
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate middleware configuration."""
        pass
