from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from pythonjsonlogger import jsonlogger

from app.core.config import settings
from app.core.paths import logs_dir


class _CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        # If we later add middleware that sets record.correlation_id, keep it.
        if not hasattr(record, "correlation_id"):
            record.correlation_id = None
        return True


def configure_logging() -> None:
    """Configure structured JSON logging for the backend."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Ensure logs directory exists
    log_dir = logs_dir()
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create formatter
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(correlation_id)s"
    )

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(_CorrelationIdFilter())

    # File handler with rotation (10MB per file, keep 5 backups)
    log_file = log_dir / "backend.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(_CorrelationIdFilter())

    # Replace any existing handlers (avoid duplicate logs in reload/dev)
    root.handlers = [console_handler, file_handler]

    # Make uvicorn loggers consistent
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        logger.handlers = [console_handler, file_handler]
        logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    return logger
