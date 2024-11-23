"""
API routes.
"""
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Query, Path, Depends
from ..config import config
from ..core.errors import ValidationError, NotFoundError
from ..storage import get_storage
from .models import (
    FileUploadResponse,
    FileListResponse,
    FileDeleteResponse,
    StorageConfigResponse,
    HealthResponse,
    HealthInfo,
    HealthStatus,
)
from .deps import CommonDeps, ContentDeps
from .utils import get_uptime

# Create router
router = APIRouter()

@router.post(
    "/upload",
    response_model=FileUploadResponse,
    dependencies=[Depends(ContentDeps)],
    description="Upload file to storage"
)
async def upload_file(
    file: UploadFile = File(...),
    path: Optional[str] = Query(None, description="Storage path"),
    _: CommonDeps = None
) -> FileUploadResponse:
    """Upload file to storage.
    
    Args:
        file: File to upload
        path: Optional storage path
        
    Returns:
        Upload response with file info
        
    Raises:
        ValidationError: If file upload fails
    """
    # Get storage backend
    storage = get_storage()
    
    # Upload file
    file_info = await storage.upload_file(file, path)
    
    # Return response
    return FileUploadResponse(data=file_info)

@router.get(
    "/files",
    response_model=FileListResponse,
    description="List files in storage"
)
async def list_files(
    path: Optional[str] = Query(None, description="Storage path"),
    recursive: bool = Query(False, description="List files recursively"),
    _: CommonDeps = None
) -> FileListResponse:
    """List files in storage.
    
    Args:
        path: Optional storage path
        recursive: List files recursively
        
    Returns:
        List response with file info
    """
    # Get storage backend
    storage = get_storage()
    
    # List files
    files = await storage.list_files(path, recursive)
    
    # Return response
    return FileListResponse(data=files)

@router.delete(
    "/files/{file_path:path}",
    response_model=FileDeleteResponse,
    description="Delete file from storage"
)
async def delete_file(
    file_path: str = Path(..., description="File path"),
    _: CommonDeps = None
) -> FileDeleteResponse:
    """Delete file from storage.
    
    Args:
        file_path: Path to file
        
    Returns:
        Delete response
        
    Raises:
        NotFoundError: If file not found
    """
    # Get storage backend
    storage = get_storage()
    
    # Delete file
    await storage.delete_file(file_path)
    
    # Return response
    return FileDeleteResponse()

@router.get(
    "/config/storage",
    response_model=StorageConfigResponse,
    description="Get storage configuration"
)
async def get_storage_config(
    _: CommonDeps = None
) -> StorageConfigResponse:
    """Get storage configuration.
    
    Returns:
        Storage configuration response
    """
    # Get config
    cfg = config()
    
    # Return response
    return StorageConfigResponse(
        data={
            "type": cfg.storage.type,
            "path": cfg.storage.local_path,
            "domain": cfg.storage.local_domain,
            "bucket": cfg.storage.s3_bucket,
            "endpoint": cfg.storage.s3_endpoint,
            "region": cfg.storage.s3_region,
        }
    )

@router.get(
    "/health",
    response_model=HealthResponse,
    description="Get service health status"
)
async def health_check() -> HealthResponse:
    """Get service health status.
    
    Returns:
        Health check response
    """
    try:
        # Get storage backend
        storage = get_storage()
        
        # Check storage
        storage_info = await storage.get_info()
        
        # Return response
        return HealthResponse(
            data=HealthInfo(
                status=HealthStatus.OK,
                version="0.1.0",  # TODO: Get from package
                storage=storage_info,
                uptime=get_uptime()
            )
        )
    except Exception as e:
        # Return error status
        return HealthResponse(
            data=HealthInfo(
                status=HealthStatus.ERROR,
                version="0.1.0",  # TODO: Get from package
                storage={"error": str(e)},
                uptime=get_uptime()
            )
        )
