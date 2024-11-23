"""Amazon S3 storage backend."""
import os
import io
import boto3
import logging
from datetime import datetime, timedelta
from typing import BinaryIO, Optional, Dict, Any, List, Union, Tuple
import mimetypes
from botocore.exceptions import ClientError
from urllib.parse import urlparse

from .base import StorageBackend, StorageError
from ..core.schemas import FileInfo, FileMetadata
from ..core.config import config

logger = logging.getLogger(__name__)

class S3StorageBackend(StorageBackend):
    """Amazon S3 storage backend."""
    
    def __init__(
        self,
        bucket: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: Optional[str] = None,
        endpoint_url: Optional[str] = None
    ):
        """Initialize S3 storage.
        
        Args:
            bucket: S3 bucket name
            aws_access_key_id: AWS access key
            aws_secret_access_key: AWS secret key
            region_name: AWS region
            endpoint_url: Custom endpoint URL (for S3-compatible services)
        """
        super().__init__()
        
        self.bucket = bucket or config.storage.s3_bucket
        self.aws_access_key_id = aws_access_key_id or config.storage.aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key or config.storage.aws_secret_access_key
        self.region_name = region_name or config.storage.aws_region
        self.endpoint_url = endpoint_url or config.storage.s3_endpoint_url
        
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name,
            endpoint_url=self.endpoint_url
        )
        
    def _get_object_url(self, path: str, expires: int = 3600) -> str:
        """Generate pre-signed URL for object.
        
        Args:
            path: Object path
            expires: URL expiration in seconds
            
        Returns:
            Pre-signed URL
        """
        try:
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': path
                },
                ExpiresIn=expires
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate pre-signed URL: {str(e)}")
            raise StorageError(f"Failed to generate URL: {str(e)}")
            
    async def save(
        self,
        file: BinaryIO,
        path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FileInfo:
        """Save file to S3.
        
        Args:
            file: File-like object
            path: Optional storage path
            metadata: Optional metadata
            
        Returns:
            FileInfo object
            
        Raises:
            StorageError: If save fails
        """
        try:
            if path is None:
                ext = mimetypes.guess_extension(metadata.get("content_type", "")) if metadata else ""
                path = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}{ext}"
                
            # Create metadata
            file_metadata = self._create_metadata(
                file,
                metadata.get("content_type", "application/octet-stream") if metadata else "application/octet-stream",
                metadata
            )
            
            # Upload to S3
            extra_args = {
                'ContentType': file_metadata.content_type
            }
            if metadata:
                extra_args['Metadata'] = {
                    k: str(v) for k, v in metadata.items()
                }
                
            self.s3.upload_fileobj(
                file,
                self.bucket,
                path,
                ExtraArgs=extra_args
            )
            
            # Update stats
            self._update_stats('upload', file_metadata.size)
            
            return FileInfo(
                path=path,
                metadata=file_metadata,
                url=self._get_object_url(path)
            )
            
        except Exception as e:
            self._update_stats('error')
            raise StorageError(f"Failed to save file: {str(e)}")
            
    async def get(
        self,
        path: str,
        include_metadata: bool = True
    ) -> Union[BinaryIO, Tuple[BinaryIO, FileMetadata]]:
        """Get file from S3.
        
        Args:
            path: Storage path
            include_metadata: Include metadata in response
            
        Returns:
            File content and optional metadata
            
        Raises:
            StorageError: If get fails
        """
        try:
            # Get object
            response = self.s3.get_object(
                Bucket=self.bucket,
                Key=path
            )
            
            # Create file-like object
            file = io.BytesIO(response['Body'].read())
            
            if not include_metadata:
                return file
                
            # Get metadata
            metadata = FileMetadata(
                content_type=response.get('ContentType', 'application/octet-stream'),
                size=response['ContentLength'],
                created_at=response['LastModified'],
                updated_at=response['LastModified'],
                checksum=response.get('ETag', '').strip('"'),
                custom=response.get('Metadata', {})
            )
            
            # Update stats
            self._update_stats('download', metadata.size)
            
            return file, metadata
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise StorageError("File not found")
            self._update_stats('error')
            raise StorageError(f"Failed to get file: {str(e)}")
            
    async def delete(self, path: str) -> bool:
        """Delete file from S3.
        
        Args:
            path: Storage path
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            StorageError: If delete fails
        """
        try:
            self.s3.delete_object(
                Bucket=self.bucket,
                Key=path
            )
            self._update_stats('delete')
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return False
            self._update_stats('error')
            raise StorageError(f"Failed to delete file: {str(e)}")
            
    async def exists(self, path: str) -> bool:
        """Check if file exists in S3.
        
        Args:
            path: Storage path
            
        Returns:
            True if exists, False otherwise
        """
        try:
            self.s3.head_object(
                Bucket=self.bucket,
                Key=path
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise StorageError(f"Failed to check file: {str(e)}")
            
    async def list_files(
        self,
        path: Optional[str] = None,
        recursive: bool = False,
        include_metadata: bool = False
    ) -> List[Union[str, FileInfo]]:
        """List files in S3.
        
        Args:
            path: Optional path prefix
            recursive: List files recursively
            include_metadata: Include file metadata
            
        Returns:
            List of file paths or FileInfo objects
        """
        try:
            paginator = self.s3.get_paginator('list_objects_v2')
            
            kwargs = {
                'Bucket': self.bucket
            }
            if path:
                kwargs['Prefix'] = path
            if not recursive:
                kwargs['Delimiter'] = '/'
                
            files = []
            async for page in paginator.paginate(**kwargs):
                for obj in page.get('Contents', []):
                    if include_metadata:
                        metadata = FileMetadata(
                            content_type=mimetypes.guess_type(obj['Key'])[0] or 'application/octet-stream',
                            size=obj['Size'],
                            created_at=obj['LastModified'],
                            updated_at=obj['LastModified'],
                            checksum=obj['ETag'].strip('"')
                        )
                        files.append(FileInfo(
                            path=obj['Key'],
                            metadata=metadata,
                            url=self._get_object_url(obj['Key'])
                        ))
                    else:
                        files.append(obj['Key'])
                        
            return files
            
        except Exception as e:
            raise StorageError(f"Failed to list files: {str(e)}")
