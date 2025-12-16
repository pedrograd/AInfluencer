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
    from slowapi.errors import RateLimitExceeded

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
