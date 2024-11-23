"""
Middleware pipeline management.
"""
from typing import List, Dict, Any, Type
from .base import BaseMiddleware
from ..core.config import config

class MiddlewarePipeline:
    """Manages the execution of middleware chain."""
    
    def __init__(self):
        """Initialize middleware pipeline."""
        self.middlewares: List[BaseMiddleware] = []
    
    def add_middleware(self, middleware: BaseMiddleware) -> None:
        """Add middleware to pipeline."""
        if not isinstance(middleware, BaseMiddleware):
            raise TypeError("Middleware must inherit from BaseMiddleware")
        if not middleware.validate():
            raise ValueError(f"Invalid configuration for middleware: {middleware.__class__.__name__}")
        self.middlewares.append(middleware)
    
    def remove_middleware(self, middleware_type: Type[BaseMiddleware]) -> None:
        """Remove middleware from pipeline."""
        self.middlewares = [m for m in self.middlewares if not isinstance(m, middleware_type)]
    
    async def process_upload(self, file_data: bytes, metadata: Dict[str, Any]) -> tuple[bytes, Dict[str, Any]]:
        """Process file through middleware chain during upload."""
        current_data = file_data
        current_metadata = metadata.copy()
        
        for middleware in self.middlewares:
            try:
                current_data, current_metadata = await middleware.process_upload(
                    current_data, current_metadata
                )
            except Exception as e:
                # Log error and continue with next middleware
                print(f"Error in {middleware.__class__.__name__} during upload: {e}")
                continue
        
        return current_data, current_metadata
    
    async def process_download(self, file_data: bytes, metadata: Dict[str, Any]) -> tuple[bytes, Dict[str, Any]]:
        """Process file through middleware chain during download."""
        current_data = file_data
        current_metadata = metadata.copy()
        
        # Process in reverse order for download
        for middleware in reversed(self.middlewares):
            try:
                current_data, current_metadata = await middleware.process_download(
                    current_data, current_metadata
                )
            except Exception as e:
                # Log error and continue with next middleware
                print(f"Error in {middleware.__class__.__name__} during download: {e}")
                continue
        
        return current_data, current_metadata
    
    @classmethod
    def from_config(cls, middleware_config: Dict[str, Any] = None) -> 'MiddlewarePipeline':
        """Create middleware pipeline from configuration."""
        if middleware_config is None:
            middleware_config = config.middleware_config
        
        pipeline = cls()
        middleware_map = {
            'compression': ('compression.CompressionMiddleware', {}),
            'encryption': ('encryption.EncryptionMiddleware', {})
        }
        
        for name, enabled in middleware_config.get('enabled', {}).items():
            if not enabled:
                continue
                
            module_path, default_config = middleware_map.get(name, (None, None))
            if not module_path:
                continue
                
            try:
                module_name, class_name = module_path.rsplit('.', 1)
                module = __import__(f"app.middleware.{module_name}", fromlist=[class_name])
                middleware_class = getattr(module, class_name)
                
                # Merge default config with user config
                middleware_conf = middleware_config.get(name, {})
                if default_config:
                    middleware_conf = {**default_config, **middleware_conf}
                
                middleware = middleware_class(middleware_conf)
                pipeline.add_middleware(middleware)
            except Exception as e:
                print(f"Error loading middleware {name}: {e}")
        
        return pipeline
