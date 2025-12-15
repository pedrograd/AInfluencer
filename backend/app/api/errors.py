"""Error logging and aggregation API endpoints."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from app.core.paths import data_dir

router = APIRouter()

# Error storage file
ERRORS_FILE = data_dir() / "errors.jsonl"


def _ensure_errors_file() -> None:
    """Ensure errors file and parent directory exist."""
    ERRORS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not ERRORS_FILE.exists():
        ERRORS_FILE.touch()


def _load_errors(max_count: int = 100) -> list[dict[str, Any]]:
    """Load recent errors from JSONL file, most recent first."""
    _ensure_errors_file()
    
    errors = []
    if not ERRORS_FILE.exists():
        return errors
    
    try:
        with ERRORS_FILE.open("r", encoding="utf-8") as f:
            lines = f.readlines()
            # Read last max_count lines (most recent)
            for line in lines[-max_count:]:
                line = line.strip()
                if line:
                    errors.append(json.loads(line))
    except (json.JSONDecodeError, IOError):
        # If file is corrupted, return empty list
        pass
    
    # Sort by timestamp descending (most recent first)
    errors.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return errors


def _save_error(error: dict[str, Any]) -> None:
    """Append error to JSONL file."""
    _ensure_errors_file()
    
    error_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": error.get("level", "error"),
        "source": error.get("source", "unknown"),
        "message": error.get("message", ""),
        "details": error.get("details", {}),
    }
    
    try:
        with ERRORS_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(error_data) + "\n")
    except IOError:
        # Silently fail if we can't write errors
        pass


@router.post("/errors")
def log_error(error: dict[str, Any]) -> dict[str, str]:
    """
    Log an error for aggregation.
    
    Expected error format:
    {
        "level": "error" | "warning" | "info",
        "source": "backend" | "frontend" | "comfyui" | "installer" | etc.,
        "message": "Error message",
        "details": { ... }  # Optional additional context
    }
    """
    _save_error(error)
    return {"status": "logged"}


@router.get("/errors")
def get_errors(limit: int = 50, source: str | None = None) -> dict[str, Any]:
    """
    Get recent errors with aggregation.
    
    Query params:
    - limit: Maximum number of errors to return (default: 50, max: 100)
    - source: Filter by source (optional)
    """
    limit = min(max(1, limit), 100)  # Clamp between 1 and 100
    
    errors = _load_errors(max_count=limit * 2)  # Load more to filter
    
    # Filter by source if provided
    if source:
        errors = [e for e in errors if e.get("source") == source]
    
    # Limit results
    errors = errors[:limit]
    
    # Aggregate by level and source
    aggregation = {
        "by_level": {},
        "by_source": {},
        "total": len(errors),
    }
    
    for error in errors:
        level = error.get("level", "error")
        error_source = error.get("source", "unknown")
        
        aggregation["by_level"][level] = aggregation["by_level"].get(level, 0) + 1
        aggregation["by_source"][error_source] = aggregation["by_source"].get(error_source, 0) + 1
    
    return {
        "errors": errors,
        "aggregation": aggregation,
        "count": len(errors),
    }


@router.get("/errors/aggregation")
def get_error_aggregation() -> dict[str, Any]:
    """
    Get error aggregation statistics only (no error list).
    Useful for dashboard summary.
    """
    errors = _load_errors(max_count=1000)  # Load more for better stats
    
    aggregation = {
        "by_level": {},
        "by_source": {},
        "total": len(errors),
        "recent_count": len([e for e in errors if _is_recent(e, hours=24)]),
    }
    
    for error in errors:
        level = error.get("level", "error")
        error_source = error.get("source", "unknown")
        
        aggregation["by_level"][level] = aggregation["by_level"].get(level, 0) + 1
        aggregation["by_source"][error_source] = aggregation["by_source"].get(error_source, 0) + 1
    
    return aggregation


def _is_recent(error: dict[str, Any], hours: int = 24) -> bool:
    """Check if error is within the last N hours."""
    try:
        timestamp_str = error.get("timestamp", "")
        if not timestamp_str:
            return False
        
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        # Ensure timestamp is timezone-aware (assume UTC if naive)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        delta = now - timestamp
        
        return delta.total_seconds() < (hours * 3600)
    except (ValueError, TypeError):
        return False


@router.delete("/errors")
def clear_errors() -> dict[str, str]:
    """Clear all logged errors."""
    if ERRORS_FILE.exists():
        ERRORS_FILE.unlink()
    return {"status": "cleared"}

