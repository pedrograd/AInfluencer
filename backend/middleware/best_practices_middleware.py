"""
Best Practices Middleware
Enforces best practices on API requests and responses
"""
import logging
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from services.best_practices_service import BestPracticesService, PracticeCategory, PracticeSeverity

logger = logging.getLogger(__name__)


class BestPracticesMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce best practices"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.best_practices = BestPracticesService()
        self.request_times: dict = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with best practices checks"""
        start_time = time.time()
        
        # Security checks
        if not request.url.scheme == "https" and request.url.hostname != "localhost":
            logger.warning(f"Non-HTTPS request detected: {request.url}")
        
        # Rate limiting check (basic implementation)
        client_ip = request.client.host if request.client else "unknown"
        if client_ip in self.request_times:
            last_request_time = self.request_times[client_ip]
            time_since_last = time.time() - last_request_time
            if time_since_last < 0.1:  # 100ms minimum between requests
                logger.warning(f"Rate limit warning for {client_ip}")
        
        self.request_times[client_ip] = time.time()
        
        # Process request
        try:
            response = await call_next(request)
            
            # Performance monitoring
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            
            # Log slow requests
            if process_time > 2.0:  # 2 seconds
                logger.warning(f"Slow request detected: {request.url.path} took {process_time:.2f}s")
            
            return response
            
        except Exception as e:
            # Error handling best practice
            logger.error(f"Request error: {e}", exc_info=True)
            raise
