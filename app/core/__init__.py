"""
Core application components.
"""
from .errors import (
    AppError,
    ConfigError,
    AuthError,
    ValidationError,
    NotFoundError,
    PermissionError,
    RateLimitError,
    StorageError,
    ErrorCode,
    handle_error,
    register_error_handler,
)

__all__ = [
    'AppError',
    'ConfigError',
    'AuthError',
    'ValidationError',
    'NotFoundError',
    'PermissionError',
    'RateLimitError',
    'StorageError',
    'ErrorCode',
    'handle_error',
    'register_error_handler',
]
