"""
Main application module for the Blob Service.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.security import SecurityMiddleware
from app.middleware.auth import AuthMiddleware
from app.core.security_config import security_config
import logging
import logging.config
import os

# Configure logging
logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "json": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO"
        },
        "audit": {
            "class": "logging.FileHandler",
            "filename": security_config.audit_log_path,
            "formatter": "json",
            "level": "INFO"
        }
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "INFO"
        },
        "audit": {
            "handlers": ["audit"],
            "level": "INFO",
            "propagate": False
        }
    }
})

logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Blob Service",
    description="Secure blob storage and processing service",
    version="1.0.0"
)

# Add CORS middleware with security config
app.add_middleware(
    CORSMiddleware,
    allow_origins=security_config.access_control.cors_allow_origins,
    allow_credentials=True,
    allow_methods=security_config.access_control.cors_allow_methods,
    allow_headers=security_config.access_control.cors_allow_headers,
    expose_headers=security_config.access_control.cors_expose_headers,
    max_age=security_config.access_control.cors_max_age,
)

# Add security middleware
app.add_middleware(SecurityMiddleware)

# Add authentication middleware if required
if security_config.auth.require_auth:
    app.add_middleware(AuthMiddleware)

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# Import and include routers
from app.routers import auth, blobs, config

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(blobs.router, prefix="/api/blobs", tags=["blobs"])
app.include_router(config.router, prefix="/api/config", tags=["config"])

if __name__ == "__main__":
    import uvicorn
    # Ensure audit log directory exists
    os.makedirs(os.path.dirname(security_config.audit_log_path), exist_ok=True)
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        ssl_keyfile="./certs/key.pem",
        ssl_certfile="./certs/cert.pem",
    )
