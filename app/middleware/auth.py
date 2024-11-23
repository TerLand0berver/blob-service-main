from fastapi import Request
from fastapi.responses import RedirectResponse
from app.core.response import ResponseFormatter
from app.config import config
import ipaddress
from typing import List, Optional
import jwt
from datetime import datetime, timedelta
from passlib.hash import pbkdf2_sha256
import secrets

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
        self._token_blacklist = set()

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)
            
        request = Request(scope, receive=receive, send=send)
        
        # Check if path should be excluded from auth
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await self.app(scope, receive, send)

        # Get client IP and domain for logging
        client_ip = request.client.host if request.client else None
        client_domain = request.headers.get("host", "").split(":")[0]

        # First check authentication
        auth_result = await self._is_authenticated(request)
        if not auth_result.get("authenticated", False):
            # Only check whitelist if authentication fails
            if self._is_in_whitelist(client_ip, client_domain):
                return await self.app(scope, receive, send)
                
            if request.url.path.startswith("/api/"):
                # Return error for API requests
                response = ResponseFormatter.error(
                    message=auth_result.get("message", "Authentication required"),
                    status_code=401
                )
                return response(scope, receive, send)
            else:
                # Redirect to login page for other requests
                response = RedirectResponse(url="/login")
                return await response(scope, receive, send)
                
        # Add user info to request state
        request.state.user = auth_result.get("user")
        return await self.app(scope, receive, send)

    async def _is_authenticated(self, request: Request) -> dict:
        """Check if request has valid authentication"""
        try:
            auth_token = request.cookies.get("auth_token")
            if not auth_token:
                return {"authenticated": False, "message": "No auth token provided"}
                
            # Check token blacklist
            if auth_token in self._token_blacklist:
                return {"authenticated": False, "message": "Token has been revoked"}
                
            # Verify JWT token
            try:
                payload = jwt.decode(
                    auth_token,
                    config.JWT_SECRET_KEY,
                    algorithms=["HS256"]
                )
            except jwt.ExpiredSignatureError:
                return {"authenticated": False, "message": "Token has expired"}
            except jwt.InvalidTokenError:
                return {"authenticated": False, "message": "Invalid token"}
            
            # Check if token is expired
            exp = datetime.fromtimestamp(payload["exp"])
            if exp < datetime.utcnow():
                return {"authenticated": False, "message": "Token has expired"}
                
            # Check if token needs refresh
            if self._should_refresh_token(exp):
                new_token = self._generate_token(payload["sub"])
                # Implementation of token refresh response should be handled in the route
                
            # Add user info to response
            return {
                "authenticated": True,
                "user": {
                    "username": payload["sub"],
                    "roles": payload.get("roles", []),
                    "permissions": payload.get("permissions", [])
                }
            }
            
        except Exception as e:
            return {"authenticated": False, "message": str(e)}

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

    def _should_refresh_token(self, exp: datetime) -> bool:
        """Check if token should be refreshed"""
        # Refresh token if it's going to expire in the next hour
        return exp - datetime.utcnow() < timedelta(hours=1)

    def _generate_token(self, username: str, roles: List[str] = None, permissions: List[str] = None) -> str:
        """Generate a new JWT token"""
        exp = datetime.utcnow() + timedelta(hours=24)
        payload = {
            "sub": username,
            "exp": exp,
            "iat": datetime.utcnow(),
            "jti": secrets.token_hex(16),
            "roles": roles or [],
            "permissions": permissions or []
        }
        return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm="HS256")

    def blacklist_token(self, token: str):
        """Add token to blacklist"""
        self._token_blacklist.add(token)
        # TODO: Implement token blacklist cleanup mechanism
