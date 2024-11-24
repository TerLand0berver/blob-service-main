"""
Document parser implementation.
"""
import io
from typing import Dict, Any, Optional
import magic
import docx
import PyPDF2
import csv
import openpyxl
from pygments import highlight
from pygments.lexers import get_lexer_for_filename, TextLexer
from pygments.formatters import TextFormatter

from .base import BaseParser, ParserError

class DocumentParser(BaseParser):
    """Parser for document files (DOCX, PDF, CSV, XLSX, and code files)."""
    
    SUPPORTED_TYPES = {
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/pdf',
        'text/csv',
        'text/plain',
        'text/x-python',
        'text/x-sh',
        'text/x-bat',
        'application/x-shellscript'
    }
    
    SUPPORTED_EXTENSIONS = {
        '.docx', '.xlsx', '.pdf', '.csv', '.txt',
        '.py', '.sh', '.bash', '.bat', '.cmd',
        '.js', '.ts', '.java', '.c', '.cpp', '.h',
        '.hpp', '.cs', '.go', '.rs', '.php', '.rb',
        '.pl', '.sql', '.yaml', '.yml', '.json',
        '.xml', '.html', '.css', '.md'
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize document parser."""
        super().__init__(config)
        self.max_excel_rows = self.config.get('max_excel_rows', 1000)
        self.max_code_size = self.config.get('max_code_size', 1024 * 1024)  # 1MB

    async def can_handle(self, content_type: str, file_extension: str) -> bool:
        """Check if parser can handle this file type."""
        return (content_type.lower() in self.SUPPORTED_TYPES or
                file_extension.lower() in self.SUPPORTED_EXTENSIONS)

    async def validate(self, file_data: bytes, metadata: Dict[str, Any]) -> bool:
        """Validate document format."""
        try:
            mime = magic.Magic(mime=True)
            content_type = mime.from_buffer(file_data)
            
            # For code files, check size limit
            if self._is_code_file(content_type, metadata.get('filename', '')):
                return len(file_data) <= self.max_code_size
            
            return content_type in self.SUPPORTED_TYPES or self._is_code_file(content_type, metadata.get('filename', ''))
        except Exception:
            return False

    def _is_code_file(self, content_type: str, filename: str) -> bool:
        """Check if file is a code file."""
        if content_type.startswith('text/'):
            ext = filename.lower().split('.')[-1] if '.' in filename else ''
            return ext in [x[1:] for x in self.SUPPORTED_EXTENSIONS if x.startswith('.')]
        return False

    async def parse(self, file_data: bytes, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse document and extract text."""
        try:
            mime = magic.Magic(mime=True)
            content_type = mime.from_buffer(file_data)
            filename = metadata.get('filename', '')
            text_content = ""

            if content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                doc = docx.Document(io.BytesIO(file_data))
                text_content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
            elif content_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                wb = openpyxl.load_workbook(io.BytesIO(file_data), read_only=True)
                texts = []
                for sheet in wb.sheetnames:
                    ws = wb[sheet]
                    sheet_texts = []
                    for idx, row in enumerate(ws.rows):
                        if idx >= self.max_excel_rows:
                            break
                        row_text = [str(cell.value) if cell.value is not None else '' for cell in row]
                        sheet_texts.append('\t'.join(row_text))
                    texts.append(f"Sheet: {sheet}\n" + '\n'.join(sheet_texts))
                text_content = '\n\n'.join(texts)
                wb.close()
            
            elif content_type == 'application/pdf':
                pdf = PyPDF2.PdfReader(io.BytesIO(file_data))
                text_content = "\n".join([page.extract_text() for page in pdf.pages])
            
            elif content_type == 'text/csv':
                decoded_content = file_data.decode('utf-8', errors='ignore')
                csv_reader = csv.reader(io.StringIO(decoded_content))
                text_content = "\n".join([",".join(row) for row in csv_reader])
            
            elif self._is_code_file(content_type, filename):
                # 使用Pygments进行代码解析
                try:
                    lexer = get_lexer_for_filename(filename)
                except Exception:
                    lexer = TextLexer()
                
                formatter = TextFormatter()
                text_content = highlight(file_data.decode('utf-8', errors='ignore'), lexer, formatter)
            
            else:  # 普通文本文件
                text_content = file_data.decode('utf-8', errors='ignore')

            metadata.update({
                'content_type': content_type,
                'text_content': text_content,
                'size': len(file_data),
                'is_code': self._is_code_file(content_type, filename)
            })
            
            return metadata
        except Exception as e:
            raise ParserError(f"Failed to parse document: {e}")

    async def optimize(self, file_data: bytes, metadata: Dict[str, Any]) -> tuple[bytes, Dict[str, Any]]:
        """No optimization needed for documents."""
        return file_data, metadata
