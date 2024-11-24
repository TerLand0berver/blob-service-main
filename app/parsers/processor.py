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
import aiofiles
import concurrent.futures
import signal

# 设置日志
logger = logging.getLogger(__name__)

def read_file_size(file_path: str) -> int:
    """Read file size in bytes"""
    return os.path.getsize(file_path)

def get_file_type(filename: str) -> Dict[str, str]:
    """Get file type information based on extension"""
    try:
        ext = filename.lower().split('.')[-1]
        
        # 文档类型
        document_extensions = {
            'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt',
            'md', 'markdown', 'rst', 'tex'
        }
        # 代码文件类型
        code_extensions = {
            'py', 'js', 'java', 'cpp', 'c', 'cs', 'php', 'rb',
            'go', 'rs', 'swift', 'kt', 'scala', 'sql', 'sh',
            'html', 'css', 'xml', 'json', 'yaml', 'yml'
        }
        # 电子表格类型
        spreadsheet_extensions = {
            'xls', 'xlsx', 'csv', 'ods'
        }
        # 图片类型
        image_extensions = {
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp',
            'tiff', 'svg'
        }
        
        if ext in document_extensions:
            return {
                "type": "document",
                "icon": "📄",
                "description": "Document",
                "processors": ["text", "ocr"] if ext == "pdf" else ["text"]
            }
        elif ext in code_extensions:
            return {
                "type": "code",
                "icon": "💻",
                "description": "Code",
                "processors": ["text"]
            }
        elif ext in spreadsheet_extensions:
            return {
                "type": "spreadsheet",
                "icon": "📊",
                "description": "Spreadsheet",
                "processors": ["text"]
            }
        elif ext in image_extensions:
            return {
                "type": "image",
                "icon": "🖼️",
                "description": "Image",
                "processors": ["ocr"]
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
        
        # 获取文件类型信息
        file_type = get_file_type(file.filename)
        
        # 验证文件大小
        file_size = 0
        chunk_size = 8192  # 8KB chunks
        async with aiofiles.tempfile.NamedTemporaryFile(delete=True) as temp_file:
            while chunk := await file.read(chunk_size):
                file_size += len(chunk)
                if file_size > config['max_file_size']:
                    raise ValidationError(
                        f"File size {format_size(file_size)} exceeds maximum {format_size(config['max_file_size'])}"
                    )
                await temp_file.write(chunk)
            
            # 重置文件指针
            await temp_file.seek(0)
            file_content = await temp_file.read()
        
        # 获取处理策略
        strategy = config.FILE_PROCESSING["save_all" if save_all else "default"]
        
        # 初始化响应部分
        response_parts = []
        
        # 处理save_all模式 - 只返回链接
        if save_all:
            url = await save_to_storage(file_content, file.filename)
            template = "image" if file_type["type"] == "image" else "link"
            return format_markdown(template, text=file.filename, url=url)
        
        # 处理OCR模式 - 返回文本和图片
        if enable_ocr and "ocr" in file_type["processors"]:
            # 保存原始文件
            url = await save_to_storage(file_content, file.filename)
            response_parts.append(format_markdown("link", text=file.filename, url=url))
            
            # 提取OCR文本
            if file_type["type"] == "document" and file.filename.lower().endswith('.pdf'):
                # 特殊处理PDF - 使用异步处理避免阻塞
                async with concurrent.futures.ProcessPoolExecutor() as pool:
                    pdf_images = await asyncio.get_event_loop().run_in_executor(
                        pool, extract_images_from_pdf, file_content
                    )
                
                if pdf_images:
                    image_texts = []
                    # 并发处理所有图片
                    async def process_image(idx: int, image_data: bytes, image_ext: str):
                        try:
                            # 保存提取的图片
                            image_filename = f"page_{idx}_{file.filename}.{image_ext}"
                            image_url = await save_to_storage(image_data, image_filename)
                            response_parts.append(format_markdown("image", text=f"Page {idx}", url=image_url))
                            
                            # 提取图片文本
                            ocr_result = await perform_ocr(image_data)
                            if ocr_result and ocr_result.get('text'):
                                return format_markdown("quote", text=f"Page {idx}: {ocr_result['text']}")
                            return None
                        except Exception as e:
                            logger.error(f"Error processing image {idx}: {str(e)}")
                            return None
                    
                    # 并发执行所有图片处理
                    tasks = [
                        process_image(idx, image_data, image_ext)
                        for idx, (image_data, image_ext) in enumerate(pdf_images, 1)
                    ]
                    results = await asyncio.gather(*tasks)
                    image_texts = [r for r in results if r is not None]
                    
                    if image_texts:
                        response_parts.append(format_markdown("heading", text="Extracted Text"))
                        response_parts.extend(image_texts)
            else:
                # 处理其他支持OCR的文件
                ocr_result = await perform_ocr(file_content)
                if ocr_result and ocr_result.get('text'):
                    response_parts.append(format_markdown("quote", text=ocr_result['text']))
            
            return format_markdown("newline").join(filter(None, response_parts))
        
        # 处理普通模式 - 只返回处理后的文本
        if file_type["type"] in strategy["extract_text_types"]:
            if "text" in file_type["processors"]:
                text_content = await extract_text(file_content, file_type["type"])
                if text_content:
                    return text_content
        
        # 如果无法处理，返回错误信息
        raise ProcessingError(f"Unsupported file type: {file_type['type']}")
        
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
        # 验证图片数据
        if not image_data:
            logger.error("Empty image data")
            return None
            
        # 准备OCR请求
        async with aiohttp.ClientSession() as session:
            # 添加重试机制
            for attempt in range(3):
                try:
                    data = aiohttp.FormData()
                    data.add_field('image',
                                image_data,
                                filename='image.png',
                                content_type='image/png')
                    
                    # 设置超时和重试策略
                    timeout = aiohttp.ClientTimeout(total=30)
                    async with session.post(config.OCR_ENDPOINT,
                                        data=data,
                                        timeout=timeout,
                                        headers={"Authorization": config.OCR_API_KEY}) as response:
                        if response.status == 200:
                            result = await response.json()
                            if not result:
                                logger.error("Empty OCR result")
                                return None
                                
                            return {
                                "text": result.get("text", ""),
                                "confidence": result.get("confidence", 0),
                                "language": result.get("language", ""),
                                "words": result.get("words", [])
                            }
                        elif response.status == 429:  # Rate limit
                            if attempt < 2:  # 最后一次尝试不等待
                                await asyncio.sleep(2 ** attempt)  # 指数退避
                                continue
                        else:
                            logger.error(f"OCR API returned status {response.status}")
                            return None
                            
                except asyncio.TimeoutError:
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    logger.error("OCR API request timed out")
                    return None
                except Exception as e:
                    logger.error(f"OCR attempt {attempt + 1} failed: {str(e)}")
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    break
                    
        return None
        
    except Exception as e:
        logger.error(f"OCR error: {str(e)}")
        return None

async def extract_text(content: bytes, file_type: str) -> Optional[str]:
    """Extract text content from file based on type"""
    try:
        if file_type == "document":
            # 检查文件头以确定具体类型
            if content.startswith(b'%PDF'):
                # PDF文件
                return await extract_pdf_text(content)
            elif content.startswith(b'PK\x03\x04'):
                # Word文档(.docx)
                return await extract_docx_text(content)
            elif content.startswith(b'{\\rtf1'):
                # RTF文档
                return await extract_rtf_text(content)
            elif content.startswith(b'\xD0\xCF\x11\xE0'):
                # 旧版Word文档(.doc)
                return await extract_doc_text(content)
            else:
                # 尝试作为纯文本处理
                return content.decode('utf-8', errors='ignore')
        elif file_type == "code":
            # 代码文件处理
            encodings = ['utf-8', 'gbk', 'latin1']
            for encoding in encodings:
                try:
                    return content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            # 如果所有编码都失败，使用忽略错误的方式解码
            return content.decode('utf-8', errors='ignore')
        elif file_type == "spreadsheet":
            return await extract_spreadsheet_text(content)
        return None
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}")
        return None

