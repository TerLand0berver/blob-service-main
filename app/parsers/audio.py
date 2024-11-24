"""
Audio parser implementation using Azure Cognitive Services.
"""
import io
from typing import Dict, Any, Optional
import magic
import azure.cognitiveservices.speech as speechsdk

from .base import BaseParser, ParserError

class AudioParser(BaseParser):
    """Parser for audio files using Azure Cognitive Services."""
    
    SUPPORTED_TYPES = {
        'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav',
        'audio/ogg', 'audio/flac', 'audio/aac', 'audio/m4a'
    }
    
    SUPPORTED_EXTENSIONS = {
        '.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a'
    }

    def __init__(self):
        super().__init__()
        self.speech_config = None

    def _initialize_speech_config(self):
        """Initialize Azure Speech config if not already initialized."""
        if not self.speech_config:
            from ..core.config import settings
            self.speech_config = speechsdk.SpeechConfig(
                subscription=settings.AZURE_SPEECH_KEY,
                region=settings.AZURE_SPEECH_REGION
            )

    def parse(self, file_content: bytes, mime_type: str = None, **kwargs) -> Dict[str, Any]:
        """
        Parse audio file content using Azure Speech Services.
        
        Args:
            file_content: Raw bytes of the audio file
            mime_type: MIME type of the file (optional)
            **kwargs: Additional arguments
            
        Returns:
            Dict containing the parsed information
        """
        try:
            self._initialize_speech_config()
            
            # Save content to temporary file for Azure SDK
            temp_path = self._save_temp_file(file_content)
            
            # Create audio config from file
            audio_config = speechsdk.AudioConfig(filename=temp_path)
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # Start recognition
            result = speech_recognizer.recognize_once_async().get()
            
            # Clean up temp file
            self._cleanup_temp_file(temp_path)
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return {
                    'text': result.text,
                    'confidence': 1.0 if result.text else 0.0,
                    'duration': None  # Azure doesn't provide duration directly
                }
            else:
                return {
                    'text': '',
                    'confidence': 0.0,
                    'duration': None
                }
                
        except Exception as e:
            raise ParserError(f"Failed to parse audio file: {str(e)}")

    def _save_temp_file(self, content: bytes) -> str:
        """Save content to a temporary file and return its path."""
        import tempfile
        import os
        
        temp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        try:
            temp.write(content)
            temp.close()
            return temp.name
        except Exception as e:
            os.unlink(temp.name)
            raise ParserError(f"Failed to save temporary file: {str(e)}")

    def _cleanup_temp_file(self, path: str):
        """Clean up temporary file."""
        import os
        try:
            os.unlink(path)
        except:
            pass  # Ignore cleanup errors

    async def can_handle(self, content_type: str, file_extension: str) -> bool:
        """Check if parser can handle this file type."""
        return (content_type.lower() in self.SUPPORTED_TYPES or
                file_extension.lower() in self.SUPPORTED_EXTENSIONS)

    async def validate(self, file_data: bytes, metadata: Dict[str, Any]) -> bool:
        """Validate audio format."""
        try:
            mime = magic.Magic(mime=True)
            content_type = mime.from_buffer(file_data)
            
            if not any(t in content_type for t in ('audio/', 'video/')):
                return False
            
            return True
        except Exception:
            return False

    async def optimize(self, file_data: bytes, metadata: Dict[str, Any]) -> tuple[bytes, Dict[str, Any]]:
        """Optimize audio file."""
        return file_data, metadata
