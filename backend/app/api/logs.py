from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

from app.core.paths import logs_dir, repo_root
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
    - Backend application (from .ainfluencer/logs/backend.log)
    - Installer service
    - ComfyUI manager
    - System logs (from runs/)
    """
    all_logs: list[dict[str, Any]] = []
    
    # Get backend application logs from log files
    if source is None or source in ("backend", "system", "all"):
        try:
            backend_log_file = logs_dir() / "backend.log"
            # Also check rotated files (backend.log.1, backend.log.2, etc.)
            log_files = [backend_log_file]
            for i in range(1, 6):  # Check up to 5 rotated files
                rotated_file = logs_dir() / f"backend.log.{i}"
                if rotated_file.exists():
                    log_files.append(rotated_file)
            
            # Read from newest to oldest (reverse order)
            for log_file in reversed(log_files):
                if not log_file.exists():
                    continue
                try:
                    with log_file.open("r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                # Parse JSON log entry
                                log_entry = json.loads(line)
                                # Extract timestamp from asctime or use current time
                                asctime = log_entry.get("asctime", "")
                                timestamp = 0
                                if asctime:
                                    try:
                                        # Parse ISO format or standard format
                                        dt = datetime.strptime(asctime, "%Y-%m-%d %H:%M:%S")
                                        timestamp = dt.timestamp()
                                    except Exception:
                                        try:
                                            dt = datetime.fromisoformat(asctime.replace("Z", "+00:00"))
                                            timestamp = dt.timestamp()
                                        except Exception:
                                            pass
                                
                                # Extract level and message
                                level = log_entry.get("levelname", "info").lower()
                                message = log_entry.get("message", "")
                                name = log_entry.get("name", "backend")
                                
                                all_logs.append({
                                    "timestamp": timestamp,
                                    "level": level,
                                    "source": "backend",
                                    "message": message,
                                    "logger": name,
                                    "raw": log_entry,
                                })
                            except json.JSONDecodeError:
                                # If not JSON, try to parse as plain text
                                pass
                except Exception:
                    pass  # Non-fatal if file can't be read
        except Exception:
            pass  # Non-fatal if backend logs can't be read
    
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
    
    # Get system logs from runs/ directory (if available)
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


@router.get("/logs/stats")
def get_log_stats() -> dict[str, Any]:
    """
    Get statistics about available logs.
    
    Returns:
    - Total log count per source
    - Log count per level
    - Available sources
    - Available levels
    """
    # Get all logs (with a reasonable limit for stats)
    all_logs: list[dict[str, Any]] = []
    
    # Collect from all sources
    try:
        # Backend logs
        backend_log_file = logs_dir() / "backend.log"
        if backend_log_file.exists():
            with backend_log_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        log_entry = json.loads(line)
                        level = log_entry.get("levelname", "info").lower()
                        all_logs.append({
                            "source": "backend",
                            "level": level,
                        })
                    except Exception:
                        pass
    except Exception:
        pass
    
    # Installer logs
    try:
        installer_logs = installer.logs(limit=1000)
        for log in installer_logs:
            all_logs.append({
                "source": "installer",
                "level": log.get("level", "info"),
            })
    except Exception:
        pass
    
    # ComfyUI logs
    try:
        comfyui_logs = comfyui_manager.logs(limit=1000)
        for log_line in comfyui_logs:
            match = re.match(r"^\[([^\]]+)\] \[([^\]]+)\]", log_line)
            if match:
                level = match.group(2).lower()
                all_logs.append({
                    "source": "comfyui",
                    "level": level,
                })
    except Exception:
        pass
    
    # Calculate statistics
    source_counts: dict[str, int] = {}
    level_counts: dict[str, int] = {}
    source_level_counts: dict[str, dict[str, int]] = {}
    
    for log in all_logs:
        source = log.get("source", "unknown")
        level = log.get("level", "info")
        
        # Count by source
        source_counts[source] = source_counts.get(source, 0) + 1
        
        # Count by level
        level_counts[level] = level_counts.get(level, 0) + 1
        
        # Count by source and level
        if source not in source_level_counts:
            source_level_counts[source] = {}
        source_level_counts[source][level] = source_level_counts[source].get(level, 0) + 1
    
    return {
        "total": len(all_logs),
        "by_source": source_counts,
        "by_level": level_counts,
        "by_source_and_level": source_level_counts,
        "sources": sorted(set(log.get("source", "unknown") for log in all_logs)),
        "levels": sorted(set(log.get("level", "info") for log in all_logs)),
    }

