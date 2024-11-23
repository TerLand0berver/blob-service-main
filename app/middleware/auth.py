from fastapi import Request
from fastapi.responses import RedirectResponse
from app.core.response import ResponseFormatter
from app.config import config
import ipaddress
from typing import List
import jwt
from datetime import datetime, timedelta

class AuthMiddleware:
    def __init__(
        self,
        app,
        exclude_paths: List[str] = [
            "/static",
            "/favicon.ico",
            "/login",
            "/api/auth/login",
        ],
    ):
        self.app = app
        self.exclude_paths = exclude_paths
        
    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)
            
        request = Request(scope, receive=receive, send=send)
        
        # Check if path should be excluded from auth
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await self.app(scope, receive, send)
            
        # Get client IP and domain
        client_ip = request.client.host if request.client else None
        client_domain = request.headers.get("host", "").split(":")[0]
        
        # Check whitelist
        if self._is_in_whitelist(client_ip, client_domain):
            return await self.app(scope, receive, send)
            
        # Check authentication
        if not await self._is_authenticated(request):
            if request.url.path.startswith("/api/"):
                # Return error for API requests
                response = ResponseFormatter.error(
                    message="Authentication required",
                    status_code=401
                )
                return response(scope, receive, send)
            else:
                # Redirect to login page for other requests
                response = RedirectResponse(url="/login")
                return await response(scope, receive, send)
                
        return await self.app(scope, receive, send)
        
    def _is_in_whitelist(self, client_ip: str, client_domain: str) -> bool:
        """Check if client IP or domain is in whitelist"""
        if not config.REQUIRE_AUTH:
            return True
            
        # Check IP whitelist
        if client_ip and config.WHITELIST_IPS:
            for allowed_ip in config.WHITELIST_IPS:
                try:
                    if "/" in allowed_ip:  # CIDR notation
                        network = ipaddress.ip_network(allowed_ip)
                        if ipaddress.ip_address(client_ip) in network:
                            return True
                    elif client_ip == allowed_ip:  # Exact IP match
                        return True
                except ValueError:
                    continue
                    
        # Check domain whitelist
        if client_domain and config.WHITELIST_DOMAINS:
            return any(
                client_domain.endswith(domain.lstrip("*."))
                for domain in config.WHITELIST_DOMAINS
            )
            
        return False
        
    async def _is_authenticated(self, request: Request) -> bool:
        """Check if request has valid authentication"""
        try:
            auth_token = request.cookies.get("auth_token")
            if not auth_token:
                return False
                
            # Verify JWT token
            payload = jwt.decode(
                auth_token,
                config.JWT_SECRET_KEY,
                algorithms=["HS256"]
            )
            
            # Check if token is expired
            exp = datetime.fromtimestamp(payload["exp"])
            if exp < datetime.utcnow():
                return False
                
            return True
            
        except Exception:
            return False
