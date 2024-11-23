"""Custom exceptions for the blob service"""

class BlobServiceError(Exception):
    """Base exception for blob service"""
    pass

class ProcessingError(BlobServiceError):
    """Raised when there is an error processing a file"""
    pass

class StorageError(BlobServiceError):
    """Raised when there is an error storing a file"""
    pass

class OCRError(BlobServiceError):
    """Raised when there is an error performing OCR"""
    pass

class ConfigError(BlobServiceError):
    """Raised when there is an error in configuration"""
    pass

class AuthenticationError(BlobServiceError):
    """Raised when there is an authentication error"""
    pass

class ValidationError(BlobServiceError):
    """Raised when there is a validation error"""
    pass
