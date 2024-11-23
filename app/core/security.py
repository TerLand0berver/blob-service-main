import re
import magic
from typing import Optional, Tuple
from fastapi import UploadFile

class SecurityValidator:
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
        
    @classmethod
    async def validate_file(cls, file: UploadFile, max_size: int) -> Tuple[bool, Optional[str]]:
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
        if mime_type not in cls.ALLOWED_MIME_TYPES:
            return False, f"File type {mime_type} not allowed"
            
        # Verify extension matches mime type
        file_ext = file.filename.lower()[file.filename.rfind('.'):]
        if file_ext not in cls.ALLOWED_MIME_TYPES[mime_type]:
            return False, "File extension does not match its content type"
            
        return True, None
