import os
from datetime import datetime
import hashlib
import uuid
from typing import Optional

def md5_encode(text: str) -> str:
    """计算文本的MD5哈希值"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def generate_unique_id() -> str:
    """生成唯一标识符"""
    return str(uuid.uuid4())

def store_filename(original_filename: str, prefix: Optional[str] = None) -> str:
    """
    生成存储文件名
    
    Args:
        original_filename: 原始文件名
        prefix: 可选的文件名前缀
    
    Returns:
        str: 生成的存储文件名
    """
    # 获取文件扩展名
    _, ext = os.path.splitext(original_filename)
    if not ext:
        ext = '.bin'  # 默认扩展名
    
    # 生成基础文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = generate_unique_id()[:8]
    
    # 组合文件名
    if prefix:
        base_name = f"{prefix}_{timestamp}_{unique_id}"
    else:
        base_name = f"{timestamp}_{unique_id}"
    
    # 确保文件名安全
    base_name = "".join(c for c in base_name if c.isalnum() or c in '_-')
    
    return f"{base_name}{ext.lower()}"

def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不安全字符
    
    Args:
        filename: 原始文件名
    
    Returns:
        str: 清理后的文件名
    """
    # 分离文件名和扩展名
    base_name, ext = os.path.splitext(filename)
    
    # 只保留字母、数字和安全的特殊字符
    safe_name = "".join(c for c in base_name if c.isalnum() or c in '_-')
    
    # 如果清理后的文件名为空，使用默认名称
    if not safe_name:
        safe_name = "file"
    
    # 返回清理后的完整文件名
    return f"{safe_name}{ext.lower()}"
