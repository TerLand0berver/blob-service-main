"""
Base parser interface.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, BinaryIO

class ParserError(Exception):
    """Base exception for parser-related errors."""
    pass

class BaseParser(ABC):
    """Base parser interface."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize parser with optional configuration."""
        self.config = config or {}
    
    @abstractmethod
    async def can_handle(self, content_type: str, file_extension: str) -> bool:
        """Check if parser can handle this file type."""
        pass
    
    @abstractmethod
    async def parse(self, file_data: bytes, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse file and extract metadata.
        
        Args:
            file_data: Raw file data
            metadata: Existing metadata
            
        Returns:
            Updated metadata dictionary
        """
        pass
    
    @abstractmethod
    async def validate(self, file_data: bytes, metadata: Dict[str, Any]) -> bool:
        """Validate file format."""
        pass
    
    @abstractmethod
    async def optimize(self, file_data: bytes, metadata: Dict[str, Any]) -> tuple[bytes, Dict[str, Any]]:
        """Optimize file format if possible."""
        pass
