from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.backend_service import BackendServiceManager

router = APIRouter()

# Singleton instance
_backend_service_manager = BackendServiceManager()


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

