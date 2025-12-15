from __future__ import annotations

from fastapi import APIRouter

from app.core.paths import repo_root
from app.services.comfyui_manager import comfyui_manager
from app.services.system_check import system_check
from app.services.comfyui_client import ComfyUiClient, ComfyUiError
from app.core.runtime_settings import get_comfyui_base_url

router = APIRouter()


@router.get("/status")
def unified_status() -> dict:
    """
    Unified status endpoint that aggregates:
    - Backend health
    - System check information
    - ComfyUI manager status
    - ComfyUI service status
    - Frontend status (implied - if this endpoint responds, frontend can reach backend)
    """
    root = repo_root()
    
    # Backend health (this endpoint itself proves backend is running)
    backend_health = {
        "status": "ok",
        "message": "Backend is running",
    }
    
    # System check
    system_info = system_check(root)
    
    # ComfyUI Manager status
    manager_status = comfyui_manager.status()
    manager_dict = {
        "state": manager_status.state,
        "installed_path": manager_status.installed_path,
        "process_id": manager_status.process_id,
        "port": manager_status.port,
        "base_url": manager_status.base_url,
        "message": manager_status.message,
        "error": manager_status.error,
        "last_check": manager_status.last_check,
        "is_installed": comfyui_manager.is_installed(),
    }
    
    # ComfyUI service status (try to reach the actual service)
    comfyui_service = {
        "reachable": False,
        "base_url": None,
        "error": None,
        "stats": None,
    }
    
    base = get_comfyui_base_url()
    comfyui_service["base_url"] = base.value
    
    if manager_status.state == "running":
        try:
            client = ComfyUiClient(base_url=base.value)
            stats = client.get_system_stats()
            comfyui_service["reachable"] = True
            comfyui_service["stats"] = stats
        except ComfyUiError as exc:
            comfyui_service["error"] = str(exc)
    
    # Frontend status (implied - if backend is reachable, frontend can reach it)
    # In a real scenario, we could check if frontend port is listening, but that's not necessary
    # If this endpoint is called from the frontend, the frontend is running
    frontend_status = {
        "status": "ok",
        "message": "Frontend is reachable (implied by successful API call)",
    }
    
    # Overall status (green/yellow/red)
    overall_status = "ok"
    if system_info.get("issues"):
        critical_issues = [i for i in system_info["issues"] if i.get("severity") == "error"]
        if critical_issues:
            overall_status = "error"
        else:
            overall_status = "warning"
    
    if manager_status.state == "error":
        overall_status = "error"
    elif manager_status.state in {"stopping", "stopped", "not_installed"}:
        if overall_status != "error":
            overall_status = "warning"
    
    return {
        "overall_status": overall_status,
        "backend": backend_health,
        "frontend": frontend_status,
        "comfyui_manager": manager_dict,
        "comfyui_service": comfyui_service,
        "system": system_info,
    }

