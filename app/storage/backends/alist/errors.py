"""
AList storage errors.
"""
from typing import Optional, Dict, Any

class AListError(Exception):
    """Base AList error."""
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class AListAuthError(AListError):
    """AList authentication error."""
    pass

class AListConnectionError(AListError):
    """AList connection error."""
    pass

class AListNotFoundError(AListError):
    """AList resource not found error."""
    pass

class AListPermissionError(AListError):
    """AList permission error."""
    pass

class AListConfigError(AListError):
    """AList configuration error."""
    pass

class AListUploadError(AListError):
    """AList upload error."""
    pass

class AListDownloadError(AListError):
    """AList download error."""
    pass

class AListDeleteError(AListError):
    """AList delete error."""
    pass

class AListListError(AListError):
    """AList list error."""
    pass

def map_alist_error(
    status_code: int,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> AListError:
    """Map AList error based on status code.
    
    Args:
        status_code: HTTP status code
        message: Error message
        details: Additional error details
    
    Returns:
        Mapped AList error
    """
    error_map = {
        401: AListAuthError,
        403: AListPermissionError,
        404: AListNotFoundError,
        500: AListError,
    }
    error_class = error_map.get(status_code, AListError)
    return error_class(message, status_code, details)
