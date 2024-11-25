"""Text extraction utilities and configuration management"""

from typing import List, Dict, Optional
import logging
from app.config import config
from app.utils.exceptions import ProcessingError

logger = logging.getLogger(__name__)

class TextExtractionConfig:
    """Manages text extraction configuration and validation"""
    
    def __init__(self):
        self.config = config.TEXT_EXTRACTION
        
    @property
    def pdf_config(self) -> Dict:
        """Get PDF extraction configuration"""
        return self.config.get("pdf", {
            "extract_images": True,
            "ocr_images": True,
            "max_pages": 1000
        })
    
    @property
    def spreadsheet_config(self) -> Dict:
        """Get spreadsheet extraction configuration"""
        return self.config.get("spreadsheet", {
            "max_rows": 10000,
            "max_cols": 1000,
            "supported_formats": ["xlsx", "csv"]
        })
    
    @property
    def document_config(self) -> Dict:
        """Get document extraction configuration"""
        return self.config.get("document", {
            "supported_formats": ["docx", "txt", "pdf"],
            "max_size_mb": 50
        })
    
    @property
    def encodings(self) -> List[str]:
        """Get supported text encodings"""
        return self.config.get("encodings", [
            "utf-8", "ascii", "iso-8859-1", "cp1252", "utf-16"
        ])
    
    def validate_pdf_extraction(self, page_count: int) -> None:
        """Validate PDF extraction parameters"""
        if page_count > self.pdf_config["max_pages"]:
            raise ProcessingError(
                f"PDF exceeds maximum page limit of {self.pdf_config['max_pages']}"
            )
    
    def validate_spreadsheet_extraction(self, rows: int, cols: int, format: str) -> None:
        """Validate spreadsheet extraction parameters"""
        if format not in self.spreadsheet_config["supported_formats"]:
            raise ProcessingError(f"Unsupported spreadsheet format: {format}")
        
        if rows > self.spreadsheet_config["max_rows"]:
            raise ProcessingError(
                f"Spreadsheet exceeds maximum row limit of {self.spreadsheet_config['max_rows']}"
            )
            
        if cols > self.spreadsheet_config["max_cols"]:
            raise ProcessingError(
                f"Spreadsheet exceeds maximum column limit of {self.spreadsheet_config['max_cols']}"
            )
    
    def validate_document_extraction(self, size_mb: float, format: str) -> None:
        """Validate document extraction parameters"""
        if format not in self.document_config["supported_formats"]:
            raise ProcessingError(f"Unsupported document format: {format}")
            
        if size_mb > self.document_config["max_size_mb"]:
            raise ProcessingError(
                f"Document exceeds maximum size limit of {self.document_config['max_size_mb']}MB"
            )

# Create global text extraction config instance
text_config = TextExtractionConfig()
