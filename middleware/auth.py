from fastapi import Request, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import secrets
from typing import Optional
from urllib.parse import urlparse

from config import ADMIN_USER, ADMIN_PASSWORD, WHITELIST_DOMAINS, REQUIRE_AUTH

security = HTTPBasic()

def is_whitelisted(origin: Optional[str]) -> bool:
    """Check if origin is whitelisted"""
    if not origin or not WHITELIST_DOMAINS:
        return False
    
    try:
        domain = urlparse(origin).netloc
        return domain in WHITELIST_DOMAINS
    except:
        return False

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for whitelisted domains
        origin = request.headers.get("origin")
        if is_whitelisted(origin):
            return await call_next(request)
            
        # Skip auth for static files and non-api paths
        if not REQUIRE_AUTH or request.url.path.startswith("/static/"):
            return await call_next(request)
            
        # Check auth header
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
