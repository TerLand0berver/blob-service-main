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
        "/static/",
    }
    return any(path.startswith(prefix) for prefix in browser_resources)

def is_api_endpoint(path: str) -> bool:
    """Check if path is an API endpoint."""
    return path.startswith("/api/")

def is_config_endpoint(path: str) -> bool:
    """Check if path is a config endpoint."""
    return path.startswith("/api/config") or path == "/config"

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
        
        # API endpoints only accessible by whitelisted clients
        if is_api_endpoint(path):
            if not is_whitelisted:
                raise HTTPException(
                    status_code=403,
                    detail="API endpoints are only accessible by whitelisted clients"
                )
            return await call_next(request)
            
        # Config endpoints always require authentication
        if is_config_endpoint(path):
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
        
        # All other paths are accessible
        return await call_next(request)
