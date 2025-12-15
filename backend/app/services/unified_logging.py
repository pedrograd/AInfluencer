"""Unified logging service for writing to runs/<timestamp>/ directory.

This service provides a unified way for backend services to write structured
events to runs/<timestamp>/events.jsonl and summary lines to summary.txt,
matching the format used by the launcher scripts.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from app.core.paths import repo_root


class UnifiedLoggingService:
    """Service for writing unified logs to runs/<timestamp>/ directory."""

    def __init__(self) -> None:
        """Initialize unified logging service."""
        self._runs_dir: Path | None = None
        self._current_run_dir: Path | None = None
        self._events_file: Path | None = None
        self._summary_file: Path | None = None

    def _ensure_run_dir(self) -> Path | None:
        """Ensure current run directory is available.
        
        Returns:
            Path to current run directory, or None if not available.
        """
        if self._current_run_dir is not None and self._current_run_dir.exists():
            return self._current_run_dir

        # Find runs directory
        root = repo_root()
        runs_dir = root / "runs"
        if not runs_dir.exists():
            return None

        # Find current run (from latest.txt or latest symlink)
        latest_file = runs_dir / "latest.txt"
        latest_symlink = runs_dir / "latest"

        current_run: str | None = None

        # Try latest.txt first
        if latest_file.exists():
            try:
                current_run = latest_file.read_text(encoding="utf-8").strip()
            except Exception:
                pass

        # Fall back to latest symlink
        if not current_run and latest_symlink.exists():
            try:
                if latest_symlink.is_symlink():
                    current_run = latest_symlink.readlink().name
                elif latest_symlink.is_dir():
                    current_run = latest_symlink.name
            except Exception:
                pass

        if not current_run:
            return None

        # Verify run directory exists
        run_dir = runs_dir / current_run
        if not run_dir.exists():
            return None

        # Cache paths
        self._runs_dir = runs_dir
        self._current_run_dir = run_dir
        self._events_file = run_dir / "events.jsonl"
        self._summary_file = run_dir / "summary.txt"

        return self._current_run_dir

    def write_event(
        self,
        level: str,
        service: str,
        message: str,
        fix: str | None = None,
        **extra: Any,
    ) -> None:
        """Write an event to events.jsonl.
        
        Args:
            level: Event level (info, warning, error)
            service: Service name (e.g., "backend", "frontend", "comfyui")
            message: Event message
            fix: Optional fix suggestion
            **extra: Additional event data
        """
        run_dir = self._ensure_run_dir()
        if run_dir is None or self._events_file is None:
            return  # Silently fail if run directory not available

        event: dict[str, Any] = {
            "ts": int(time.time()),
            "level": level,
            "service": service,
            "message": message,
        }

        if fix:
            event["fix"] = fix

        if extra:
            event.update(extra)

        try:
            with self._events_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception:
            pass  # Silently fail if we can't write

    def write_summary(self, line: str) -> None:
        """Write a line to summary.txt.
        
        Args:
            line: Summary line to write
        """
        run_dir = self._ensure_run_dir()
        if run_dir is None or self._summary_file is None:
            return  # Silently fail if run directory not available

        try:
            with self._summary_file.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass  # Silently fail if we can't write

    def info(self, service: str, message: str, **extra: Any) -> None:
        """Write an info event.
        
        Args:
            service: Service name
            message: Event message
            **extra: Additional event data
        """
        self.write_event("info", service, message, **extra)

    def warning(self, service: str, message: str, fix: str | None = None, **extra: Any) -> None:
        """Write a warning event.
        
        Args:
            service: Service name
            message: Event message
            fix: Optional fix suggestion
            **extra: Additional event data
        """
        self.write_event("warning", service, message, fix=fix, **extra)

    def error(self, service: str, message: str, fix: str | None = None, **extra: Any) -> None:
        """Write an error event.
        
        Args:
            service: Service name
            message: Event message
            fix: Optional fix suggestion
            **extra: Additional event data
        """
        self.write_event("error", service, message, fix=fix, **extra)


# Global instance
_unified_logger: UnifiedLoggingService | None = None


def get_unified_logger() -> UnifiedLoggingService:
    """Get the global unified logging service instance.
    
    Returns:
        Unified logging service instance
    """
    global _unified_logger
    if _unified_logger is None:
        _unified_logger = UnifiedLoggingService()
    return _unified_logger

