"""
Storage factory module.
"""
from typing import Dict, Any, Type, Optional

from .base import BaseStorage
from .config import StorageConfig, create_storage_config
from .errors import StorageConfigError

# Storage backend registry
_storage_backends: Dict[str, Type[BaseStorage]] = {}

def register_backend(name: str, backend_class: Type[BaseStorage]):
    """Register storage backend.
    
    Args:
        name: Backend name
        backend_class: Backend class
    """
    _storage_backends[name] = backend_class

def create_storage(
    backend: str,
    config: Optional[Dict[str, Any]] = None
) -> BaseStorage:
    """Create storage instance.
    
    Args:
        backend: Backend name
        config: Optional backend configuration
        
    Returns:
        Storage instance
        
    Raises:
        StorageConfigError: If backend not found or config invalid
    """
    if backend not in _storage_backends:
        raise StorageConfigError(
            f"Storage backend not found: {backend}"
        )
        
    backend_class = _storage_backends[backend]
    
    if config is None:
        config = {}
    
    # Add backend name to config
    config['backend'] = backend
    
    # Create storage config
    storage_config = create_storage_config(**config)
    
    # Create storage instance
    return backend_class(storage_config)
