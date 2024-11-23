"""
API module.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ..config import config
from ..middleware.error_handler import ErrorHandlerMiddleware
from .routes import router

def create_app() -> FastAPI:
    """Create FastAPI application.
    
    Returns:
        FastAPI application
    """
    # Create app
    app = FastAPI(
        title="Blob Service API",
        description="File storage service API",
        version="0.1.0",  # TODO: Get from package
    )
    
    # Get config
    cfg = config()
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add error handler middleware
    app.add_middleware(ErrorHandlerMiddleware)
    
    # Include API router
    app.include_router(router, prefix="/api/v1")
    
    return app

# Export for convenience
app = create_app()

__all__ = [
    'app',
    'create_app',
]
