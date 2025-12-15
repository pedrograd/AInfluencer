"""Unified system status API endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.paths import repo_root
from app.services.backend_service import BackendServiceManager
from app.services.frontend_service import FrontendServiceManager
from app.services.comfyui_service import ComfyUIServiceManager
from app.services.comfyui_manager import comfyui_manager
from app.services.system_check import system_check
from app.services.comfyui_client import ComfyUiClient, ComfyUiError
from app.core.runtime_settings import get_comfyui_base_url

router = APIRouter()

# Service managers
_backend_service_manager = BackendServiceManager()
_frontend_service_manager = FrontendServiceManager()
_comfyui_service_manager = ComfyUIServiceManager()


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
    
    # Backend service status (using service manager)
    backend_status = _backend_service_manager.status()
    backend_health = {
        "status": "ok" if backend_status.state == "running" else "error",
        "message": backend_status.message or "Backend status unknown",
        "state": backend_status.state,
        "port": backend_status.port,
        "host": backend_status.host,
        "process_id": backend_status.process_id,
        "last_check": backend_status.last_check,
    }
    
    # Frontend service status (using service manager)
    frontend_status_obj = _frontend_service_manager.status()
    frontend_status = {
        "status": "ok" if frontend_status_obj.state == "running" else "error",
        "message": frontend_status_obj.message or "Frontend status unknown",
        "state": frontend_status_obj.state,
        "port": frontend_status_obj.port,
        "host": frontend_status_obj.host,
        "process_id": frontend_status_obj.process_id,
        "last_check": frontend_status_obj.last_check,
    }
    
    # ComfyUI service status (using service manager)
    comfyui_status_obj = _comfyui_service_manager.status()
    comfyui_service = {
        "state": comfyui_status_obj.state,
        "port": comfyui_status_obj.port,
        "host": comfyui_status_obj.host,
        "process_id": comfyui_status_obj.process_id,
        "message": comfyui_status_obj.message,
        "error": comfyui_status_obj.error,
        "last_check": comfyui_status_obj.last_check,
        "installed": comfyui_status_obj.installed,
        "base_url": comfyui_status_obj.base_url,
        "reachable": False,
        "stats": None,
    }
    
    # Try to reach ComfyUI if it's running
    if comfyui_status_obj.state == "running" and comfyui_status_obj.base_url:
        try:
            client = ComfyUiClient(base_url=comfyui_status_obj.base_url)
            stats = client.get_system_stats()
            comfyui_service["reachable"] = True
            comfyui_service["stats"] = stats
        except ComfyUiError as exc:
            comfyui_service["error"] = str(exc)
    
    # ComfyUI Manager status (for backward compatibility)
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
    
    # System check
    system_info = system_check(root)
    
    # Overall status (green/yellow/red)
    overall_status = "ok"
    if system_info.get("issues"):
        critical_issues = [i for i in system_info["issues"] if i.get("severity") == "error"]
        if critical_issues:
            overall_status = "error"
        else:
            overall_status = "warning"
    
    # Check service states
    if backend_status.state == "error" or frontend_status_obj.state == "error" or comfyui_status_obj.state == "error":
        overall_status = "error"
    elif backend_status.state != "running" or frontend_status_obj.state != "running":
        if overall_status != "error":
            overall_status = "warning"
    elif comfyui_status_obj.state == "stopped" or not comfyui_status_obj.installed:
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

