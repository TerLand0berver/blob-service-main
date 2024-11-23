"""
Core schemas for the application.
"""
from typing import Optional, Any, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime

class ResponseBase(BaseModel):
    """Base response model"""
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class FileMetadata(BaseModel):
    """File metadata"""
    content_type: str
    size: int
    created_at: datetime
    updated_at: datetime
    checksum: str
    custom: Dict[str, Any] = Field(default_factory=dict)

class FileInfo(BaseModel):
    """File information"""
    id: str = Field(..., description="File ID")
    name: str = Field(..., description="File name")
    path: str = Field(..., description="Storage path")
    size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="Content type")
    url: str = Field(..., description="Access URL")
    metadata: FileMetadata = Field(..., description="File metadata")

class FileResponse(ResponseBase):
    """File operation response"""
    data: Optional[FileInfo] = None

class BatchResponse(ResponseBase):
    """Batch operation response"""
    data: Optional[List[FileInfo]] = None

class ProcessOptions(BaseModel):
    """File processing options"""
    extract_text: bool = Field(default=False, description="Extract text content")
    perform_ocr: bool = Field(default=False, description="Perform OCR")
    save_original: bool = Field(default=True, description="Save original file")
    custom_options: Dict[str, Any] = Field(default_factory=dict)

class BatchOptions(BaseModel):
    """Batch operation options"""
    process_options: Optional[ProcessOptions] = None
    parallel: bool = Field(default=True, description="Process in parallel")
    max_parallel: int = Field(default=5, description="Maximum parallel operations")

class StorageInfo(BaseModel):
    """Storage information"""
    backend: str = Field(..., description="Storage backend type")
    total_size: int = Field(..., description="Total storage size")
    used_size: int = Field(..., description="Used storage size")
    file_count: int = Field(..., description="Total file count")

class SystemStats(BaseModel):
    """System statistics"""
    uptime: float = Field(..., description="System uptime in seconds")
    cpu_usage: float = Field(..., description="CPU usage percentage")
    memory_usage: float = Field(..., description="Memory usage percentage")
    storage_info: StorageInfo = Field(..., description="Storage information")
