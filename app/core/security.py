import re
import magic
from typing import Optional, Tuple, Dict, Any, List
from fastapi import UploadFile
from fastapi.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class SecurityValidator:
    """Security validation utilities."""
    
    MIN_PASSWORD_LENGTH = 12
    PASSWORD_PATTERN = re.compile(
        r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]'
    )
    
    ALLOWED_MIME_TYPES = {
        # Images
        'image/jpeg': ['.jpg', '.jpeg'],
        'image/png': ['.png'],
        'image/gif': ['.gif'],
        'image/webp': ['.webp'],
        # Documents
        'application/pdf': ['.pdf'],
        'application/msword': ['.doc'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
        'text/plain': ['.txt'],
        # Others
        'application/json': ['.json'],
        'text/csv': ['.csv'],
        'application/vnd.ms-excel': ['.xls'],
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
    }
    
    def __init__(self):
        self.mime = magic.Magic(mime=True)
        
    @classmethod
    def validate_password(cls, password: str) -> Tuple[bool, str]:
        """
        Validate password strength
        Returns: (is_valid, error_message)
        """
        if len(password) < cls.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {cls.MIN_PASSWORD_LENGTH} characters long"
            
        if not cls.PASSWORD_PATTERN.match(password):
            return False, "Password must contain at least one uppercase letter, one lowercase letter, one number and one special character"
            
        return True, ""
        
    async def validate_file(self, file: UploadFile, max_size: int) -> Tuple[bool, Optional[str]]:
        """
        Validate file type and size
        Returns: (is_valid, error_message)
        """
        # Check file size
        file_size = 0
        content = await file.read()
        file_size = len(content)
        await file.seek(0)  # Reset file pointer
        
        if file_size > max_size:
            return False, f"File size exceeds maximum limit of {max_size} bytes"
            
        # Check file type using python-magic
        mime_type = magic.from_buffer(content, mime=True)
        if mime_type not in self.ALLOWED_MIME_TYPES:
            return False, f"File type {mime_type} not allowed"
            
        # Verify extension matches mime type
        file_ext = file.filename.lower()[file.filename.rfind('.'):]
        if file_ext not in self.ALLOWED_MIME_TYPES[mime_type]:
            return False, "File extension does not match its content type"
            
        return True, None

    def validate_file_upload(self, file: UploadFile, config: Dict[str, Any]) -> bool:
        """Validate file upload request.
        
        Args:
            file: Uploaded file
            config: Security configuration
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Check file size
            if file.size > config['max_file_size']:
                raise ValidationError(
                    f"File size {file.size} exceeds maximum {config['max_file_size']}"
                )
                
            # Check filename
            if not self._is_safe_filename(file.filename):
                raise ValidationError("Invalid filename")
                
            # Check content type
            content = file.file.read()
            content_type = self.mime.from_buffer(content)
            if not self._is_allowed_content_type(content_type, config['allowed_types']):
                raise ValidationError(f"File type {content_type} not allowed")
                
            # Reset file pointer
            file.file.seek(0)
            return True
            
        except Exception as e:
            logger.error(f"File validation failed: {str(e)}")
            raise ValidationError(str(e))
            
    def _is_safe_filename(self, filename: str) -> bool:
        """Check if filename is safe."""
        return bool(re.match(r'^[\w\-. ]+$', filename))
        
    def _is_allowed_content_type(self, content_type: str, allowed_types: List[str]) -> bool:
        """Check if content type is allowed."""
        return content_type in allowed_types
