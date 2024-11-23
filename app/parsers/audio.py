"""
Audio parser implementation.
"""
import io
from typing import Dict, Any, Optional
import magic
import pydub
from pydub.utils import mediainfo

from .base import BaseParser, ParserError

class AudioParser(BaseParser):
    """Parser for audio files."""
    
    SUPPORTED_TYPES = {
        'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav',
        'audio/ogg', 'audio/flac', 'audio/aac', 'audio/m4a'
    }
    
    SUPPORTED_EXTENSIONS = {
        '.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a'
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize audio parser."""
        super().__init__(config)
        self.target_format = self.config.get('target_format', 'mp3')
        self.bitrate = self.config.get('bitrate', '192k')
        self.sample_rate = self.config.get('sample_rate', 44100)
        self.channels = self.config.get('channels', 2)
        self.normalize = self.config.get('normalize', True)
    
    async def can_handle(self, content_type: str, file_extension: str) -> bool:
        """Check if parser can handle this file type."""
        return (content_type.lower() in self.SUPPORTED_TYPES or
                file_extension.lower() in self.SUPPORTED_EXTENSIONS)
    
    async def parse(self, file_data: bytes, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse audio and extract metadata."""
        try:
            # Save temp file for pydub
            temp_file = io.BytesIO(file_data)
            audio = pydub.AudioSegment.from_file(temp_file)
            
            # Get media info
            info = mediainfo(temp_file)
            
            metadata.update({
                'duration': len(audio) / 1000.0,  # Convert to seconds
                'channels': audio.channels,
                'frame_rate': audio.frame_rate,
                'sample_width': audio.sample_width,
                'frame_width': audio.frame_width,
                'max_dBFS': audio.max_dBFS,
                'format': info.get('format_name', ''),
                'codec': info.get('codec_name', ''),
                'bitrate': info.get('bit_rate', ''),
                'tags': {
                    k.lower(): v for k, v in info.get('tags', {}).items()
                }
            })
            
            return metadata
        except Exception as e:
            raise ParserError(f"Failed to parse audio: {e}")
    
    async def validate(self, file_data: bytes, metadata: Dict[str, Any]) -> bool:
        """Validate audio format."""
        try:
            mime = magic.Magic(mime=True)
            content_type = mime.from_buffer(file_data)
            
            if not any(t in content_type for t in ('audio/', 'video/')):
                return False
            
            # Try to load the audio
            temp_file = io.BytesIO(file_data)
            pydub.AudioSegment.from_file(temp_file)
            return True
        except Exception:
            return False
    
    async def optimize(self, file_data: bytes, metadata: Dict[str, Any]) -> tuple[bytes, Dict[str, Any]]:
        """Optimize audio file."""
        try:
            temp_file = io.BytesIO(file_data)
            audio = pydub.AudioSegment.from_file(temp_file)
            
            # Track original size
            original_size = len(file_data)
            
            # Normalize volume if requested
            if self.normalize:
                audio = pydub.effects.normalize(audio)
            
            # Convert sample rate if different
            if audio.frame_rate != self.sample_rate:
                audio = audio.set_frame_rate(self.sample_rate)
            
            # Convert channels if different
            if audio.channels != self.channels:
                if self.channels == 1:
                    audio = audio.set_channels(1)
                else:
                    audio = audio.set_channels(2)
            
            # Export to target format
            output = io.BytesIO()
            export_args = {
                'format': self.target_format,
                'bitrate': self.bitrate,
            }
            
            if self.target_format == 'mp3':
                export_args.update({
                    'codec': 'libmp3lame',
                    'parameters': ['-q:a', '2']  # High quality VBR
                })
            
            audio.export(output, **export_args)
            optimized_data = output.getvalue()
            
            # Only use optimized version if it's smaller
            if len(optimized_data) < original_size:
                metadata['optimized'] = True
                metadata['original_size'] = original_size
                metadata['format'] = self.target_format
                return optimized_data, metadata
            
            return file_data, metadata
            
        except Exception as e:
            raise ParserError(f"Failed to optimize audio: {e}")
