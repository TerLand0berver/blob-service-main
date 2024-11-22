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

def get_origin_domain(request: Request) -> str:
    """Get domain from origin header or referer."""
    origin = request.headers.get("origin")
    if origin:
        try:
            return urlparse(origin).netloc
        except:
            pass
    
    referer = request.headers.get("referer")
    if referer:
        try:
            return urlparse(referer).netloc
        except:
            pass
            
    return ""

def is_browser_resource(path: str) -> bool:
    """Check if path is a browser-only resource that should always be accessible."""
    browser_resources = {
        "/favicon.ico",
        "/robots.txt",
        "/.well-known/",
        "/static/",
    }
    return any(path.startswith(prefix) for prefix in browser_resources)

def is_root_endpoint(path: str) -> bool:
    """Check if path is a root endpoint."""
    return path.startswith("/root")

def is_api_endpoint(path: str) -> bool:
    """Check if path is an API endpoint."""
    return path.startswith("/api/") or path == "/"

def check_auth(request: Request) -> bool:
    """Check if request has valid authentication."""
    auth = request.headers.get("Authorization")
    if not auth:
        return False
        
    try:
        scheme, credentials = auth.split()
        if scheme.lower() != "basic":
            return False
            
        decoded = base64.b64decode(credentials).decode("utf-8")
        username, password = decoded.split(":")
        
        return secrets.compare_digest(username, ADMIN_USER) and \
               secrets.compare_digest(password, ADMIN_PASSWORD)
                
    except Exception:
        return False

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Always allow OPTIONS requests for CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)
            
        # Always allow browser resources
        if is_browser_resource(path):
            return await call_next(request)
            
        # Check if client is whitelisted
        client_ip = get_client_ip(request)
        domain = get_origin_domain(request)
        is_whitelisted = (not WHITELIST_DOMAINS and not WHITELIST_IPS) or \
                        (WHITELIST_DOMAINS and is_domain_allowed(domain)) or \
                        (WHITELIST_IPS and is_ip_allowed(client_ip))
        
        # Root endpoints
        if is_root_endpoint(path):
            # Root page is always accessible
            if path == "/root":
                return await call_next(request)
                
            # Root config endpoints require authentication
            if not check_auth(request):
                raise HTTPException(
                    status_code=401,
                    detail="Unauthorized",
                    headers={"WWW-Authenticate": "Basic"},
                )
            return await call_next(request)
            
        # API endpoints and main page
        if is_api_endpoint(path):
            if not is_whitelisted:
                raise HTTPException(
                    status_code=403,
                    detail="This endpoint is only accessible by whitelisted clients"
                )
            return await call_next(request)
        
        # All other paths require whitelisting
        if not is_whitelisted:
            raise HTTPException(
                status_code=403,
                detail="Access denied. Please configure access through /root"
            )
            
        return await call_next(request)
