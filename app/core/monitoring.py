"""
Performance monitoring and metrics collection.
"""
import time
import logging
from typing import Callable, Dict, Any
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge
import psutil
from fastapi import Request
from app.core.config import config

logger = logging.getLogger(__name__)

# Metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

FILE_UPLOAD_SIZE = Histogram(
    'file_upload_size_bytes',
    'File upload size in bytes',
    ['content_type']
)

PROCESSING_TIME = Histogram(
    'file_processing_duration_seconds',
    'File processing duration',
    ['processor_type']
)

STORAGE_OPERATIONS = Counter(
    'storage_operations_total',
    'Storage operations',
    ['operation', 'status']
)

SYSTEM_MEMORY = Gauge(
    'system_memory_usage_bytes',
    'System memory usage'
)

SYSTEM_CPU = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage'
)

def monitor_request() -> Callable:
    """Request monitoring decorator."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get('request') or args[0]
            method = request.method
            endpoint = request.url.path
            
            start_time = time.time()
            try:
                response = await func(*args, **kwargs)
                status = response.status_code
                return response
            except Exception as e:
                status = getattr(e, 'status_code', 500)
                raise
            finally:
                duration = time.time() - start_time
                REQUEST_COUNT.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).inc()
                REQUEST_LATENCY.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
        return wrapper
    return decorator

def monitor_upload(func: Callable) -> Callable:
    """File upload monitoring decorator."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        file = kwargs.get('file')
        if not file:
            return await func(*args, **kwargs)
            
        content_type = getattr(file, 'content_type', 'unknown')
        size = getattr(file, 'size', 0)
        
        FILE_UPLOAD_SIZE.labels(
            content_type=content_type
        ).observe(size)
        
        return await func(*args, **kwargs)
    return wrapper

def monitor_processing(processor_type: str) -> Callable:
    """File processing monitoring decorator."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                PROCESSING_TIME.labels(
                    processor_type=processor_type
                ).observe(duration)
        return wrapper
    return decorator

def monitor_storage(operation: str) -> Callable:
    """Storage operation monitoring decorator."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                STORAGE_OPERATIONS.labels(
                    operation=operation,
                    status='success'
                ).inc()
                return result
            except Exception as e:
                STORAGE_OPERATIONS.labels(
                    operation=operation,
                    status='error'
                ).inc()
                raise
        return wrapper
    return decorator

async def collect_system_metrics():
    """Collect system metrics."""
    try:
        # Memory usage
        memory = psutil.virtual_memory()
        SYSTEM_MEMORY.set(memory.used)
        
        # CPU usage
        cpu = psutil.cpu_percent()
        SYSTEM_CPU.set(cpu)
        
    except Exception as e:
        logger.error(f"Error collecting system metrics: {e}")
