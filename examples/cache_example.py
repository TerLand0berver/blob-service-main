"""
Example usage of cache middleware.
"""
import asyncio
import os
from typing import Dict, Any

from app.middleware.cache_factory import CacheFactory
from app.utils.cache_config import get_cache_config

async def process_file(file_path: str, cache_backend: str = 'disk') -> None:
    """Process a file using cache middleware.
    
    Args:
        file_path: Path to file to process
        cache_backend: Cache backend to use ('disk' or 'redis')
    """
    try:
        # Load cache configuration
        config = get_cache_config()
        
        # Create cache middleware
        cache = CacheFactory.create(cache_backend, config)
        
        # Read file data
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Create metadata
        metadata = {
            'filename': os.path.basename(file_path),
            'content_type': 'application/octet-stream',
            'size': len(file_data)
        }
        
        print(f"\nProcessing file: {metadata['filename']}")
        print(f"Original size: {metadata['size']} bytes")
        
        # Process file during upload
        print("\nProcessing upload...")
        processed_data, processed_metadata = await cache.process_upload(file_data, metadata)
        
        print("Upload cache stats:")
        print_cache_stats(cache.get_stats())
        
        # Process file during download
        print("\nProcessing download...")
        downloaded_data, downloaded_metadata = await cache.process_download(processed_data, processed_metadata)
        
        print("Download cache stats:")
        print_cache_stats(cache.get_stats())
        
    except Exception as e:
        print(f"Error processing file: {e}")

def print_cache_stats(stats: Dict[str, Any]) -> None:
    """Print cache statistics.
    
    Args:
        stats: Cache statistics dictionary
    """
    print(f"  Hits: {stats['hits']}")
    print(f"  Misses: {stats['misses']}")
    print(f"  Errors: {stats['errors']}")
    print(f"  Size: {stats['size']} bytes")
    print(f"  Hit ratio: {stats['hit_ratio']:.2%}")
    print(f"  Error rate: {stats['error_rate']:.2%}")

async def main():
    """Main function."""
    # Create test file
    test_file = 'test_file.txt'
    with open(test_file, 'w') as f:
        f.write('Hello, World!' * 1000)
    
    try:
        # Test disk cache
        print("\n=== Testing disk cache ===")
        await process_file(test_file, 'disk')
        
        # Test Redis cache
        print("\n=== Testing Redis cache ===")
        await process_file(test_file, 'redis')
        
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == '__main__':
    asyncio.run(main())
