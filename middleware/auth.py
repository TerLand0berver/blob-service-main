from fastapi import Request, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import secrets
import base64
from typing import Optional
from urllib.parse import urlparse

from config import (
    ADMIN_USER, ADMIN_PASSWORD, WHITELIST_DOMAINS, WHITELIST_IPS,
    REQUIRE_AUTH, is_ip_allowed, is_domain_allowed
)

security = HTTPBasic()

def get_client_ip(request: Request) -> str:
    """Get client IP from request headers or connection."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""

def is_browser_resource(path: str) -> bool:
    """Check if path is a browser-only resource that should always be accessible."""
    browser_resources = {
        "/favicon.ico",
        "/robots.txt",
        "/.well-known/",
    }
    return any(path.startswith(prefix) for prefix in browser_resources)

def is_static_file(path: str) -> bool:
    """Check if path is a static file."""
    return path.startswith("/static/")

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get client info
        origin = request.headers.get("origin")
        client_ip = get_client_ip(request)
        path = request.url.path
        
        # Always allow browser resources
        if is_browser_resource(path):
            return await call_next(request)
        
        # Check if client is whitelisted
        is_whitelisted = is_domain_allowed(origin) or is_ip_allowed(client_ip)
        
        # Check if request is for config endpoints
        is_config_endpoint = path.startswith("/api/config") or path == "/config"
        
        # If client is whitelisted and trying to access config, deny access
        if is_whitelisted and is_config_endpoint:
            raise HTTPException(
                status_code=403,
                detail="Whitelisted clients cannot modify configuration"
            )
        
        # If client is whitelisted, allow access
        if is_whitelisted:
            return await call_next(request)
        
        # If auth is not required and not accessing config
        if not REQUIRE_AUTH and not is_config_endpoint:
            # For static files and index page
            if is_static_file(path) or path == "/" or path == "/index.html":
                return await call_next(request)
            
            # For API endpoints, still require auth
            if not path.startswith("/api/"):
                return await call_next(request)
        
        # For all other cases, require authentication
        auth = request.headers.get("Authorization")
        if not auth:
            raise HTTPException(
                status_code=401,
                detail="Unauthorized",
                headers={"WWW-Authenticate": "Basic"},
            )
            
        try:
            scheme, credentials = auth.split()
            if scheme.lower() != "basic":
                raise HTTPException(status_code=401, detail="Invalid authentication scheme")
                
            decoded = base64.b64decode(credentials).decode("utf-8")
            username, password = decoded.split(":")
            
            if not secrets.compare_digest(username, ADMIN_USER) or \
               not secrets.compare_digest(password, ADMIN_PASSWORD):
                raise HTTPException(status_code=401, detail="Invalid credentials")
                
        except Exception as e:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        return await call_next(request)
