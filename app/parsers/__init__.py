"""
File parser module initialization.
"""
from .base import BaseParser, ParserError
from .image import ImageParser
from .registry import ParserRegistry

__all__ = [
    'BaseParser',
    'ParserError',
    'ImageParser',
    'ParserRegistry',
]