async def extract_pdf_text(content: bytes) -> Optional[str]:
    """Extract text from PDF file"""
    try:
        with fitz.open(stream=content, filetype="pdf") as doc:
            text = []
            for page in doc:
                text.append(page.get_text())
            return "\n".join(text)
    except Exception as e:
        logger.error(f"Error extracting PDF text: {str(e)}")
        return None

async def extract_docx_text(content: bytes) -> Optional[str]:
    """Extract text from DOCX file"""
    try:
        from docx import Document
        doc = Document(io.BytesIO(content))
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)
    except Exception as e:
        logger.error(f"Error extracting DOCX text: {str(e)}")
        return None

async def extract_rtf_text(content: bytes) -> Optional[str]:
    """Extract text from RTF file"""
    try:
        import striprtf.striprtf
        rtf_text = content.decode('utf-8', errors='ignore')
        return striprtf.striprtf.rtf_to_text(rtf_text)
    except Exception as e:
        logger.error(f"Error extracting RTF text: {str(e)}")
        return None

async def extract_doc_text(content: bytes) -> Optional[str]:
    """Extract text from legacy DOC file"""
    try:
        import textract
        return textract.process(io.BytesIO(content), extension='.doc').decode('utf-8')
    except Exception as e:
        logger.error(f"Error extracting DOC text: {str(e)}")
        return None

async def extract_spreadsheet_text(content: bytes) -> Optional[str]:
    """Extract text from spreadsheet file"""
    try:
        import pandas as pd
        # 尝试Excel格式
        try:
            df = pd.read_excel(io.BytesIO(content))
            return df.to_string()
        except Exception:
            # 尝试CSV格式
            try:
                for encoding in ['utf-8', 'gbk', 'latin1']:
                    try:
                        df = pd.read_csv(io.BytesIO(content), encoding=encoding)
                        return df.to_string()
                    except UnicodeDecodeError:
                        continue
            except Exception:
                return None
    except Exception as e:
        logger.error(f"Error extracting spreadsheet text: {str(e)}")
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
        # 设置处理超时
        signal.alarm(30)  # 30秒超时
        
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
                    if not base_image:
                        continue
                        
                    image_data = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # 验证图片数据
                    if not image_data or len(image_data) == 0:
                        continue
                        
                    # 验证图片格式
                    if not image_ext or image_ext.lower() not in {'jpg', 'jpeg', 'png', 'webp'}:
                        continue
                        
                    # 验证图片大小
                    if len(image_data) > config.MAX_IMAGE_SIZE:
                        continue
                    
                    images.append((image_data, image_ext))
                    
                except Exception as e:
                    logger.error(f"Error extracting image {img_idx} from page {page_num}: {str(e)}")
                    continue
                    
                if len(images) >= config.PDF_MAX_IMAGES:
                    break
        
        # 清除超时
        signal.alarm(0)
        
        pdf_document.close()
        return images
        
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return []
    finally:
        # 确保清除超时
        signal.alarm(0)
