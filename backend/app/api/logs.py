from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

from app.core.paths import data_dir, logs_dir, repo_root
from app.services.comfyui_manager import comfyui_manager
from app.services.installer_service import installer

router = APIRouter()


@router.get("/logs")
def get_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    source: str | None = Query(default=None, description="Filter by source: installer, comfyui, system, all"),
    level: str | None = Query(default=None, description="Filter by level: info, warning, error"),
) -> dict[str, Any]:
    """
    Get unified logs from all sources.
    
    Aggregates logs from:
    - Installer service
    - ComfyUI manager
    - System logs (from .ainfluencer/logs/ and runs/)
    """
    all_logs: list[dict[str, Any]] = []
    
    # Get installer logs
    if source is None or source in ("installer", "all"):
        installer_logs = installer.logs(limit=limit)
        for log in installer_logs:
            all_logs.append({
                "timestamp": log.get("ts", 0),
                "level": log.get("level", "info"),
                "source": "installer",
                "message": log.get("message", ""),
                "raw": log,
            })
    
    # Get ComfyUI manager logs
    if source is None or source in ("comfyui", "all"):
        comfyui_logs = comfyui_manager.logs(limit=limit)
        for log_line in comfyui_logs:
            # Parse log line: "[YYYY-MM-DD HH:MM:SS] [LEVEL] message"
            match = re.match(r"^\[([^\]]+)\] \[([^\]]+)\] (.+)$", log_line)
            if match:
                timestamp_str, level, message = match.groups()
                # Convert timestamp string to unix timestamp (approximate)
                try:
                    dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    timestamp = dt.timestamp()
                except Exception:
                    timestamp = 0
                all_logs.append({
                    "timestamp": timestamp,
                    "level": level.lower(),
                    "source": "comfyui",
                    "message": message,
                    "raw": log_line,
                })
            else:
                # Fallback for unparsed logs
                all_logs.append({
                    "timestamp": 0,
                    "level": "info",
                    "source": "comfyui",
                    "message": log_line,
                    "raw": log_line,
                })
    
    # Get system logs from files (if available)
    if source is None or source in ("system", "all"):
        try:
            # Check for run logs (events.jsonl)
            runs_dir = repo_root() / "runs"
            if runs_dir.exists():
                # Find latest run
                latest_file = runs_dir / "latest.txt"
                if latest_file.exists():
                    latest_run = latest_file.read_text().strip()
                    events_file = runs_dir / latest_run / "events.jsonl"
                    if events_file.exists():
                        with events_file.open("r", encoding="utf-8") as f:
                            for line in f:
                                line = line.strip()
                                if not line:
                                    continue
                                try:
                                    event = json.loads(line)
                                    all_logs.append({
                                        "timestamp": event.get("ts", 0),
                                        "level": event.get("level", "info"),
                                        "source": event.get("service", "system"),
                                        "message": event.get("message", ""),
                                        "raw": event,
                                    })
                                except Exception:
                                    pass
        except Exception:
            pass  # Non-fatal if system logs can't be read
    
    # Apply level filter
    if level:
        all_logs = [log for log in all_logs if log["level"].lower() == level.lower()]
    
    # Sort by timestamp (newest first)
    all_logs.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Apply limit
    all_logs = all_logs[:limit]
    
    # Get unique sources for filtering
    sources = sorted(set(log["source"] for log in all_logs))
    levels = sorted(set(log["level"] for log in all_logs))
    
    return {
        "logs": all_logs,
        "count": len(all_logs),
        "sources": sources,
        "levels": levels,
    }

