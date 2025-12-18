"""FastAPI middleware for rate limiting and error handling."""

from __future__ import annotations

import logging
from typing import Callable

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.error_taxonomy import classify_error, create_error_response, ErrorCode

logger = logging.getLogger(__name__)

# Initialize rate limiter (uses in-memory storage by default)
limiter = Limiter(key_func=get_remote_address)


async def error_handler_middleware(request: Request, call_next: Callable) -> Response:
    """Centralized error handling middleware for FastAPI.
    
    Catches unhandled exceptions and returns standardized error responses.
    Logs errors for debugging and monitoring. Handles different exception types
    with appropriate HTTP status codes.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/endpoint in the chain
        
    Returns:
        Response with error details if exception occurred, otherwise normal response
    """
    try:
        response = await call_next(request)
        return response
    except HTTPException as exc:
        # Enhance HTTPException with taxonomy if not already present
        if not hasattr(exc, "error_code") or not exc.error_code:
            error_code, remediation = classify_error(exc.detail or str(exc), {"method": request.method, "path": request.url.path})
            # Create enhanced response with taxonomy
            error_response = create_error_response(
                error_code=error_code,
                message=exc.detail or "An error occurred",
                remediation=remediation,
            )
            return JSONResponse(
                status_code=exc.status_code,
                content=error_response,
            )
        # Re-raise HTTPException as-is if already has taxonomy
        raise exc
    except ValueError as exc:
        # Handle validation errors
        error_code, remediation = classify_error(exc, {"method": request.method, "path": request.url.path})
        logger.warning(
            f"Validation error in {request.method} {request.url.path}: {exc}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": get_remote_address(request),
                "error_code": error_code.value,
            },
        )
        error_response = create_error_response(
            error_code=error_code,
            message="Invalid request parameters",
            detail=str(exc) if settings.app_env == "dev" else None,
            remediation=remediation,
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response,
        )
    except KeyError as exc:
        # Handle missing key errors
        error_code, remediation = classify_error(exc, {"method": request.method, "path": request.url.path})
        logger.warning(
            f"Missing key error in {request.method} {request.url.path}: {exc}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": get_remote_address(request),
                "error_code": error_code.value,
            },
        )
        error_response = create_error_response(
            error_code=error_code,
            message=f"Required parameter missing: {str(exc)}",
            detail=str(exc) if settings.app_env == "dev" else None,
            remediation=remediation,
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response,
        )
    except PermissionError as exc:
        # Handle permission errors
        logger.warning(
            f"Permission error in {request.method} {request.url.path}: {exc}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": get_remote_address(request),
            },
        )
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": "permission_denied",
                "message": "You do not have permission to perform this action",
                "detail": str(exc) if settings.app_env == "dev" else None,
            },
        )
    except FileNotFoundError as exc:
        # Handle file not found errors
        logger.warning(
            f"File not found in {request.method} {request.url.path}: {exc}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": get_remote_address(request),
            },
        )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "file_not_found",
                "message": "The requested resource was not found",
                "detail": str(exc) if settings.app_env == "dev" else None,
            },
        )
    except TimeoutError as exc:
        # Handle timeout errors
        logger.error(
            f"Timeout error in {request.method} {request.url.path}: {exc}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": get_remote_address(request),
            },
        )
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={
                "error": "timeout",
                "message": "The request took too long to process",
                "detail": str(exc) if settings.app_env == "dev" else None,
            },
        )
    except ConnectionError as exc:
        # Handle connection errors
        error_code, remediation = classify_error(exc, {"method": request.method, "path": request.url.path})
        logger.error(
            f"Connection error in {request.method} {request.url.path}: {exc}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": get_remote_address(request),
                "error_code": error_code.value,
            },
        )
        error_response = create_error_response(
            error_code=error_code,
            message="An external service is currently unavailable",
            detail=str(exc) if settings.app_env == "dev" else None,
            remediation=remediation,
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_response,
        )
    except Exception as exc:
        # Log all other exceptions
        error_code, remediation = classify_error(exc, {"method": request.method, "path": request.url.path})
        logger.error(
            f"Unhandled exception in {request.method} {request.url.path}: {exc}",
            exc_info=True,
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": get_remote_address(request),
                "exception_type": type(exc).__name__,
                "error_code": error_code.value,
            },
        )
        
        # Return standardized error response with taxonomy
        error_response = create_error_response(
            error_code=error_code,
            message="An unexpected error occurred. Please try again later.",
            detail=str(exc) if settings.app_env == "dev" else None,
            remediation=remediation,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response,
        )

