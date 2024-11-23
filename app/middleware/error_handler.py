"""
Error handling middleware.
"""
from typing import Callable, Awaitable, Any, Dict, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from ..core.errors import AppError, handle_error
from ..config import config
from ..utils.exceptions import (
    ProcessingError,
    ValidationError,
    StorageError,
    ConfigError
)

class ErrorHandlerMiddleware:
    """Error handling middleware."""
    
    def __init__(self, app: Any):
        """Initialize middleware.
        
        Args:
            app: FastAPI application
        """
        self.app = app
        
    async def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Handle request.
        
        Args:
            request: FastAPI request
            call_next: Next middleware in chain
            
        Returns:
            Response
        """
        try:
            # Process request
            response = await call_next(request)
            return response
            
        except ProcessingError as exc:
            return JSONResponse(
                status_code=400,
                content={
                    "code": "PROCESSING_ERROR",
                    "message": str(exc),
                    "data": {"error_type": "processing"}
                }
            )
            
        except ValidationError as exc:
            return JSONResponse(
                status_code=400,
                content={
                    "code": "VALIDATION_ERROR",
                    "message": str(exc),
                    "data": {"error_type": "validation"}
                }
            )
            
        except StorageError as exc:
            return JSONResponse(
                status_code=500,
                content={
                    "code": "STORAGE_ERROR",
                    "message": str(exc),
                    "data": {"error_type": "storage"}
                }
            )
            
        except ConfigError as exc:
            return JSONResponse(
                status_code=500,
                content={
                    "code": "CONFIG_ERROR",
                    "message": str(exc),
                    "data": {"error_type": "config"}
                }
            )
            
        except Exception as exc:
            # Convert exception to AppError
            error = handle_error(exc)
            
            # Get current config
            cfg = config()
            
            # Format error response
            error_response = {
                cfg.response.code_field: error.code.value,
                cfg.response.message_field: error.message,
                cfg.response.data_field: error.details
            }
            
            # Return JSON response
            return JSONResponse(
                status_code=error.http_status,
                content=error_response
            )

def format_error_response(
    error: AppError,
    include_details: bool = False
) -> Dict[str, Any]:
    """Format error for response.
    
    Args:
        error: Error to format
        include_details: Include error details in response
        
    Returns:
        Formatted error response
    """
    # Get current config
    cfg = config()
    
    # Basic error response
    response = {
        cfg.response.code_field: error.code.value,
        cfg.response.message_field: error.message,
    }
    
    # Add details if requested
    if include_details and error.details:
        response[cfg.response.data_field] = error.details
        
    return response
