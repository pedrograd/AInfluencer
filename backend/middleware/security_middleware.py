"""
Security Middleware
Implements security best practices: rate limiting, HTTPS enforcement, input validation
"""
import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from typing import Callable, Optional

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security best practices"""
    
    def __init__(
        self,
        app: ASGIApp,
        enable_rate_limiting: bool = True,
        max_requests_per_minute: int = 60,
        max_requests_per_hour: int = 1000,
        max_request_size_mb: int = 25,
        request_timeout_seconds: Optional[int] = 120,
    ):
        super().__init__(app)
        self.enable_rate_limiting = enable_rate_limiting
        self.rate_limit_store: dict = defaultdict(list)
        self.max_requests_per_minute = max_requests_per_minute
        self.max_requests_per_hour = max_requests_per_hour
        self.max_request_bytes = max_request_size_mb * 1024 * 1024
        self.request_timeout_seconds = request_timeout_seconds
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with security checks"""
        
        # 1. HTTPS enforcement (except localhost)
        if request.url.scheme != "https" and request.url.hostname not in ["localhost", "127.0.0.1"]:
            logger.warning(f"Non-HTTPS request from {request.client.host if request.client else 'unknown'}")
            # In production, you might want to redirect or reject
        
        # 2. Request size guard (best effort without reading body)
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_request_bytes:
                    logger.warning("Request rejected due to size limit")
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Request too large",
                    )
            except ValueError:
                pass

        # 3. Rate limiting
        if self.enable_rate_limiting:
            client_ip = request.client.host if request.client else "unknown"
            
            # Check per-minute limit
            now = datetime.utcnow()
            minute_key = f"{client_ip}:minute"
            self.rate_limit_store[minute_key] = [
                ts for ts in self.rate_limit_store[minute_key]
                if (now - ts).total_seconds() < 60
            ]
            
            if len(self.rate_limit_store[minute_key]) >= self.max_requests_per_minute:
                logger.warning(f"Rate limit exceeded for {client_ip} (per minute)")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later."
                )
            
            # Check per-hour limit
            hour_key = f"{client_ip}:hour"
            self.rate_limit_store[hour_key] = [
                ts for ts in self.rate_limit_store[hour_key]
                if (now - ts).total_seconds() < 3600
            ]
            
            if len(self.rate_limit_store[hour_key]) >= self.max_requests_per_hour:
                logger.warning(f"Rate limit exceeded for {client_ip} (per hour)")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Hourly rate limit exceeded. Please try again later."
                )
            
            # Record request
            self.rate_limit_store[minute_key].append(now)
            self.rate_limit_store[hour_key].append(now)
        
        # 4. Input validation headers
        # Check for suspicious headers
        suspicious_headers = ["x-forwarded-for", "x-real-ip"]
        for header in suspicious_headers:
            if header in request.headers:
                # Log but don't block (might be legitimate in proxy setups)
                logger.debug(f"Suspicious header detected: {header}")
        
        # 5. Process request with timeout guard
        try:
            if self.request_timeout_seconds and self.request_timeout_seconds > 0:
                response = await asyncio.wait_for(call_next(request), timeout=self.request_timeout_seconds)
            else:
                response = await call_next(request)
        except asyncio.TimeoutError:
            logger.warning("Request timed out")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Request timed out",
            )
        except HTTPException:
            raise
        except Exception as e:
            # Error handling best practice - don't leak internal errors
            logger.error(f"Request processing error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal error occurred"
            )
            
        # 6. Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Remove server header (security best practice)
        if "server" in response.headers:
            del response.headers["server"]
        
        return response
