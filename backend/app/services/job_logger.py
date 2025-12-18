"""Job logging service with secret redaction.

This module provides structured logging for pipeline jobs with automatic
secret redaction to prevent sensitive information from being stored.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.paths import data_dir
from app.core.logging import get_logger

logger = get_logger(__name__)

# Patterns to redact (case-insensitive)
SECRET_PATTERNS = [
    "api_key",
    "apiKey",
    "apikey",
    "token",
    "password",
    "secret",
    "credential",
    "auth",
    "bearer",
]


def redact_secrets(data: dict[str, Any] | list[Any] | Any) -> dict[str, Any] | list[Any] | Any:
    """Recursively redact secrets from data structure.
    
    Args:
        data: Data structure to redact (dict, list, or primitive)
        
    Returns:
        Data structure with secrets redacted
    """
    if isinstance(data, dict):
        redacted: dict[str, Any] = {}
        for key, value in data.items():
            # Check if key matches secret pattern
            key_lower = str(key).lower()
            if any(pattern.lower() in key_lower for pattern in SECRET_PATTERNS):
                redacted[key] = "***REDACTED***"
            elif isinstance(value, (dict, list)):
                redacted[key] = redact_secrets(value)
            elif isinstance(value, str) and any(pattern.lower() in value.lower() for pattern in ["key", "token", "secret"]):
                # Redact if value looks like a secret (contains key/token/secret and is long)
                if len(value) > 10:
                    redacted[key] = "***REDACTED***"
                else:
                    redacted[key] = value
            else:
                redacted[key] = value
        return redacted
    elif isinstance(data, list):
        return [redact_secrets(item) for item in data]
    else:
        return data


class JobLogger:
    """Logger for pipeline jobs with secret redaction."""

    def __init__(self, jobs_dir: Path | None = None) -> None:
        """Initialize job logger.
        
        Args:
            jobs_dir: Base directory for job logs (defaults to data_dir() / "jobs")
        """
        self.jobs_dir = jobs_dir or (data_dir() / "jobs")
        self.jobs_dir.mkdir(parents=True, exist_ok=True)

    def log_job_event(
        self,
        job_id: str,
        level: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Log job event with secret redaction.
        
        Args:
            job_id: Job identifier
            level: Log level ("info", "warning", "error")
            message: Log message
            metadata: Optional metadata (will be redacted)
        """
        # Create job log directory
        job_log_dir = self.jobs_dir / job_id
        job_log_dir.mkdir(parents=True, exist_ok=True)

        # Redact secrets from metadata
        redacted_metadata = redact_secrets(metadata) if metadata else None

        # Create log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
        }
        if redacted_metadata:
            log_entry["metadata"] = redacted_metadata

        # Append to JSONL file
        log_file = job_log_dir / "logs.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        # Also log to application logger
        log_func = getattr(logger, level, logger.info)
        log_func(f"[Job {job_id}] {message}", extra={"job_id": job_id, "metadata": redacted_metadata})
