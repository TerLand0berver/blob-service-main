from typing import Any, Dict, Optional, Union
from fastapi.responses import JSONResponse, Response
from fastapi.encoders import jsonable_encoder
import secrets
import markdown2
import re
from config import (
    RESPONSE_CODE_FIELD,
    RESPONSE_MSG_FIELD,
    RESPONSE_SN_FIELD,
    RESPONSE_DATA_FIELD,
    RESPONSE_SUCCESS_CODE,
    RESPONSE_ERROR_CODE,
)

class ResponseFormatter:
    @staticmethod
    def format_file_url(url: str, filename: str = None) -> str:
        """Format file URL with proper markdown and spacing."""
        if not url:
            return url
            
        # 确保URL两端有空格
        url = f" {url.strip()} "
        
        # 如果有文件名，使用文件名格式
        if filename:
            return f"```file\n[[{filename}]]\n{url}\n```"
        else:
            # 从URL提取文件名
            match = re.search(r'/([^/]+)$', url)
            extracted_filename = match.group(1) if match else "file"
            return f"```file\n[[{extracted_filename}]]\n{url}\n```"

    @staticmethod
    def format_data(data: Any) -> Dict:
        """Format response data with support for markdown and special types."""
        if isinstance(data, dict):
            # 特殊处理文件URL
            if "url" in data and isinstance(data["url"], str):
                filename = data.get("filename", None)
                if data["url"]:  # 只有当URL非空时才格式化
                    data["url"] = ResponseFormatter.format_file_url(data["url"], filename)
            return {k: ResponseFormatter.format_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [ResponseFormatter.format_data(item) for item in data]
        elif isinstance(data, str) and data.startswith("```") and data.endswith("```"):
            # 处理已经是markdown格式的字符串
            return data
        else:
            return data

    @staticmethod
    def create_response(
        success: bool,
        message: str,
        data: Optional[Any] = None,
        status_code: int = 200,
        headers: Optional[Dict] = None,
        content_type: str = "application/json"
    ) -> Response:
        """Create a formatted response with support for different content types."""
        response_data = {
            RESPONSE_CODE_FIELD: RESPONSE_SUCCESS_CODE if success else RESPONSE_ERROR_CODE,
            RESPONSE_MSG_FIELD: message,
            RESPONSE_SN_FIELD: secrets.token_hex(8),
            RESPONSE_DATA_FIELD: ResponseFormatter.format_data(data) if data is not None else {}
        }

        # Convert to JSON-compatible format
        json_compatible_data = jsonable_encoder(response_data)

        # Create response with appropriate content type
        response = JSONResponse(
            content=json_compatible_data,
            status_code=status_code
        )

        # Add custom headers if provided
        if headers:
            for key, value in headers.items():
                response.headers[key] = value

        # Set content type
        response.headers["Content-Type"] = content_type

        return response

    @staticmethod
    def success(
        message: str = "Success",
        data: Optional[Any] = None,
        status_code: int = 200,
        headers: Optional[Dict] = None,
        content_type: str = "application/json"
    ) -> Response:
        """Create a success response."""
        return ResponseFormatter.create_response(
            success=True,
            message=message,
            data=data,
            status_code=status_code,
            headers=headers,
            content_type=content_type
        )

    @staticmethod
    def error(
        message: str = "Error",
        data: Optional[Any] = None,
        status_code: int = 400,
        headers: Optional[Dict] = None,
        content_type: str = "application/json"
    ) -> Response:
        """Create an error response."""
        return ResponseFormatter.create_response(
            success=False,
            message=message,
            data=data,
            status_code=status_code,
            headers=headers,
            content_type=content_type
        )
