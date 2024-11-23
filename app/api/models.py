"""
API models for request and response.
"""
from typing import TypeVar, Generic, Optional, Any, Dict, List
from pydantic import BaseModel, Field
from enum import Enum

# Generic type for response data
DataT = TypeVar('DataT')

class ResponseFormat(str, Enum):
    """Response format types."""
    JSON = "json"
    TEXT = "text"
    BINARY = "binary"

class StorageType(str, Enum):
    """Storage backend types."""
    LOCAL = "local"
    S3 = "s3"
    ALIST = "alist"

class BaseResponse(BaseModel, Generic[DataT]):
    """Base response model."""
    code: int = Field(0, description="Response code")
    msg: str = Field("success", description="Response message")
    data: Optional[DataT] = Field(None, description="Response data")

class ErrorResponse(BaseResponse[Dict[str, Any]]):
    """Error response model."""
    code: int = Field(1, description="Error code")
    msg: str = Field("error", description="Error message")
    data: Optional[Dict[str, Any]] = Field(None, description="Error details")

class FileInfo(BaseModel):
    """File information."""
    filename: str = Field(..., description="Original filename")
    size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="File content type")
    url: Optional[str] = Field(None, description="File URL")
    is_image: bool = Field(False, description="Whether file is an image")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="File metadata")

class FileUploadResponse(BaseResponse[FileInfo]):
    """File upload response."""
    pass

class FileListResponse(BaseResponse[List[FileInfo]]):
    """File list response."""
    pass

class FileDeleteResponse(BaseResponse[None]):
    """File delete response."""
    pass

class StorageConfig(BaseModel):
    """Storage configuration."""
    type: StorageType = Field(..., description="Storage backend type")
    path: Optional[str] = Field(None, description="Storage path")
    domain: Optional[str] = Field(None, description="Storage domain")
    access_key: Optional[str] = Field(None, description="Storage access key")
    secret_key: Optional[str] = Field(None, description="Storage secret key")
    bucket: Optional[str] = Field(None, description="Storage bucket")
    endpoint: Optional[str] = Field(None, description="Storage endpoint")
    region: Optional[str] = Field(None, description="Storage region")

class StorageConfigResponse(BaseResponse[StorageConfig]):
    """Storage configuration response."""
    pass

class HealthStatus(str, Enum):
    """Health check status."""
    OK = "ok"
    ERROR = "error"

class HealthInfo(BaseModel):
    """Health check information."""
    status: HealthStatus = Field(..., description="Health status")
    version: str = Field(..., description="Application version")
    storage: Dict[str, Any] = Field(..., description="Storage status")
    uptime: float = Field(..., description="Uptime in seconds")

class HealthResponse(BaseResponse[HealthInfo]):
    """Health check response."""
    pass
