import os
import fitz  # PyMuPDF
import io
import requests
from typing import List, Dict, Any, Optional, Tuple, Union
from PIL import Image
import logging
import aiohttp
import asyncio
from datetime import datetime
from app.config import config
from app.utils.exceptions import ProcessingError, StorageError, OCRError, ValidationError
from fastapi import UploadFile

# 设置日志
logger = logging.getLogger(__name__)

def read_file_size(file_path: str) -> int:
    """Read file size in bytes"""
    return os.path.getsize(file_path)

def get_file_type(filename: str) -> Dict[str, str]:
    """Get file type information based on extension"""
    try:
        ext = filename.lower().split('.')[-1]
        for category, info in config.FILE_TYPE_MAPPINGS.items():
            if ext in info["extensions"]:
                return {
                    "type": category,
                    "icon": info["icon"],
                    "description": info["description"],
                    "processors": info.get("processors", [])
                }
        return {
            "type": "other",
            "icon": "📎",
            "description": "File",
            "processors": []
        }
    except Exception as e:
        logger.error(f"Error determining file type for {filename}: {str(e)}")
        raise ProcessingError(f"Could not determine file type: {str(e)}")

def format_markdown(template_key: str, **kwargs) -> str:
    """Format markdown text using template"""
    try:
        template = config.RESPONSE_FORMAT["markdown"].get(template_key, "{text}")
        return template.format(**kwargs)
    except KeyError as e:
        logger.error(f"Missing template key: {str(e)}")
        return kwargs.get("text", "")
    except Exception as e:
        logger.error(f"Error formatting markdown: {str(e)}")
        return kwargs.get("text", "")

