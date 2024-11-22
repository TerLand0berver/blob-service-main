from fastapi import UploadFile, File
import magic
import os
from typing import Tuple, Optional
from config import ENABLE_AZURE_SPEECH, MAX_FILE_SIZE
from handlers import (
    pdf,
    word,
    ppt,
    xlsx,
    image,
    speech,
)
from store.store import process_all


async def read_file_size(file: UploadFile) -> float:
    """Read file size and return it in MiB."""
    try:
        # 使用文件的size属性（如果可用）
        if hasattr(file, "size"):
            return file.size / 1024 / 1024
            
        # 否则读取文件内容计算大小
        file_size = 0
        chunk_size = 20480  # 20KB chunks
        while chunk := await file.read(chunk_size):
            file_size += len(chunk)
        await file.seek(0)
        return file_size / 1024 / 1024
    except Exception as e:
        raise ValueError(f"Failed to read file size: {str(e)}")


def get_file_type(filename: str, content: Optional[bytes] = None) -> Tuple[str, str]:
    """
    Get file type using both extension and content.
    Returns: (type_category, mime_type)
    """
    # 从文件名获取扩展名
    ext = os.path.splitext(filename.lower())[1][1:] if "." in filename else ""
    
    # 如果有文件内容，使用 magic 检测实际类型
    if content:
        mime_type = magic.from_buffer(content, mime=True)
        
        # 映射 MIME 类型到我们的类型分类
        if mime_type.startswith("image/"):
            return "image", mime_type
        elif mime_type == "application/pdf":
            return "pdf", mime_type
        elif mime_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            return "docx", mime_type
        elif mime_type in ["application/vnd.ms-powerpoint", "application/vnd.openxmlformats-officedocument.presentationml.presentation"]:
            return "pptx", mime_type
        elif mime_type in ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
            return "xlsx", mime_type
        elif mime_type.startswith("audio/") or mime_type.startswith("video/"):
            return "media", mime_type
        elif mime_type.startswith("text/"):
            return "text", mime_type
    
    # 如果没有内容或无法识别，使用扩展名
    type_map = {
        "pdf": "pdf",
        "doc": "docx", "docx": "docx",
        "ppt": "pptx", "pptx": "pptx",
        "xls": "xlsx", "xlsx": "xlsx",
        "jpg": "image", "jpeg": "image", "png": "image", "gif": "image", "webp": "image",
        "mp3": "media", "wav": "media", "ogg": "media", "m4a": "media",
        "txt": "text", "md": "text", "json": "text"
    }
    
    return type_map.get(ext, "unknown"), f"application/{ext}" if ext else "application/octet-stream"


async def process_file(
        file: UploadFile = File(...),
        enable_ocr: bool = False,
        enable_vision: bool = True,
        save_all: bool = False,
) -> Tuple[str, str]:
    """Process file and return its contents."""
    try:
        # 检查文件大小
        if MAX_FILE_SIZE > 0:
            file_size = await read_file_size(file)
            if file_size > MAX_FILE_SIZE:
                raise ValueError(f"File size {file_size:.2f} MiB exceeds the limit of {MAX_FILE_SIZE} MiB.")

        # 读取文件内容用于类型检测
        content = await file.read()
        await file.seek(0)
        
        # 获取文件类型
        file_type, mime_type = get_file_type(file.filename, content)

        # 如果启用了保存所有文件
        if save_all:
            return file_type, await process_all(file)

        # 根据文件类型处理
        if file_type == "pdf":
            return "pdf", await pdf.process(
                file,
                enable_ocr=enable_ocr,
                enable_vision=enable_vision,
            )
        elif file_type == "docx":
            return "docx", word.process(file)
        elif file_type == "pptx":
            return "pptx", ppt.process(file)
        elif file_type == "xlsx":
            return "xlsx", xlsx.process(file)
        elif file_type == "image":
            return "image", await image.process(
                file,
                enable_ocr=enable_ocr,
                enable_vision=enable_vision,
            )
        elif file_type == "media" and ENABLE_AZURE_SPEECH:
            return "audio", speech.process(file)
        elif file_type == "text":
            return "text", content.decode("utf-8", errors="replace")
        else:
            # 对于未知类型，如果开启了save_all则保存文件
            if save_all:
                return file_type, await process_all(file)
            raise ValueError(f"Unsupported file type: {mime_type}")
            
    except Exception as e:
        raise ValueError(f"Failed to process file: {str(e)}")
