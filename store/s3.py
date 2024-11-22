import os
import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile
from config import (
    S3_ACCESS_KEY,
    S3_SECRET_KEY,
    S3_BUCKET_NAME,
    S3_ENDPOINT_URL,
    S3_REGION_NAME,
    FILE_API_URL,
    FILE_API_TOKEN
)
from store.utils import store_filename
import aiohttp

logger = logging.getLogger(__name__)

async def process_s3(file: UploadFile) -> str:
    """
    将文件上传到S3存储并返回URL
    
    Args:
        file: 要上传的文件对象
    
    Returns:
        str: 文件的访问URL
    
    Raises:
        ValueError: 当上传失败时抛出
    """
    try:
        # 初始化S3客户端
        s3_client = boto3.client(
            's3',
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
            endpoint_url=S3_ENDPOINT_URL,
            region_name=S3_REGION_NAME
        )
        
        # 生成存储文件名
        filename = store_filename(file.filename)
        
        # 上传文件
        file_content = await file.read()
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=filename,
            Body=file_content,
            ContentType=file.content_type
        )
        
        # 生成URL
        url = f"{S3_ENDPOINT_URL}/{S3_BUCKET_NAME}/{filename}"
        
        logger.info(f"File {filename} uploaded successfully to S3")
        return url
        
    except ClientError as e:
        error_msg = f"S3 upload failed: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error during S3 upload: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

async def process_file_api(file: UploadFile) -> str:
    """
    通过文件API上传文件并返回URL
    
    Args:
        file: 要上传的文件对象
    
    Returns:
        str: 文件的访问URL
    
    Raises:
        ValueError: 当上传失败时抛出
    """
    try:
        # 准备上传
        headers = {
            "Authorization": f"Bearer {FILE_API_TOKEN}"
        }
        
        # 读取文件内容
        file_content = await file.read()
        
        # 使用aiohttp进行异步上传
        async with aiohttp.ClientSession() as session:
            form = aiohttp.FormData()
            form.add_field(
                'file',
                file_content,
                filename=file.filename,
                content_type=file.content_type
            )
            
            async with session.post(
                FILE_API_URL,
                data=form,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_msg = f"File API upload failed with status {response.status}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                result = await response.json()
                if not result.get('url'):
                    raise ValueError("File API response missing URL")
                
                logger.info(f"File {file.filename} uploaded successfully via File API")
                return result['url']
                
    except aiohttp.ClientError as e:
        error_msg = f"File API request failed: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error during File API upload: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
