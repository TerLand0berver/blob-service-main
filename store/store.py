from fastapi import UploadFile
from typing import Dict, Callable, Awaitable, Optional
from config import STORAGE_TYPE

from store.common import process_base64
from store.local import process_local
from store.s3 import process_s3, process_file_api
from store.telegram import process_tg

# 处理器类型定义
FileHandler = Callable[[UploadFile], Awaitable[str]]

# 文件处理器映射
FILE_HANDLERS: Dict[str, FileHandler] = {
    "common": process_base64,
    "local": process_local,
    "s3": process_s3,
    "tg": process_tg,
    "file_api": process_file_api,
}

async def get_handler(storage_type: Optional[str] = None) -> FileHandler:
    """获取文件处理器"""
    handler_type = storage_type or STORAGE_TYPE
    handler = FILE_HANDLERS.get(handler_type)
    
    if not handler:
        raise ValueError(f"Unsupported storage type: {handler_type}")
    
    return handler

async def process_file(file: UploadFile, storage_type: Optional[str] = None) -> str:
    """处理文件并返回URL"""
    handler = await get_handler(storage_type)
    return await handler(file)

async def process_image(file: UploadFile, storage_type: Optional[str] = None) -> str:
    """处理图片文件"""
    return await process_file(file, storage_type)

async def process_all(file: UploadFile) -> str:
    """处理所有类型的文件"""
    if STORAGE_TYPE == "common":
        raise ValueError("Cannot use 'Save All' option without storage configuration")
        
    return await process_file(file)
