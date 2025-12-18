"""Installer API endpoints for system setup and dependency management.

This module provides API endpoints for automated installation and system setup
including system requirements checking, installation process management, fix
actions for detected issues, and diagnostics bundle generation.
"""

from __future__ import annotations

import io
import json
import zipfile

from fastapi import APIRouter
from fastapi.responses import Response

from app.services.installer_service import InstallerService

router = APIRouter()
installer = InstallerService()


@router.get("/check")
def check() -> dict:
    """
    Check system requirements and installation status.
    
    Performs a comprehensive system check including OS, Python version,
    Node.js, Git, disk space, GPU availability, and other prerequisites.
    
    Returns:
        dict: System check results with status for each requirement
    """
    return installer.check()


@router.get("/status")
def status() -> dict:
    """
    Get installer service status.
    
    Returns the current state of the installer service including
    current step, progress, and any status messages.
    
    Returns:
        dict: Installer status with state, step, message, and progress
    """
    s = installer.status()
    return {
        "state": s.state,
        "step": s.step,
        "message": s.message,
        "progress": s.progress,
        "started_at": s.started_at,
        "finished_at": s.finished_at,
    }


@router.get("/logs")
def logs() -> dict:
    """
    Get installer service logs.
    
    Returns recent installer logs including installation steps,
    errors, and progress messages.
    
    Returns:
        dict: List of log entries (up to 1000 most recent)
    """
    return {"items": installer.logs(limit=1000)}


@router.post("/start")
def start() -> dict:
    """
    Start the installation process.
    
    Initiates the automated installation of dependencies, models,
    and configuration. The installation runs asynchronously.
    
    Returns:
        dict: Success status and current installer state
    """
    installer.start()
    return {"ok": True, "state": installer.status().state}


@router.post("/fix/{action}")
def fix(action: str) -> dict:
    """
    Run a specific fix action.
    
    Executes a targeted fix for a specific issue (e.g., install Python,
    install Node.js, create directories).
    
    Args:
        action: Name of the fix action to run
        
    Returns:
        dict: Success status, current state, and action executed
    """
    installer.run_fix(action)
    return {"ok": True, "state": installer.status().state, "action": action}


@router.post("/fix_all")
def fix_all() -> dict:
    """
    Run all available fix actions.
    
    Executes all fix actions to resolve detected issues automatically.
    This is equivalent to running each fix action sequentially.
    
    Returns:
        dict: Success status and current installer state
    """
    installer.run_fix_all()
    return {"ok": True, "state": installer.status().state}


@router.post("/repair")
def repair() -> dict:
    """
    Run comprehensive system repair.
    
    Performs a full system repair including:
    - Re-running doctor/system checks
    - Repairing backend venv (recreating if Python version mismatch)
    - Reinstalling backend dependencies if corrupted
    - Re-checking port availability
    - Re-checking ComfyUI health
    
    This is safe to run multiple times and will not delete user-generated content.
    
    Returns:
        dict: Repair results with status and details of what was repaired
    """
    result = installer.repair()
    return {"ok": True, **result}


@router.get("/diagnostics")
def diagnostics() -> Response:
    """
    Download a small diagnostics bundle for support/debugging.
    Includes: system_check.json, installer_status.json, installer_logs.jsonl
    """
    sysinfo = installer.check()
    status = installer.status()
    logs = installer.logs(limit=5000)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("system_check.json", json.dumps(sysinfo, indent=2, sort_keys=True))
        z.writestr("installer_status.json", json.dumps(status.__dict__, indent=2, sort_keys=True))
        z.writestr("installer_logs.jsonl", "\n".join(json.dumps(x, ensure_ascii=False) for x in logs) + "\n")

    data = buf.getvalue()
    headers = {"Content-Disposition": "attachment; filename=ainfluencer-diagnostics.zip"}
    return Response(content=data, media_type="application/zip", headers=headers)
