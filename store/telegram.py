import os
import logging
from typing import Optional
import aiohttp
from fastapi import UploadFile
from config import (
    TG_BOT_TOKEN,
    TG_CHAT_ID,
    TG_API_URL
)
from store.utils import store_filename

logger = logging.getLogger(__name__)

async def process_tg(file: UploadFile) -> str:
    """
    将文件上传到Telegram并返回URL
    
    Args:
        file: 要上传的文件对象
    
    Returns:
        str: 文件的访问URL
    
    Raises:
        ValueError: 当上传失败时抛出
    """
    if not all([TG_BOT_TOKEN, TG_CHAT_ID]):
        raise ValueError("Telegram credentials not configured")
    
    try:
        # 准备API URL
        api_url = f"{TG_API_URL}/bot{TG_BOT_TOKEN}/sendDocument"
        
        # 读取文件内容
        file_content = await file.read()
        
        # 准备表单数据
        form = aiohttp.FormData()
        form.add_field('chat_id', TG_CHAT_ID)
        form.add_field(
            'document',
            file_content,
            filename=file.filename,
            content_type=file.content_type
        )
        
        # 发送请求
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, data=form) as response:
                if response.status != 200:
                    error_msg = f"Telegram API request failed with status {response.status}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                result = await response.json()
                if not result.get('ok'):
                    error_msg = f"Telegram API error: {result.get('description', 'Unknown error')}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                # 从响应中获取文件URL
                document = result.get('result', {}).get('document')
                if not document or 'file_id' not in document:
                    raise ValueError("File ID not found in Telegram response")
                
                file_id = document['file_id']
                
                # 获取文件路径
                file_path_url = f"{TG_API_URL}/bot{TG_BOT_TOKEN}/getFile"
                async with session.get(file_path_url, params={'file_id': file_id}) as path_response:
                    if path_response.status != 200:
                        raise ValueError("Failed to get file path from Telegram")
                    
                    path_result = await path_response.json()
                    if not path_result.get('ok'):
                        raise ValueError("Failed to get file path from Telegram")
                    
                    file_path = path_result.get('result', {}).get('file_path')
                    if not file_path:
                        raise ValueError("File path not found in Telegram response")
                    
                    # 构建最终的文件URL
                    file_url = f"{TG_API_URL}/file/bot{TG_BOT_TOKEN}/{file_path}"
                    
                    logger.info(f"File {file.filename} uploaded successfully to Telegram")
                    return file_url
    
    except aiohttp.ClientError as e:
        error_msg = f"Telegram API request failed: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error during Telegram upload: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
