"""
Video parser implementation.
"""
import io
import os
from typing import Dict, Any, Optional
import magic
import ffmpeg
from PIL import Image

from .base import BaseParser, ParserError

class VideoParser(BaseParser):
    """Parser for video files."""
    
    SUPPORTED_TYPES = {
        'video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo',
        'video/x-matroska', 'video/webm', 'video/x-flv'
    }
    
    SUPPORTED_EXTENSIONS = {
        '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.mpeg', '.mpg'
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize video parser."""
        super().__init__(config)
        self.target_format = self.config.get('target_format', 'mp4')
        self.video_codec = self.config.get('video_codec', 'libx264')
        self.audio_codec = self.config.get('audio_codec', 'aac')
        self.video_bitrate = self.config.get('video_bitrate', '2M')
        self.audio_bitrate = self.config.get('audio_bitrate', '192k')
        self.max_resolution = self.config.get('max_resolution', 1080)
        self.generate_thumbnail = self.config.get('generate_thumbnail', True)
        self.thumbnail_time = self.config.get('thumbnail_time', 1)  # seconds
        self.thumbnail_size = self.config.get('thumbnail_size', (320, 180))
    
    async def can_handle(self, content_type: str, file_extension: str) -> bool:
        """Check if parser can handle this file type."""
        return (content_type.lower() in self.SUPPORTED_TYPES or
                file_extension.lower() in self.SUPPORTED_EXTENSIONS)
    
    async def parse(self, file_data: bytes, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse video and extract metadata."""
        try:
            # Save temp file for ffmpeg
            temp_file = io.BytesIO(file_data)
            probe = ffmpeg.probe(temp_file)
            
            # Extract video stream info
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            
            # Extract audio stream info if exists
            audio_info = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
            
            metadata.update({
                'format': probe['format']['format_name'],
                'duration': float(probe['format'].get('duration', 0)),
                'size': int(probe['format'].get('size', 0)),
                'bitrate': int(probe['format'].get('bit_rate', 0)),
                'video': {
                    'codec': video_info['codec_name'],
                    'width': int(video_info.get('width', 0)),
                    'height': int(video_info.get('height', 0)),
                    'fps': eval(video_info.get('r_frame_rate', '0/1')),
                    'bitrate': int(video_info.get('bit_rate', 0)),
                    'pixel_format': video_info.get('pix_fmt', '')
                }
            })
            
            if audio_info:
                metadata['audio'] = {
                    'codec': audio_info['codec_name'],
                    'channels': int(audio_info.get('channels', 0)),
                    'sample_rate': int(audio_info.get('sample_rate', 0)),
                    'bitrate': int(audio_info.get('bit_rate', 0))
                }
            
            # Generate thumbnail if requested
            if self.generate_thumbnail:
                thumbnail = await self._generate_thumbnail(temp_file)
                if thumbnail:
                    metadata['thumbnail'] = thumbnail
            
            return metadata
        except Exception as e:
            raise ParserError(f"Failed to parse video: {e}")
    
    async def validate(self, file_data: bytes, metadata: Dict[str, Any]) -> bool:
        """Validate video format."""
        try:
            mime = magic.Magic(mime=True)
            content_type = mime.from_buffer(file_data)
            
            if not content_type.startswith('video/'):
                return False
            
            # Try to probe the video
            temp_file = io.BytesIO(file_data)
            ffmpeg.probe(temp_file)
            return True
        except Exception:
            return False
    
    async def optimize(self, file_data: bytes, metadata: Dict[str, Any]) -> tuple[bytes, Dict[str, Any]]:
        """Optimize video file."""
        try:
            # Track original size
            original_size = len(file_data)
            
            # Create input stream
            temp_file = io.BytesIO(file_data)
            stream = ffmpeg.input(temp_file)
            
            # Get video info
            probe = ffmpeg.probe(temp_file)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            width = int(video_info.get('width', 0))
            height = int(video_info.get('height', 0))
            
            # Scale if necessary
            if max(width, height) > self.max_resolution:
                scale_factor = self.max_resolution / max(width, height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                stream = ffmpeg.filter(stream, 'scale', new_width, new_height)
            
            # Set up output options
            output_options = {
                'vcodec': self.video_codec,
                'acodec': self.audio_codec,
                'video_bitrate': self.video_bitrate,
                'audio_bitrate': self.audio_bitrate,
                'format': self.target_format
            }
            
            if self.video_codec == 'libx264':
                output_options.update({
                    'preset': 'medium',
                    'crf': '23'
                })
            
            # Create output stream
            output = io.BytesIO()
            stream = ffmpeg.output(stream, output, **output_options)
            
            # Run the conversion
            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
            optimized_data = output.getvalue()
            
            # Only use optimized version if it's smaller
            if len(optimized_data) < original_size:
                metadata['optimized'] = True
                metadata['original_size'] = original_size
                metadata['format'] = self.target_format
                return optimized_data, metadata
            
            return file_data, metadata
            
        except Exception as e:
            raise ParserError(f"Failed to optimize video: {e}")
    
    async def _generate_thumbnail(self, video_file: io.BytesIO) -> Optional[bytes]:
        """Generate thumbnail from video."""
        try:
            stream = ffmpeg.input(video_file, ss=self.thumbnail_time)
            stream = ffmpeg.filter(stream, 'scale', self.thumbnail_size[0], self.thumbnail_size[1])
            output = io.BytesIO()
            
            stream = ffmpeg.output(stream, output, vframes=1, format='image2', vcodec='mjpeg')
            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
            
            return output.getvalue()
        except Exception:
            return None
