"""
Document parser implementation.
"""
import io
from typing import Dict, Any, Optional
import magic
import docx
import PyPDF2
import openpyxl
from odf import text, teletype
from odf.opendocument import load

from .base import BaseParser, ParserError

class DocumentParser(BaseParser):
    """Parser for document files (DOCX, PDF, XLSX, ODT, etc)."""
    
    SUPPORTED_TYPES = {
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.oasis.opendocument.text',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/pdf'
    }
    
    SUPPORTED_EXTENSIONS = {
        '.docx', '.odt', '.xlsx', '.pdf'
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize document parser."""
        super().__init__(config)
        self.extract_text = self.config.get('extract_text', True)
        self.max_text_length = self.config.get('max_text_length', 10000)
        self.extract_metadata = self.config.get('extract_metadata', True)
    
    async def can_handle(self, content_type: str, file_extension: str) -> bool:
        """Check if parser can handle this file type."""
        return (content_type.lower() in self.SUPPORTED_TYPES or
                file_extension.lower() in self.SUPPORTED_EXTENSIONS)
    
    async def parse(self, file_data: bytes, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse document and extract metadata."""
        try:
            temp_file = io.BytesIO(file_data)
            mime = magic.Magic(mime=True)
            content_type = mime.from_buffer(file_data)
            
            if 'wordprocessingml.document' in content_type:  # DOCX
                return await self._parse_docx(temp_file, metadata)
            elif 'opendocument.text' in content_type:  # ODT
                return await self._parse_odt(temp_file, metadata)
            elif 'spreadsheetml.sheet' in content_type:  # XLSX
                return await self._parse_xlsx(temp_file, metadata)
            elif 'pdf' in content_type:  # PDF
                return await self._parse_pdf(temp_file, metadata)
            else:
                raise ParserError(f"Unsupported document type: {content_type}")
        except Exception as e:
            raise ParserError(f"Failed to parse document: {e}")
    
    async def validate(self, file_data: bytes, metadata: Dict[str, Any]) -> bool:
        """Validate document format."""
        try:
            mime = magic.Magic(mime=True)
            content_type = mime.from_buffer(file_data)
            
            if content_type not in self.SUPPORTED_TYPES:
                return False
            
            # Try to open the document based on type
            temp_file = io.BytesIO(file_data)
            if 'wordprocessingml.document' in content_type:
                docx.Document(temp_file)
            elif 'opendocument.text' in content_type:
                load(temp_file)
            elif 'spreadsheetml.sheet' in content_type:
                openpyxl.load_workbook(temp_file, read_only=True)
            elif 'pdf' in content_type:
                PyPDF2.PdfReader(temp_file)
            return True
        except Exception:
            return False
    
    async def optimize(self, file_data: bytes, metadata: Dict[str, Any]) -> tuple[bytes, Dict[str, Any]]:
        """Optimize document file."""
        # Document optimization is not implemented yet
        # Could implement in future:
        # - Image compression within documents
        # - Remove unused styles
        # - Compress embedded media
        return file_data, metadata
    
    async def _parse_docx(self, file_obj: io.BytesIO, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse DOCX document."""
        doc = docx.Document(file_obj)
        
        if self.extract_metadata:
            core_props = doc.core_properties
            metadata.update({
                'author': core_props.author,
                'created': core_props.created,
                'modified': core_props.modified,
                'title': core_props.title,
                'subject': core_props.subject,
                'keywords': core_props.keywords,
                'language': core_props.language,
                'format': 'DOCX'
            })
        
        if self.extract_text:
            text = '\n'.join(paragraph.text for paragraph in doc.paragraphs)
            if len(text) > self.max_text_length:
                text = text[:self.max_text_length] + "..."
            metadata['text_preview'] = text
        
        metadata['paragraphs'] = len(doc.paragraphs)
        metadata['sections'] = len(doc.sections)
        
        return metadata
    
    async def _parse_odt(self, file_obj: io.BytesIO, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ODT document."""
        doc = load(file_obj)
        
        if self.extract_metadata:
            metadata.update({
                'title': doc.meta.get_by_name('title'),
                'subject': doc.meta.get_by_name('subject'),
                'keywords': doc.meta.get_by_name('keyword'),
                'creator': doc.meta.get_by_name('creator'),
                'creation_date': doc.meta.get_by_name('creation-date'),
                'format': 'ODT'
            })
        
        if self.extract_text:
            text = []
            for element in doc.getElementsByType(text.P):
                text.append(teletype.extractText(element))
            text = '\n'.join(text)
            
            if len(text) > self.max_text_length:
                text = text[:self.max_text_length] + "..."
            metadata['text_preview'] = text
        
        return metadata
    
    async def _parse_xlsx(self, file_obj: io.BytesIO, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse XLSX document."""
        wb = openpyxl.load_workbook(file_obj, read_only=True)
        
        if self.extract_metadata:
            metadata.update({
                'creator': wb.properties.creator,
                'created': wb.properties.created,
                'modified': wb.properties.modified,
                'title': wb.properties.title,
                'subject': wb.properties.subject,
                'keywords': wb.properties.keywords,
                'format': 'XLSX'
            })
        
        metadata['sheets'] = len(wb.sheetnames)
        metadata['sheet_names'] = wb.sheetnames
        
        if self.extract_text:
            text = []
            for sheet in wb.sheetnames:
                ws = wb[sheet]
                for row in ws.iter_rows(max_row=100):  # Limit to first 100 rows
                    text.append(' '.join(str(cell.value or '') for cell in row))
                    if len('\n'.join(text)) > self.max_text_length:
                        break
            
            text = '\n'.join(text)
            if len(text) > self.max_text_length:
                text = text[:self.max_text_length] + "..."
            metadata['text_preview'] = text
        
        wb.close()
        return metadata
    
    async def _parse_pdf(self, file_obj: io.BytesIO, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse PDF document."""
        pdf = PyPDF2.PdfReader(file_obj)
        
        if self.extract_metadata:
            info = pdf.metadata
            if info:
                metadata.update({
                    'title': info.get('/Title', ''),
                    'author': info.get('/Author', ''),
                    'subject': info.get('/Subject', ''),
                    'keywords': info.get('/Keywords', ''),
                    'creator': info.get('/Creator', ''),
                    'producer': info.get('/Producer', ''),
                    'creation_date': info.get('/CreationDate', ''),
                    'modification_date': info.get('/ModDate', ''),
                    'format': 'PDF'
                })
        
        metadata['pages'] = len(pdf.pages)
        
        if self.extract_text:
            text = []
            for page in pdf.pages:
                text.append(page.extract_text())
                if len('\n'.join(text)) > self.max_text_length:
                    break
            
            text = '\n'.join(text)
            if len(text) > self.max_text_length:
                text = text[:self.max_text_length] + "..."
            metadata['text_preview'] = text
        
        return metadata
