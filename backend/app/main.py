"""FastAPI application factory and main entry point.

This module provides the application factory function that creates and configures
the FastAPI application instance with all middleware, routers, and static file
mounting.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from pydantic import ValidationError

from app.core.error_taxonomy import ErrorCode, create_error_response

from app.api.router import router as api_router
from app.core.logging import configure_logging
from app.core.middleware import error_handler_middleware, limiter
from app.core.paths import content_dir
from app.core.redis_client import close_redis, get_redis
from app.services.unified_logging import get_unified_logger


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance.
    
    Sets up logging, CORS middleware for local development, API routing,
    and static file serving for content. The application is configured for
    MVP development with localhost:3000 frontend access.
    
    Returns:
        FastAPI: Configured FastAPI application instance ready to run.
    """
    configure_logging()

    app = FastAPI(title="AInfluencer Backend", version="0.0.1")

    # Initialize rate limiter
    app.state.limiter = limiter

    # MVP: allow local dev dashboard
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add error handlers for rate limiting
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        """Handle rate limit exceeded errors."""
        response = JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "rate_limit_exceeded",
                "message": f"Rate limit exceeded: {exc.detail}",
            },
        )
        response = request.app.state.limiter._inject_headers(
            response, request.state.view_rate_limit
        )
        return response
    
    # Add error handler for Pydantic validation errors (422)
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle Pydantic validation errors with user-friendly messages."""
        errors = exc.errors()
        error_messages = []
        missing_fields = []
        
        for error in errors:
            field = ".".join(str(loc) for loc in error["loc"])
            error_type = error["type"]
            error_msg = error.get("msg", "Validation error")
            
            if error_type == "missing":
                missing_fields.append(field)
                error_messages.append(f"Missing required field: {field}")
            elif error_type == "value_error":
                error_messages.append(f"Invalid value for {field}: {error_msg}")
            else:
                error_messages.append(f"{field}: {error_msg}")
        
        # If request body is missing entirely, provide helpful message
        if not missing_fields and any("body" in str(error.get("loc", [])) for error in errors):
            error_response = create_error_response(
                error_code=ErrorCode.CONTRACT_MISMATCH,
                message="Request body is missing or invalid. Expected JSON body with required fields.",
                detail="Please ensure you're sending a JSON body with Content-Type: application/json header.",
            )
            error_response["errors"] = error_messages[:5]  # Limit to first 5 errors
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=error_response,
            )
        
        # Use CONTRACT_MISMATCH for all validation errors (per pipeline spec)
        # This provides consistent error taxonomy for schema drift issues
        error_code = ErrorCode.CONTRACT_MISMATCH
        
        error_response = create_error_response(
            error_code=error_code,
            message="Request validation failed. The request format doesn't match the API contract.",
            detail="; ".join(error_messages[:5]),  # Limit to first 5 errors
        )
        if missing_fields:
            error_response["missing_fields"] = missing_fields[:5]
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response,
        )

    # Add error handling middleware (should be last to catch all errors)
    app.middleware("http")(error_handler_middleware)

    app.include_router(api_router, prefix="/api")
    content_dir().mkdir(parents=True, exist_ok=True)
    app.mount("/content", StaticFiles(directory=str(content_dir())), name="content")
    
    @app.on_event("startup")
    async def startup_event() -> None:
        """Initialize Redis connection on application startup."""
        logger = get_unified_logger()
        logger.info("backend", "Application startup: initializing services")
        await get_redis()
        logger.info("backend", "Application startup: Redis connection established")
    
    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        """Close Redis connection on application shutdown."""
        logger = get_unified_logger()
        logger.info("backend", "Application shutdown: closing connections")
        await close_redis()
        logger.info("backend", "Application shutdown: Redis connection closed")
    
    @app.get("/")
    def root():
        """Root endpoint - redirects to API documentation."""
        return RedirectResponse(url="/docs")
    
    @app.get("/api")
    def api_root():
        """API root endpoint - provides basic API information."""
        return {
            "name": "AInfluencer Backend API",
            "version": "0.0.1",
            "docs": "/docs",
            "health": "/api/health",
            "status": "/api/status"
        }
    
    return app


app = create_app()
