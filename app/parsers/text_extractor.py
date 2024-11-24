"""Text extraction utilities for different file types"""

import io
import fitz  # PyMuPDF
from typing import Optional
import logging
import os
import tempfile
from app.utils.exceptions import ProcessingError

logger = logging.getLogger(__name__)

async def extract_text_with_encoding(content: bytes) -> Optional[str]:
    """Try to extract text with different encodings"""
    encodings = ['utf-8', 'ascii', 'iso-8859-1', 'cp1252', 'utf-16']
    
    for encoding in encodings:
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    
    return None

async def extract_doc_text(content: bytes) -> Optional[str]:
    """Extract text from Word document"""
    try:
        # 使用python-docx处理.docx文件
        if content.startswith(b'PK\x03\x04'):  # .docx file signature
            from docx import Document
            doc = Document(io.BytesIO(content))
            return '\n'.join(paragraph.text for paragraph in doc.paragraphs)
        
        # 使用antiword处理.doc文件
        elif content.startswith(b'\xD0\xCF\x11\xE0'):  # .doc file signature
            import subprocess
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                temp.write(content)
                temp.flush()
                try:
                    result = subprocess.run(['antiword', temp.name], 
                                         capture_output=True, 
                                         text=True)
                    if result.returncode == 0:
                        return result.stdout
                finally:
                    os.unlink(temp.name)
        
        return None
        
    except Exception as e:
        logger.error(f"Error extracting document text: {str(e)}")
        return None

async def extract_spreadsheet_text(content: bytes) -> Optional[str]:
    """Extract text from spreadsheet content"""
    try:
        # Try CSV format with different encodings
        for encoding in ['utf-8', 'gbk', 'latin1']:
            try:
                text = content.decode(encoding)
                # Simple CSV parsing
                lines = text.split('\n')
                if lines:
                    return '\n'.join(lines)
            except UnicodeDecodeError:
                continue
            except Exception:
                pass
        
        # If CSV parsing fails, return None
        return None
        
    except Exception as e:
        logger.error(f"Error extracting spreadsheet text: {str(e)}")
        return None

async def extract_pdf_text(content: bytes) -> Optional[str]:
    """Extract text from PDF content"""
    try:
        with fitz.open(stream=content, filetype="pdf") as doc:
            text = []
            for page in doc:
                text.append(page.get_text())
            return "\n\n".join(text)
    except Exception as e:
        logger.error(f"Error extracting PDF text: {str(e)}")
        return None
