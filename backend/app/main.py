"""FastAPI application factory and main entry point.

This module provides the application factory function that creates and configures
the FastAPI application instance with all middleware, routers, and static file
mounting.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import router as api_router
from app.core.logging import configure_logging
from app.core.paths import content_dir


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

    # MVP: allow local dev dashboard
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")
    content_dir().mkdir(parents=True, exist_ok=True)
    app.mount("/content", StaticFiles(directory=str(content_dir())), name="content")
    
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
