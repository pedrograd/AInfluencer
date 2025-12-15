from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.backend_service import BackendServiceManager
from app.services.comfyui_service import ComfyUIServiceManager
from app.services.frontend_service import FrontendServiceManager

router = APIRouter()

# Singleton instances
_backend_service_manager = BackendServiceManager()
_frontend_service_manager = FrontendServiceManager()
_comfyui_service_manager = ComfyUIServiceManager()


@router.get("/backend/status")
def backend_status() -> dict:
    """Get backend service status."""
    status = _backend_service_manager.status()
    return {
        "state": status.state,
        "process_id": status.process_id,
        "port": status.port,
        "host": status.host,
        "message": status.message,
        "error": status.error,
        "last_check": status.last_check,
        "pid_file_path": status.pid_file_path,
    }


@router.get("/backend/health")
def backend_health() -> dict:
    """Get backend service health check."""
    return _backend_service_manager.health()


@router.get("/backend/info")
def backend_info() -> dict:
    """Get backend service information and instructions."""
    status = _backend_service_manager.status()
    
    info = {
        "status": status.state,
        "port": status.port,
        "host": status.host,
        "process_id": status.process_id,
        "message": status.message,
    }
    
    # Add instructions based on state
    if status.state == "stopped":
        info["instructions"] = {
            "start": "Use launcher script (launch.sh/launch.ps1) or run: uvicorn app.main:app --host 0.0.0.0 --port 8000",
            "note": "Backend cannot start itself via API. Use external launcher or manual start.",
        }
    elif status.state == "running":
        info["instructions"] = {
            "stop": "Use launcher script or send SIGTERM to process",
            "restart": "Stop and start using launcher script",
            "note": "Backend cannot stop itself via API for safety reasons. Use external launcher or manual stop.",
        }
    else:
        info["instructions"] = {
            "note": "Backend status is uncertain. Check logs and process status.",
        }
    
    return info


@router.get("/frontend/status")
def frontend_status() -> dict:
    """Get frontend service status."""
    status = _frontend_service_manager.status()
    return {
        "state": status.state,
        "process_id": status.process_id,
        "port": status.port,
        "host": status.host,
        "message": status.message,
        "error": status.error,
        "last_check": status.last_check,
        "pid_file_path": status.pid_file_path,
    }


@router.get("/frontend/health")
def frontend_health() -> dict:
    """Get frontend service health check."""
    return _frontend_service_manager.health()


@router.get("/frontend/info")
def frontend_info() -> dict:
    """Get frontend service information and instructions."""
    status = _frontend_service_manager.status()
    
    info = {
        "status": status.state,
        "port": status.port,
        "host": status.host,
        "process_id": status.process_id,
        "message": status.message,
    }
    
    # Add instructions based on state
    if status.state == "stopped":
        info["instructions"] = {
            "start": "Use launcher script (launch.sh/launch.ps1) or run: npm run dev (in frontend/ directory)",
            "note": "Frontend cannot start itself via API. Use external launcher or manual start.",
        }
    elif status.state == "running":
        info["instructions"] = {
            "stop": "Use launcher script or send SIGTERM to process",
            "restart": "Stop and start using launcher script",
            "note": "Frontend cannot stop itself via API for safety reasons. Use external launcher or manual stop.",
        }
    else:
        info["instructions"] = {
            "note": "Frontend status is uncertain. Check logs and process status.",
        }
    
    return info


@router.get("/comfyui/status")
def comfyui_status() -> dict:
    """Get ComfyUI service status."""
    status = _comfyui_service_manager.status()
    return {
        "state": status.state,
        "process_id": status.process_id,
        "port": status.port,
        "host": status.host,
        "message": status.message,
        "error": status.error,
        "last_check": status.last_check,
        "pid_file_path": status.pid_file_path,
        "installed": status.installed,
        "base_url": status.base_url,
    }


@router.get("/comfyui/health")
def comfyui_health() -> dict:
    """Get ComfyUI service health check."""
    return _comfyui_service_manager.health()


@router.get("/comfyui/info")
def comfyui_info() -> dict:
    """Get ComfyUI service information and instructions."""
    status = _comfyui_service_manager.status()
    
    info = {
        "status": status.state,
        "port": status.port,
        "host": status.host,
        "process_id": status.process_id,
        "message": status.message,
        "installed": status.installed,
        "base_url": status.base_url,
    }
    
    # Add instructions based on state
    if status.state == "stopped":
        if not status.installed:
            info["instructions"] = {
                "install": "Use /api/comfyui/manager/install endpoint or install ComfyUI manually",
                "start": "After installation, use /api/comfyui/manager/start endpoint",
                "note": "ComfyUI can be installed and started via API endpoints.",
            }
        else:
            info["instructions"] = {
                "start": "Use /api/comfyui/manager/start endpoint or launcher script",
                "note": "ComfyUI can be started via API endpoint.",
            }
    elif status.state == "running":
        info["instructions"] = {
            "stop": "Use /api/comfyui/manager/stop endpoint",
            "restart": "Use /api/comfyui/manager/restart endpoint",
            "note": "ComfyUI can be stopped/restarted via API endpoints.",
        }
    else:
        info["instructions"] = {
            "note": "ComfyUI status is uncertain. Check logs and process status.",
        }
    
    return info