def format_size(size: int) -> str:
    """Format file size to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}" if unit != 'B' else f"{size} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

async def process_file(
    file: UploadFile,
    config: Dict[str, Any],
    enable_ocr: bool = False,
    enable_vision: bool = True,
    save_all: bool = False,
) -> str:
    """Process uploaded file and return markdown formatted text"""
    try:
        # 验证输入
        if not file:
            raise ProcessingError("Empty file content")
        if not file.filename:
            raise ProcessingError("Missing filename")
        
        # 验证文件大小
        if file.size > config['max_file_size']:
            raise ValidationError(f"File size {file.size} exceeds maximum {config['max_file_size']}")
            
        # 获取文件类型信息
        file_type = get_file_type(file.filename)
        
        # 获取处理策略
        strategy = config.FILE_PROCESSING["save_all" if save_all else "default"]
        
        # 初始化响应部分
        response_parts = []
        
        # 处理save_all模式
        if save_all:
            # 保存文件并返回链接
            url = await save_to_storage(await file.read(), file.filename)
            template = "image" if file_type["type"] == "image" else "link"
            response_parts.append(format_markdown(template, text=file.filename, url=url))
            
            # 如果启用OCR且是PDF，提取图片文本
            if enable_ocr and file_type["type"] == "document" and file.filename.lower().endswith('.pdf'):
                pdf_images = extract_images_from_pdf(await file.read())
                if pdf_images:
                    image_texts = []
                    for idx, (image_data, _) in enumerate(pdf_images, 1):
                        ocr_result = await perform_ocr(image_data)
                        if ocr_result and ocr_result.get('text'):
                            image_texts.append(format_markdown("quote", 
                                text=f"Page {idx}: {ocr_result['text']}"
                            ))
                    if image_texts:
                        response_parts.append(format_markdown("heading", text="Extracted Text"))
                        response_parts.extend(image_texts)
            
            return format_markdown("newline").join(filter(None, response_parts))
        
        # 处理默认模式
        if file_type["type"] in strategy["extract_text_types"]:
            # 提取文本内容
            if "text" in file_type["processors"]:
                text_content = await extract_text(await file.read(), file_type["type"])
                if text_content:
                    response_parts.append(text_content)
            
            # 如果启用OCR且支持，提取OCR文本
            if enable_ocr and "ocr" in file_type["processors"]:
                if file_type["type"] == "document" and file.filename.lower().endswith('.pdf'):
                    # 特殊处理PDF
                    pdf_images = extract_images_from_pdf(await file.read())
                    if pdf_images:
                        image_texts = []
                        for idx, (image_data, _) in enumerate(pdf_images, 1):
                            ocr_result = await perform_ocr(image_data)
                            if ocr_result and ocr_result.get('text'):
                                image_texts.append(format_markdown("quote", 
                                    text=f"Page {idx}: {ocr_result['text']}"
                                ))
                        if image_texts:
                            response_parts.append(format_markdown("heading", text="Extracted Text"))
                            response_parts.extend(image_texts)
                else:
                    # 处理其他支持OCR的文件
                    ocr_result = await perform_ocr(await file.read())
                    if ocr_result and ocr_result.get('text'):
                        response_parts.append(format_markdown("quote", text=ocr_result['text']))
        
        return format_markdown("newline").join(filter(None, response_parts))
        
    except ProcessingError as e:
        logger.error(f"Processing error: {str(e)}")
        return format_markdown("quote", text=f"Error processing file: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return format_markdown("quote", text="An unexpected error occurred while processing the file")

async def save_to_storage(content: bytes, filename: str) -> str:
    """Save file to storage and return URL"""
    try:
        if config.FILE_API_ENDPOINT:
            return await save_to_api(content, filename)
        else:
            return await save_to_local(content, filename)
    except Exception as e:
        logger.error(f"Error saving file {filename}: {str(e)}")
        raise StorageError(f"Could not save file: {str(e)}")

async def save_to_api(content: bytes, filename: str) -> str:
    """Save file to API storage"""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {config.FILE_API_KEY}"}
            data = aiohttp.FormData()
            data.add_field('file',
                         content,
                         filename=filename,
                         content_type='application/octet-stream')
            
            async with session.post(config.FILE_API_ENDPOINT,
                                  data=data,
                                  headers=headers,
                                  timeout=30) as response:
                if response.status != 200:
                    raise StorageError(f"API returned status {response.status}")
                result = await response.json()
                return result["url"]
    except asyncio.TimeoutError:
        raise StorageError("API request timed out")
    except Exception as e:
        raise StorageError(f"API storage error: {str(e)}")

async def save_to_local(content: bytes, filename: str) -> str:
    """Save file to local storage"""
    try:
        # 确保文件名安全
        safe_filename = os.path.basename(filename)
        # 添加时间戳避免文件名冲突
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_filename = f"{timestamp}_{safe_filename}"
        
        # 构建存储路径
        storage_path = os.path.join(config.STORAGE_PATH, final_filename)
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        
        # 写入文件
        with open(storage_path, 'wb') as f:
            f.write(content)
        
        # 返回可访问的URL
        return f"{config.STORAGE_URL}/{final_filename}"
    except Exception as e:
        raise StorageError(f"Local storage error: {str(e)}")

async def perform_ocr(image_data: bytes) -> Optional[Dict[str, str]]:
    """Perform OCR on image data"""
    if not config.OCR_ENDPOINT:
        return None
        
    try:
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('image',
                          image_data,
                          filename='image.png',
                          content_type='image/png')
            
            async with session.post(config.OCR_ENDPOINT,
                                  data=data,
                                  timeout=30) as response:
                if response.status != 200:
                    logger.error(f"OCR API returned status {response.status}")
                    return None
                    
                result = await response.json()
                return {
                    "text": result.get("text", ""),
                    "confidence": result.get("confidence", 0)
                }
    except asyncio.TimeoutError:
        logger.error("OCR API request timed out")
        return None
    except Exception as e:
        logger.error(f"OCR error: {str(e)}")
        return None

async def extract_text(content: bytes, file_type: str) -> Optional[str]:
    """Extract text content from file based on type"""
    try:
        if file_type == "document":
            # 使用合适的库处理不同类型的文档
            if content.startswith(b'%PDF'):
                return await extract_pdf_text(content)
            else:
                return content.decode('utf-8', errors='ignore')
        elif file_type == "code":
            return content.decode('utf-8', errors='ignore')
        elif file_type == "spreadsheet":
            # 使用pandas或其他库处理电子表格
            return await extract_spreadsheet_text(content)
        return None
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}")
        return None

def get_image_metadata(image_data: bytes) -> Dict[str, Any]:
    """Get image metadata such as dimensions and format"""
    try:
        image = Image.open(io.BytesIO(image_data))
        return {
            "width": image.width,
            "height": image.height,
            "format": image.format.lower()
        }
    except Exception as e:
        logger.error(f"Error getting image metadata: {str(e)}")
        return {}

def extract_images_from_pdf(pdf_content: bytes) -> List[Tuple[bytes, str]]:
    """Extract images from PDF content"""
    images = []
    try:
        # Load PDF from memory
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        
        # Process each page
        for page_num in range(len(pdf_document)):
            if len(images) >= config.PDF_MAX_IMAGES:
                break
                
            page = pdf_document[page_num]
            image_list = page.get_images()
            
            # Extract each image
            for img_idx, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = pdf_document.extract_image(xref)
                    image_data = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    images.append((image_data, image_ext))
                    
                except Exception as e:
                    logger.error(f"Error extracting image {img_idx} from page {page_num}: {str(e)}")
                    continue
                    
                if len(images) >= config.PDF_MAX_IMAGES:
                    break
        
        pdf_document.close()
        return images
        
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return []
