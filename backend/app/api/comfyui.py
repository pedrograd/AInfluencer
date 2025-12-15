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
    
    Checks if ComfyUI is reachable and returns system statistics
    including GPU usage, memory, and queue information.
    
    Returns:
        dict: Status response with base URL, stats, or error message
    """
    client = ComfyUiClient()
    base = get_comfyui_base_url()
    try:
        stats = client.get_system_stats()
        return {"ok": True, "base_url": base.value, "base_url_source": base.source, "stats": stats}
    except ComfyUiError as exc:
        return {"ok": False, "base_url": base.value, "base_url_source": base.source, "error": str(exc)}


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
