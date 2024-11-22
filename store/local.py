import os
from fastapi import UploadFile
from config import LOCAL_STORAGE_DOMAIN
from store.utils import store_filename
import aiofiles
import logging

logger = logging.getLogger(__name__)

async def process_local(file: UploadFile) -> str:
    """Process file and return its direct url."""
    try:
        filename = store_filename(file.filename)
        storage_dir = "static"
        
        # 确保存储目录存在
        os.makedirs(storage_dir, exist_ok=True)
        
        path = os.path.join(storage_dir, filename)
        
        # 使用异步文件操作
        async with aiofiles.open(path, "wb") as f:
            # 分块读写，避免大文件占用内存
            chunk_size = 8192  # 8KB chunks
            while chunk := await file.read(chunk_size):
                await f.write(chunk)
        
        # 构建URL时确保路径分隔符正确
        url_path = path.replace(os.path.sep, "/")
        url = f"{LOCAL_STORAGE_DOMAIN.rstrip('/')}/{url_path}"
        
        logger.info(f"File {filename} saved successfully at {path}")
        return url
        
    except Exception as e:
        error_msg = f"Failed to save file {file.filename}: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
