"""
Request models for the Blob Service API.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
import mimetypes

class ProcessingMode(str, Enum):
    """File processing mode."""
    DEFAULT = "default"  # 返回处理后的文本内容
    SAVE_ALL = "save_all"  # 返回文件/图片链接
    OCR = "ocr"  # 返回OCR文本和提取的图片

class FileProcessRequest(BaseModel):
    """File processing request model."""
    mode: ProcessingMode = Field(
        default=ProcessingMode.DEFAULT,
        description="Processing mode"
    )
    enable_ocr: bool = Field(
        default=False,
        description="Enable OCR processing"
    )
    enable_vision: bool = Field(
        default=True,
        description="Enable vision processing"
    )
    save_all: bool = Field(
        default=False,
        description="Save all extracted content"
    )
    max_file_size: Optional[int] = Field(
        default=None,
        description="Maximum file size in bytes"
    )
    allowed_types: Optional[List[str]] = Field(
        default=None,
        description="List of allowed file types"
    )
    extract_metadata: bool = Field(
        default=True,
        description="Extract file metadata"
    )
    extract_text: bool = Field(
        default=True,
        description="Extract text content"
    )
    extract_images: bool = Field(
        default=True,
        description="Extract images from documents"
    )
    image_format: str = Field(
        default="jpg",
        description="Output image format"
    )
    image_quality: int = Field(
        default=85,
        description="Output image quality (1-100)"
    )
    max_image_size: int = Field(
        default=2048,
        description="Maximum image dimension"
    )
    ocr_languages: Optional[List[str]] = Field(
        default=None,
        description="OCR languages to use"
    )
    ocr_timeout: int = Field(
        default=30,
        description="OCR timeout in seconds"
    )

    @validator('image_quality')
    def validate_image_quality(cls, v):
        """Validate image quality."""
        if not 1 <= v <= 100:
            raise ValueError("Image quality must be between 1 and 100")
        return v

    @validator('max_image_size')
    def validate_max_image_size(cls, v):
        """Validate maximum image size."""
        if v < 16 or v > 8192:
            raise ValueError("Max image size must be between 16 and 8192")
        return v

    @validator('allowed_types')
    def validate_allowed_types(cls, v):
        """Validate allowed file types."""
        if v is not None:
            valid_types = []
            for t in v:
                if t.startswith('.'):
                    t = t[1:]
                mime_type = mimetypes.guess_type(f"test.{t}")[0]
                if mime_type is None:
                    raise ValueError(f"Invalid file type: {t}")
                valid_types.append(t.lower())
            return valid_types
        return v

    @validator('ocr_languages')
    def validate_ocr_languages(cls, v):
        """Validate OCR languages."""
        if v is not None:
            valid_langs = {'eng', 'chi_sim', 'chi_tra', 'jpn', 'kor', 'rus'}
            invalid_langs = set(v) - valid_langs
            if invalid_langs:
                raise ValueError(f"Invalid OCR languages: {invalid_langs}")
        return v

    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "mode": "default",
                "enable_ocr": False,
                "enable_vision": True,
                "save_all": False,
                "max_file_size": 10485760,
                "allowed_types": ["pdf", "doc", "docx", "txt"],
                "extract_metadata": True,
                "extract_text": True,
                "extract_images": True,
                "image_format": "jpg",
                "image_quality": 85,
                "max_image_size": 2048,
                "ocr_languages": ["eng"],
                "ocr_timeout": 30
            }
        }
