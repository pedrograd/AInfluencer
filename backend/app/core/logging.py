from __future__ import annotations

import logging
import sys

from pythonjsonlogger import jsonlogger

from app.core.config import settings


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

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(correlation_id)s"
    )
    handler.setFormatter(formatter)
    handler.addFilter(_CorrelationIdFilter())

    # Replace any existing handlers (avoid duplicate logs in reload/dev)
    root.handlers = [handler]

    # Make uvicorn loggers consistent
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(logger_name).handlers = [handler]
        logging.getLogger(logger_name).propagate = False


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    return logger
