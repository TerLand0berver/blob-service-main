"""
API dependencies.
"""
from typing import Optional, Annotated
from fastapi import Depends, HTTPException, Header, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from ..config import config
from ..core.errors import AuthError, ValidationError

# Basic auth scheme
security = HTTPBasic()

def get_auth_header(
    authorization: Optional[str] = Header(None)
) -> Optional[str]:
    """Get authorization header.
    
    Args:
        authorization: Authorization header
        
    Returns:
        Authorization token if present
    """
    return authorization

def verify_auth(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)]
) -> None:
    """Verify basic auth credentials.
    
    Args:
        credentials: Basic auth credentials
        
    Raises:
        AuthError: If authentication fails
    """
    # Get config
    cfg = config()
    
    # Skip auth if not required
    if not cfg.auth.require_auth:
        return
        
    # Verify credentials
    correct_username = secrets.compare_digest(
        credentials.username.encode("utf8"),
        cfg.auth.admin_user.encode("utf8")
    )
    correct_password = secrets.compare_digest(
        credentials.password.encode("utf8"),
        cfg.auth.admin_password.encode("utf8")
    )
    
    if not (correct_username and correct_password):
        raise AuthError("Invalid credentials")

def verify_token(
    token: Annotated[Optional[str], Depends(get_auth_header)]
) -> None:
    """Verify JWT token.
    
    Args:
        token: JWT token
        
    Raises:
        AuthError: If token is invalid
    """
    # Get config
    cfg = config()
    
    # Skip auth if not required
    if not cfg.auth.require_auth:
        return
        
    # Verify token is present
    if not token:
        raise AuthError("Missing authorization token")
        
    # TODO: Implement JWT verification
    # This is a placeholder for JWT token verification
    # We'll implement this when adding JWT support
    pass

def verify_content_length(request: Request) -> None:
    """Verify request content length.
    
    Args:
        request: FastAPI request
        
    Raises:
        ValidationError: If content length exceeds limit
    """
    # Get config
    cfg = config()
    
    # Skip check if no limit set
    if cfg.storage.max_file_size <= 0:
        return
        
    # Get content length
    content_length = request.headers.get("content-length")
    if not content_length:
        return
        
    # Verify size
    try:
        size = int(content_length)
        if size > cfg.storage.max_file_size:
            raise ValidationError(
                f"File size {size} exceeds limit {cfg.storage.max_file_size}"
            )
    except ValueError:
        raise ValidationError("Invalid content length header")

def verify_cors_origin(
    origin: Optional[str] = Header(None)
) -> None:
    """Verify CORS origin.
    
    Args:
        origin: Origin header
        
    Raises:
        ValidationError: If origin is not allowed
    """
    # Get config
    cfg = config()
    
    # Skip check if all origins allowed
    if "*" in cfg.cors_origins:
        return
        
    # Verify origin is allowed
    if origin and origin not in cfg.cors_origins:
        raise ValidationError(f"Origin {origin} not allowed")

# Common dependencies
CommonDeps = Annotated[None, Depends(verify_auth)]
TokenDeps = Annotated[None, Depends(verify_token)]
ContentDeps = Annotated[None, Depends(verify_content_length)]
CorsDeps = Annotated[None, Depends(verify_cors_origin)]
