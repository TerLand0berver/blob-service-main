"""
Response models for the Blob Service API.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class FileMetadata(BaseModel):
    """File metadata model."""
    filename: str = Field(..., description="Original filename")
    size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    created_at: datetime = Field(..., description="Creation timestamp")
    modified_at: datetime = Field(..., description="Last modification timestamp")
    hash: Optional[str] = Field(None, description="File hash")
    extension: str = Field(..., description="File extension")

class ImageMetadata(BaseModel):
    """Image metadata model."""
    width: int = Field(..., description="Image width")
    height: int = Field(..., description="Image height")
    format: str = Field(..., description="Image format")
    mode: str = Field(..., description="Color mode")
    has_alpha: bool = Field(..., description="Has alpha channel")
    dpi: Optional[tuple] = Field(None, description="DPI information")

class OCRResult(BaseModel):
    """OCR result model."""
    text: str = Field(..., description="Extracted text")
    confidence: float = Field(..., description="OCR confidence score")
    language: str = Field(..., description="Detected language")
    words: List[Dict[str, Any]] = Field(..., description="Word-level details")
    page: int = Field(..., description="Page number")

class ProcessingResult(BaseModel):
    """Processing result model."""
    file_id: str = Field(..., description="Unique file ID")
    file_url: Optional[str] = Field(None, description="File access URL")
    metadata: FileMetadata = Field(..., description="File metadata")
    content_type: str = Field(..., description="Content type")
    text_content: Optional[str] = Field(None, description="Extracted text content")
    images: Optional[List[Dict[str, Any]]] = Field(None, description="Extracted images")
    ocr_results: Optional[List[OCRResult]] = Field(None, description="OCR results")
    processing_time: float = Field(..., description="Processing time in seconds")
    error: Optional[str] = Field(None, description="Error message if any")

    class Config:
        schema_extra = {
            "example": {
                "file_id": "550e8400-e29b-41d4-a716-446655440000",
                "file_url": "http://example.com/files/doc.pdf",
                "metadata": {
                    "filename": "document.pdf",
                    "size": 1048576,
                    "mime_type": "application/pdf",
                    "created_at": "2023-12-01T12:00:00Z",
                    "modified_at": "2023-12-01T12:00:00Z",
                    "hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    "extension": "pdf"
                },
                "content_type": "document",
                "text_content": "Sample extracted text content...",
                "images": [
                    {
                        "url": "http://example.com/images/1.jpg",
                        "page": 1,
                        "metadata": {
                            "width": 800,
                            "height": 600,
                            "format": "JPEG",
                            "mode": "RGB",
                            "has_alpha": False,
                            "dpi": [72, 72]
                        }
                    }
                ],
                "ocr_results": [
                    {
                        "text": "Sample OCR text",
                        "confidence": 0.95,
                        "language": "eng",
                        "words": [
                            {
                                "text": "Sample",
                                "confidence": 0.98,
                                "bbox": [100, 100, 150, 120]
                            }
                        ],
                        "page": 1
                    }
                ],
                "processing_time": 1.23
            }
        }

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    request_id: str = Field(..., description="Request ID for tracking")
    timestamp: datetime = Field(..., description="Error timestamp")

    class Config:
        schema_extra = {
            "example": {
                "error": "File processing failed",
                "error_code": "PROC_ERR_001",
                "details": {
                    "reason": "File too large",
                    "limit": "10MB",
                    "actual": "15MB"
                },
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2023-12-01T12:00:00Z"
            }
        }
