"""Text extraction implementations for different file types"""

import io
import os
import logging
from typing import Optional, Dict, Any
import fitz  # PyMuPDF
import pandas as pd
import docx
import chardet
from app.utils.exceptions import ProcessingError
from app.utils.text_utils import text_config

logger = logging.getLogger(__name__)

class BaseExtractor:
    """Base class for text extractors"""
    
    def __init__(self, content: bytes, filename: str):
        self.content = content
        self.filename = filename
        self.config = text_config
        
    async def extract(self) -> str:
        """Extract text from content"""
        raise NotImplementedError
        
    def _detect_encoding(self, sample: bytes) -> str:
        """Detect text encoding"""
        result = chardet.detect(sample)
        return result['encoding'] or self.config.general['fallback_encoding']

class PDFExtractor(BaseExtractor):
    """PDF file text extractor"""
    
    async def extract(self) -> str:
        try:
            with fitz.open(stream=self.content, filetype="pdf") as doc:
                # Validate page count
                self.config.validate_pdf_extraction(len(doc))
                
                # Extract text from each page
                text_parts = []
                for page in doc:
                    text = page.get_text()
                    text_parts.append(text)
                
                return '\n\n'.join(text_parts)
                
        except Exception as e:
            logger.error(f"Error extracting PDF content: {str(e)}")
            raise ProcessingError(f"Failed to extract PDF content: {str(e)}")

class SpreadsheetExtractor(BaseExtractor):
    """Spreadsheet file text extractor"""
    
    async def extract(self) -> str:
        try:
            # Try different formats
            try:
                # Try Excel format
                df = pd.read_excel(io.BytesIO(self.content), sheet_name=None)
                text_parts = []
                for name, sheet in df.items():
                    self.config.validate_spreadsheet_extraction(
                        len(sheet), len(sheet.columns), 'xlsx'
                    )
                    text_parts.append(f"Sheet: {name}")
                    text_parts.append(sheet.to_string())
                return '\n\n'.join(text_parts)
            except Exception:
                try:
                    # Try CSV format
                    df = pd.read_csv(io.BytesIO(self.content))
                    self.config.validate_spreadsheet_extraction(
                        len(df), len(df.columns), 'csv'
                    )
                    return df.to_string()
                except Exception:
                    raise ProcessingError("Unsupported spreadsheet format")
            
        except Exception as e:
            logger.error(f"Error extracting spreadsheet content: {str(e)}")
            raise ProcessingError(f"Failed to extract spreadsheet content: {str(e)}")

class DocumentExtractor(BaseExtractor):
    """Document file text extractor"""
    
    async def extract(self) -> str:
        try:
            # Check file size
            size_mb = len(self.content) / (1024 * 1024)
            ext = os.path.splitext(self.filename)[1].lower()
            self.config.validate_document_extraction(size_mb, ext)
            
            if ext in ['.docx', '.doc']:
                doc = docx.Document(io.BytesIO(self.content))
                return '\n'.join(para.text for para in doc.paragraphs)
                
            elif ext in ['.txt', '.rtf']:
                encoding = self._detect_encoding(self.content[:4096])
                return self.content.decode(encoding)
            
            raise ProcessingError(f"Unsupported document format: {ext}")
            
        except Exception as e:
            logger.error(f"Error extracting document content: {str(e)}")
            raise ProcessingError(f"Failed to extract document content: {str(e)}")

class CodeExtractor(BaseExtractor):
    """Source code file text extractor"""
    
    async def extract(self) -> str:
        try:
            # Check file size
            size_mb = len(self.content) / (1024 * 1024)
            ext = os.path.splitext(self.filename)[1].lower()
            
            if ext[1:] not in self.config.code_config['supported_formats']:
                raise ProcessingError(f"Unsupported code format: {ext}")
                
            if size_mb > self.config.code_config['max_size_mb']:
                raise ProcessingError(
                    f"File exceeds maximum size of {self.config.code_config['max_size_mb']}MB"
                )
            
            # Detect encoding and extract text
            encoding = self._detect_encoding(self.content[:4096])
            return self.content.decode(encoding)
            
        except Exception as e:
            logger.error(f"Error extracting code content: {str(e)}")
            raise ProcessingError(f"Failed to extract code content: {str(e)}")

# Factory function to create appropriate extractor
def create_extractor(content: bytes, filename: str) -> BaseExtractor:
    """Create appropriate extractor based on file extension"""
    ext = os.path.splitext(filename)[1].lower()
    
    if ext in ['.pdf']:
        return PDFExtractor(content, filename)
    elif ext in ['.xlsx', '.xls', '.csv', '.tsv']:
        return SpreadsheetExtractor(content, filename)
    elif ext in ['.doc', '.docx', '.txt', '.rtf']:
        return DocumentExtractor(content, filename)
    elif ext[1:] in text_config.code_config['supported_formats']:
        return CodeExtractor(content, filename)
    else:
        raise ProcessingError(f"Unsupported file format: {ext}")

async def extract_text(content: bytes, filename: str) -> str:
    """Extract text from file content"""
    try:
        extractor = create_extractor(content, filename)
        return await extractor.extract()
    except Exception as e:
        logger.error(f"Error in text extraction: {str(e)}")
        raise ProcessingError(f"Text extraction failed: {str(e)}")
