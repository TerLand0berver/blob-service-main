"""
Security middleware for request/response validation and security headers.
"""
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.core.security_config import security_config
import ipaddress
from urllib.parse import urlparse
import time
import logging

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
    ) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # Start timing the request
        start_time = time.time()
        
        # Validate request before processing
        if security_config.enable_request_validation:
            try:
                await self._validate_request(request)
            except Exception as e:
                logger.error(f"Request validation failed: {str(e)}")
                return Response(
                    content=str(e),
                    status_code=400,
                )

        # Process the request
        response = await call_next(request)

        # Add security headers
        response.headers.update(security_config.secure_headers)

        # Add Content Security Policy if enabled
        if security_config.enable_content_security_policy:
            csp_value = self._build_csp_header()
            response.headers["Content-Security-Policy"] = csp_value

        # Validate response if enabled
        if security_config.enable_response_validation:
            try:
                await self._validate_response(response)
            except Exception as e:
                logger.error(f"Response validation failed: {str(e)}")
                return Response(
                    content=str(e),
                    status_code=500,
                )

        # Log request details if audit logging is enabled
        if security_config.enable_audit_log:
            self._audit_log(request, response, time.time() - start_time)

        return response

    async def _validate_request(self, request: Request) -> None:
        """Validate incoming request."""
        # Check if path is public
        if request.url.path in security_config.access_control.public_paths:
            return

        # Validate IP whitelist
        client_ip = request.client.host
        if not self._is_ip_allowed(client_ip):
            raise ValueError(f"IP {client_ip} is not in whitelist")

        # Validate domain whitelist for specific endpoints
        referer = request.headers.get("referer")
        if referer and not self._is_domain_allowed(referer):
            raise ValueError(f"Domain from referer {referer} is not in whitelist")

        # Additional request validation logic can be added here
        # For example, validating request size, content type, etc.

    async def _validate_response(self, response: Response) -> None:
        """Validate outgoing response."""
        # Add validation logic for responses
        # For example, checking for sensitive data patterns
        pass

    def _is_ip_allowed(self, ip: str) -> bool:
        """Check if IP is in whitelist."""
        if not security_config.access_control.whitelist_ips:
            return True

        try:
            client_ip = ipaddress.ip_address(ip)
            for allowed in security_config.access_control.whitelist_ips:
                if "/" in allowed:  # CIDR notation
                    if client_ip in ipaddress.ip_network(allowed):
                        return True
                else:
                    if client_ip == ipaddress.ip_address(allowed):
                        return True
            return False
        except ValueError:
            return False

    def _is_domain_allowed(self, url: str) -> bool:
        """Check if domain is in whitelist."""
        if not security_config.access_control.whitelist_domains:
            return True

        try:
            domain = urlparse(url).netloc.lower()
            for pattern in security_config.access_control.whitelist_domains:
                if pattern.startswith("*."):
                    if domain.endswith(pattern[2:]):
                        return True
                elif domain == pattern:
                    return True
            return False
        except Exception:
            return False

    def _build_csp_header(self) -> str:
        """Build Content Security Policy header value."""
        parts = []
        for directive, sources in security_config.content_security_policy.items():
            if sources:
                parts.append(f"{directive} {' '.join(sources)}")
        return "; ".join(parts)

    def _audit_log(
        self, request: Request, response: Response, duration: float
    ) -> None:
        """Log request and response details."""
        log_data = {
            "timestamp": time.time(),
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host,
            "status_code": response.status_code,
            "duration": duration,
            "user_agent": request.headers.get("user-agent"),
        }
        
        # Add authentication info if available
        if hasattr(request.state, "user"):
            log_data["user"] = request.state.user

        logger.info("Audit log entry", extra=log_data)
