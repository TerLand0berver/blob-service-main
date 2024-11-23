from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.response import ResponseFormatter
import time
from collections import defaultdict
import threading

class RateLimiter:
    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_limit: int = 10
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.requests = defaultdict(list)
        self._cleanup_lock = threading.Lock()
        
    def _cleanup_old_requests(self, client_ip: str):
        """Remove requests older than 1 minute"""
        current_time = time.time()
        with self._cleanup_lock:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if current_time - req_time < 60
            ]
    
    def is_rate_limited(self, client_ip: str) -> bool:
        current_time = time.time()
        self._cleanup_old_requests(client_ip)
        
        # Check burst limit
        requests_last_second = len([
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time <= 1
        ])
        if requests_last_second >= self.burst_limit:
            return True
            
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return True
            
        self.requests[client_ip].append(current_time)
        return False

class RateLimitMiddleware:
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_limit: int = 10
    ):
        self.app = app
        self.rate_limiter = RateLimiter(
            requests_per_minute=requests_per_minute,
            burst_limit=burst_limit
        )
        
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
            
        request = Request(scope, receive=receive, send=send)
        client_ip = request.client.host if request.client else None
        
        if client_ip and self.rate_limiter.is_rate_limited(client_ip):
            response = ResponseFormatter.error(
                message="Too many requests. Please try again later.",
                status_code=429
            )
            return await response(scope, receive, send)
            
        return await self.app(scope, receive, send)
