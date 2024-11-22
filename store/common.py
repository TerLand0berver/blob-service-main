import base64
import logging
from typing import Optional
from fastapi import UploadFile
from store.utils import store_filename

logger = logging.getLogger(__name__)

async def process_base64(file: UploadFile) -> str:
    """
    将文件转换为base64编码并返回
    
    Args:
        file: 要处理的文件对象
    
    Returns:
        str: base64编码的文件内容
    
    Raises:
        ValueError: 当处理失败时抛出
    """
    try:
        # 读取文件内容
        file_content = await file.read()
        
        # 转换为base64
        base64_content = base64.b64encode(file_content).decode('utf-8')
        
        # 获取MIME类型
        content_type = file.content_type or 'application/octet-stream'
        
        # 构建data URL
        data_url = f"data:{content_type};base64,{base64_content}"
        
        logger.info(f"File {file.filename} converted to base64 successfully")
        return data_url
        
    except Exception as e:
        error_msg = f"Failed to convert file to base64: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
