"""
Storage errors module.
Provides unified error handling for all storage backends.
"""
from typing import Dict, Any, Optional

class StorageError(Exception):
    """Base storage error."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize error.
        
        Args:
            message: Error message
            status_code: Optional HTTP status code
            details: Optional error details
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class StorageConfigError(StorageError):
    """Storage configuration error."""
    pass

class StorageAuthError(StorageError):
    """Storage authentication error."""
    pass

class StorageConnectionError(StorageError):
    """Storage connection error."""
    pass

class StorageNotFoundError(StorageError):
    """Storage resource not found error."""
    pass

class StoragePermissionError(StorageError):
    """Storage permission error."""
    pass

class StorageQuotaError(StorageError):
    """Storage quota exceeded error."""
    pass

class StorageFileError(StorageError):
    """Storage file operation error."""
    pass

class StorageValidationError(StorageError):
    """Storage validation error."""
    pass

def map_http_error(
    status_code: int,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> StorageError:
    """Map HTTP error to storage error.
    
    Args:
        status_code: HTTP status code
        message: Error message
        details: Optional error details
        
    Returns:
        Mapped storage error
    """
    error_map = {
        400: StorageValidationError,
        401: StorageAuthError,
        403: StoragePermissionError,
        404: StorageNotFoundError,
        413: StorageQuotaError,
        500: StorageError
    }
    
    error_class = error_map.get(status_code, StorageError)
    return error_class(message, status_code, details)
