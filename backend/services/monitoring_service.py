"""
Monitoring Service for Prometheus Metrics
"""
import time
import logging
from typing import Dict, Any
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

logger = logging.getLogger(__name__)

# Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_connections = Gauge(
    'active_connections',
    'Number of active connections'
)

database_connections_active = Gauge(
    'database_connections_active',
    'Number of active database connections'
)

database_connections_max = Gauge(
    'database_connections_max',
    'Maximum database connections'
)

redis_connections_active = Gauge(
    'redis_connections_active',
    'Number of active Redis connections'
)

generation_jobs_pending = Gauge(
    'generation_jobs_pending',
    'Number of pending generation jobs'
)

generation_jobs_processing = Gauge(
    'generation_jobs_processing',
    'Number of processing generation jobs'
)

generation_jobs_completed = Counter(
    'generation_jobs_completed_total',
    'Total completed generation jobs',
    ['type', 'status']
)

gpu_memory_used = Gauge(
    'gpu_memory_used_bytes',
    'GPU memory used in bytes'
)

gpu_memory_total = Gauge(
    'gpu_memory_total_bytes',
    'Total GPU memory in bytes'
)

def track_request(method: str, endpoint: str):
    """Decorator to track HTTP requests"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 200
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = 500
                raise
            finally:
                duration = time.time() - start_time
                http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
                http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
        
        return wrapper
    return decorator

def get_metrics() -> Response:
    """Get Prometheus metrics"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

def update_connection_metrics(active: int, max_conn: int):
    """Update database connection metrics"""
    database_connections_active.set(active)
    database_connections_max.set(max_conn)

def update_generation_metrics(pending: int, processing: int):
    """Update generation job metrics"""
    generation_jobs_pending.set(pending)
    generation_jobs_processing.set(processing)

def increment_generation_completed(job_type: str, status: str):
    """Increment completed generation jobs counter"""
    generation_jobs_completed.labels(type=job_type, status=status).inc()

def update_gpu_metrics(used: int, total: int):
    """Update GPU memory metrics"""
    gpu_memory_used.set(used)
    gpu_memory_total.set(total)
