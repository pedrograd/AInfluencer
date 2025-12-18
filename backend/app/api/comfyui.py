"""ComfyUI API endpoints for service management and integration.

This module provides API endpoints for interacting with ComfyUI, including
service status monitoring, checkpoint/sampler/scheduler listing, and ComfyUI
manager operations (install, start, stop, restart, logs, model sync).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.runtime_settings import get_comfyui_base_url
from app.services.comfyui_client import ComfyUiClient, ComfyUiError
from app.services.comfyui_manager import comfyui_manager

router = APIRouter()


@router.get("/status")
def comfyui_status() -> dict:
    """
    Get ComfyUI service status and system stats.
    
    Checks if ComfyUI is installed, running, and reachable. Returns comprehensive
    status information including installation state, process state, reachability,
    and system statistics.
    
    Returns:
        dict: Status response with:
            - ok: Boolean indicating if ComfyUI is reachable
            - base_url: ComfyUI base URL (from env/file/default)
            - base_url_source: Source of base URL ("env", "file", or "default")
            - installed: Boolean indicating if ComfyUI is installed
            - running: Boolean indicating if ComfyUI process is running
            - reachable: Boolean indicating if ComfyUI HTTP endpoint is reachable
            - stats: System statistics if reachable, None otherwise
            - error: Error message if not reachable
            - message: Human-readable status message
            - action_required: Suggested action if ComfyUI is not ready (e.g., "install", "start", None)
    """
    base = get_comfyui_base_url()
    manager_status = comfyui_manager.status()
    is_installed = comfyui_manager.is_installed()
    
    # Determine if process is running
    is_running = manager_status.state == "running"
    
    # Try to reach ComfyUI if it's supposed to be running
    is_reachable = False
    stats = None
    error = None
    message = None
    action_required = None
    
    if not is_installed:
        message = "ComfyUI is not installed"
        action_required = "install"
        return {
            "ok": False,
            "base_url": base.value,
            "base_url_source": base.source,
            "installed": False,
            "running": False,
            "reachable": False,
            "stats": None,
            "error": "ComfyUI is not installed. Use /api/comfyui/manager/install to install it.",
            "message": message,
            "action_required": action_required,
        }
    
    if not is_running:
        message = "ComfyUI is installed but not running"
        action_required = "start"
        return {
            "ok": False,
            "base_url": base.value,
            "base_url_source": base.source,
            "installed": True,
            "running": False,
            "reachable": False,
            "stats": None,
            "error": "ComfyUI is not running. Use /api/comfyui/manager/start to start it.",
            "message": message,
            "action_required": action_required,
        }
    
    # ComfyUI is installed and process is running, check if HTTP endpoint is reachable
    try:
        client = ComfyUiClient()
        stats = client.get_system_stats()
        is_reachable = True
        message = "ComfyUI is running and reachable"
        action_required = None
        return {
            "ok": True,
            "base_url": base.value,
            "base_url_source": base.source,
            "installed": True,
            "running": True,
            "reachable": True,
            "stats": stats,
            "error": None,
            "message": message,
            "action_required": action_required,
        }
    except ComfyUiError as exc:
        # Process is running but HTTP endpoint is not reachable (might be starting)
        is_reachable = False
        error = str(exc)
        message = f"ComfyUI process is running but not responding: {error}"
        action_required = "wait"  # Might just need to wait for startup
        return {
            "ok": False,
            "base_url": base.value,
            "base_url_source": base.source,
            "installed": True,
            "running": True,
            "reachable": False,
            "stats": None,
            "error": error,
            "message": message,
            "action_required": action_required,
        }


@router.get("/checkpoints")
def comfyui_checkpoints() -> dict:
    """
    List available checkpoint models in ComfyUI.
    
    Returns the list of checkpoint models available in ComfyUI's
    checkpoints directory.
    
    Returns:
        dict: List of checkpoint models with base URL and source
    """
    client = ComfyUiClient()
    base = get_comfyui_base_url()
    try:
        checkpoints = client.list_checkpoints()
        return {"ok": True, "base_url": base.value, "base_url_source": base.source, "checkpoints": checkpoints}
    except ComfyUiError as exc:
        return {"ok": False, "base_url": base.value, "base_url_source": base.source, "error": str(exc), "checkpoints": []}


@router.get("/samplers")
def comfyui_samplers() -> dict:
    """
    List available samplers in ComfyUI.
    
    Returns the list of sampler algorithms available in ComfyUI.
    
    Returns:
        dict: List of sampler names with base URL and source
    """
    client = ComfyUiClient()
    base = get_comfyui_base_url()
    try:
        samplers = client.list_samplers()
        return {"ok": True, "base_url": base.value, "base_url_source": base.source, "samplers": samplers}
    except ComfyUiError as exc:
        return {"ok": False, "base_url": base.value, "base_url_source": base.source, "error": str(exc), "samplers": []}


@router.get("/schedulers")
def comfyui_schedulers() -> dict:
    """
    List available schedulers in ComfyUI.
    
    Returns the list of scheduler algorithms available in ComfyUI.
    
    Returns:
        dict: List of scheduler names with base URL and source
    """
    client = ComfyUiClient()
    base = get_comfyui_base_url()
    try:
        schedulers = client.list_schedulers()
        return {"ok": True, "base_url": base.value, "base_url_source": base.source, "schedulers": schedulers}
    except ComfyUiError as exc:
        return {"ok": False, "base_url": base.value, "base_url_source": base.source, "error": str(exc), "schedulers": []}


# ComfyUI Manager endpoints
@router.get("/manager/status")
def manager_status() -> dict:
    """Get ComfyUI manager status (installation, process state, etc.)."""
    status = comfyui_manager.status()
    return {
        "state": status.state,
        "installed_path": status.installed_path,
        "process_id": status.process_id,
        "port": status.port,
        "base_url": status.base_url,
        "message": status.message,
        "error": status.error,
        "last_check": status.last_check,
        "is_installed": comfyui_manager.is_installed(),
    }


@router.post("/manager/install")
def manager_install() -> dict:
    """Install ComfyUI by cloning from GitHub."""
    try:
        comfyui_manager.install()
        return {"ok": True, "message": "ComfyUI installation started"}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/manager/start")
def manager_start() -> dict:
    """Start ComfyUI process."""
    try:
        comfyui_manager.start()
        return {"ok": True, "message": "ComfyUI started"}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/manager/stop")
def manager_stop() -> dict:
    """Stop ComfyUI process."""
    try:
        comfyui_manager.stop()
        return {"ok": True, "message": "ComfyUI stopped"}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/manager/restart")
def manager_restart() -> dict:
    """Restart ComfyUI process."""
    try:
        comfyui_manager.restart()
        return {"ok": True, "message": "ComfyUI restarted"}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/manager/logs")
def manager_logs(limit: int = 500) -> dict:
    """Get recent logs from ComfyUI process."""
    logs = comfyui_manager.logs(limit=limit)
    return {"logs": logs, "count": len(logs)}


@router.post("/manager/sync-models")
def manager_sync_models() -> dict:
    """Sync models from Model Manager to ComfyUI folders."""
    try:
        result = comfyui_manager.sync_models()
        return {"ok": True, **result}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc))
