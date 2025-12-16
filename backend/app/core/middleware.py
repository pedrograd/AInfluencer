"""FastAPI middleware for rate limiting and error handling."""

from __future__ import annotations

import logging
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize rate limiter (uses in-memory storage by default)
limiter = Limiter(key_func=get_remote_address)


async def error_handler_middleware(request: Request, call_next: Callable) -> Response:
    """Centralized error handling middleware for FastAPI.
    
    Catches unhandled exceptions and returns standardized error responses.
    Logs errors for debugging and monitoring.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/endpoint in the chain
        
    Returns:
        Response with error details if exception occurred, otherwise normal response
    """
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        # Log the error
        logger.error(
            f"Unhandled exception in {request.method} {request.url.path}: {exc}",
            exc_info=True,
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": get_remote_address(request),
            },
        )
        
        # Return standardized error response
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred. Please try again later.",
                "detail": str(exc) if settings.app_env == "dev" else None,
            },
        )

