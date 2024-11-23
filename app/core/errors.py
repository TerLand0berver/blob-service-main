"""
Core error types and error handling utilities.
"""
from typing import Dict, Any, Optional, Type
from enum import Enum
import traceback
import logging

logger = logging.getLogger(__name__)

class ErrorCode(str, Enum):
    """Standard error codes."""
    UNKNOWN = "unknown"
    CONFIG = "config_error"
    AUTH = "auth_error"
    STORAGE = "storage_error"
    VALIDATION = "validation_error"
    NOT_FOUND = "not_found"
    PERMISSION = "permission_denied"
    RATE_LIMIT = "rate_limit"
    BAD_REQUEST = "bad_request"
    SERVER_ERROR = "server_error"
    PROCESSING_ERROR = "processing_error"
    OCR_ERROR = "ocr_error"

class AppError(Exception):
    """Base application error."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN,
        http_status: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize error.
        
        Args:
            message: Error message
            code: Error code
            http_status: HTTP status code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status
        self.details = details or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary.
        
        Returns:
            Dictionary representation of error
        """
        return {
            "code": self.code.value,
            "message": self.message,
            "details": self.details
        }
        
    @classmethod
    def from_exception(
        cls,
        exc: Exception,
        code: ErrorCode = ErrorCode.SERVER_ERROR,
        http_status: int = 500
    ) -> 'AppError':
        """Create AppError from exception.
        
        Args:
            exc: Source exception
            code: Error code
            http_status: HTTP status code
            
        Returns:
            AppError instance
        """
        # Get exception details
        exc_type = type(exc).__name__
        exc_tb = traceback.format_exc()
        
        # Log full traceback
        logger.error(f"Exception {exc_type}: {str(exc)}\n{exc_tb}")
        
        return cls(
            message=str(exc),
            code=code,
            http_status=http_status,
            details={
                "type": exc_type,
                "traceback": exc_tb
            }
        )

class ConfigError(AppError):
    """Configuration error."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=ErrorCode.CONFIG,
            http_status=500,
            details=details
        )

class AuthError(AppError):
    """Authentication/authorization error."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=ErrorCode.AUTH,
            http_status=401,
            details=details
        )

class ValidationError(AppError):
    """Data validation error."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 400
    ):
        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION,
            http_status=status_code,
            details=None
        )

class NotFoundError(AppError):
    """Resource not found error."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=ErrorCode.NOT_FOUND,
            http_status=404,
            details=details
        )

class PermissionError(AppError):
    """Permission denied error."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=ErrorCode.PERMISSION,
            http_status=403,
            details=details
        )

class RateLimitError(AppError):
    """Rate limit exceeded error."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=ErrorCode.RATE_LIMIT,
            http_status=429,
            details=details
        )

class StorageError(AppError):
    """Storage operation error."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500
    ):
        super().__init__(
            message=message,
            code=ErrorCode.STORAGE,
            http_status=status_code,
            details=None
        )

class ProcessingError(AppError):
    """File processing error."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 400
    ):
        super().__init__(
            message=message,
            code=ErrorCode.PROCESSING_ERROR,
            http_status=status_code,
            details=None
        )

class OCRError(AppError):
    """OCR processing error."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500
    ):
        super().__init__(
            message=message,
            code=ErrorCode.OCR_ERROR,
            http_status=status_code,
            details=None
        )

# Error handler registry
_error_handlers: Dict[Type[Exception], Type[AppError]] = {
    ConfigError: ConfigError,
    AuthError: AuthError,
    ValidationError: ValidationError,
    NotFoundError: NotFoundError,
    PermissionError: PermissionError,
    RateLimitError: RateLimitError,
    StorageError: StorageError,
    ProcessingError: ProcessingError,
    OCRError: OCRError,
}

def register_error_handler(
    exc_type: Type[Exception],
    handler: Type[AppError]
) -> None:
    """Register error handler.
    
    Args:
        exc_type: Exception type to handle
        handler: AppError subclass to handle the exception
    """
    _error_handlers[exc_type] = handler

def handle_error(exc: Exception) -> AppError:
    """Convert exception to AppError.
    
    Args:
        exc: Exception to handle
        
    Returns:
        AppError instance
    """
    # Get handler for exception type
    handler = _error_handlers.get(type(exc))
    
    if handler and isinstance(exc, AppError):
        # Already an AppError, return as is
        return exc
    elif handler:
        # Convert to AppError using registered handler
        return handler(str(exc))
    else:
        # Unknown error, wrap in AppError
        return AppError.from_exception(exc)
