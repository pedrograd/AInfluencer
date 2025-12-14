from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import router as api_router
from app.core.logging import configure_logging
from app.core.paths import content_dir


def create_app() -> FastAPI:
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
    return app


app = create_app()
