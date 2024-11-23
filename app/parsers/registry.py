"""
Parser registry implementation.
"""
from typing import Dict, Any, Optional, Type
from .base import BaseParser
from .image import ImageParser
from .pdf import PDFParser
from .audio import AudioParser
from .video import VideoParser
from .document import DocumentParser

class ParserRegistry:
    """Registry for file parsers."""
    
    _instance = None
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize parser registry."""
        self.config = config or {}
        self.parsers = []
        self._register_default_parsers()
    
    @classmethod
    def from_config(cls, config: Optional[Dict[str, Any]] = None) -> 'ParserRegistry':
        """Get or create registry instance with config."""
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance
    
    def _register_default_parsers(self):
        """Register default parsers."""
        self.register_parser(ImageParser(self.config.get('image', {})))
        self.register_parser(PDFParser(self.config.get('pdf', {})))
        self.register_parser(AudioParser(self.config.get('audio', {})))
        self.register_parser(VideoParser(self.config.get('video', {})))
        self.register_parser(DocumentParser(self.config.get('document', {})))
    
    def register_parser(self, parser: BaseParser):
        """Register a new parser."""
        if not isinstance(parser, BaseParser):
            raise ValueError("Parser must be an instance of BaseParser")
        self.parsers.append(parser)
    
    async def get_parser(self, content_type: str, file_extension: str) -> Optional[BaseParser]:
        """Get appropriate parser for file type."""
        for parser in self.parsers:
            if await parser.can_handle(content_type, file_extension):
                return parser
        return None
