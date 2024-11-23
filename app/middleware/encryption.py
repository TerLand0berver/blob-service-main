"""
Encryption middleware.
"""
import os
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from .base import BaseMiddleware
from ..core.config import config

class EncryptionMiddleware(BaseMiddleware):
    """Middleware for file encryption."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize encryption middleware."""
        super().__init__(config)
        self.key = self._get_or_generate_key()
        self.fernet = Fernet(self.key)
        self.min_size = self.config.get('min_size', 0)
        self.excluded_types = set(self.config.get(
            'excluded_types',
            ['image/', 'video/', 'audio/']
        ))
    
    def _get_or_generate_key(self) -> bytes:
        """Get existing key or generate a new one."""
        key = self.config.get('key')
        if key:
            return base64.urlsafe_b64decode(key)
        
        # Generate a new key using PBKDF2
        password = self.config.get('password', os.urandom(32))
        salt = self.config.get('salt', os.urandom(16))
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def should_encrypt(self, size: int, content_type: str) -> bool:
        """Check if file should be encrypted."""
        if size < self.min_size:
            return False
            
        return not any(t in content_type for t in self.excluded_types)
    
    async def process_upload(self, file_data: bytes, metadata: Dict[str, Any]) -> tuple[bytes, Dict[str, Any]]:
        """Encrypt file during upload if applicable."""
        size = len(file_data)
        content_type = metadata.get('content_type', '')
        
        if not self.should_encrypt(size, content_type):
            return file_data, metadata
        
        encrypted_data = self.fernet.encrypt(file_data)
        metadata['encrypted'] = True
        
        return encrypted_data, metadata
    
    async def process_download(self, file_data: bytes, metadata: Dict[str, Any]) -> tuple[bytes, Dict[str, Any]]:
        """Decrypt file during download if it was encrypted."""
        if not metadata.get('encrypted'):
            return file_data, metadata
        
        decrypted_data = self.fernet.decrypt(file_data)
        metadata.pop('encrypted', None)
        
        return decrypted_data, metadata
    
    def validate(self) -> bool:
        """Validate encryption configuration."""
        try:
            if not isinstance(self.key, bytes):
                return False
            if not isinstance(self.min_size, int) or self.min_size < 0:
                return False
            # Test encryption/decryption
            test_data = b"test"
            encrypted = self.fernet.encrypt(test_data)
            decrypted = self.fernet.decrypt(encrypted)
            return decrypted == test_data
        except Exception:
            return False
