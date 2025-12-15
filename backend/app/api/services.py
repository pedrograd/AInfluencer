"""Service orchestration API endpoints for backend, frontend, and ComfyUI."""

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
    """Get backend service status.
    
    Returns:
        dict: Backend service status information including:
            - state: Current service state (unknown, running, stopped, error)
            - process_id: Process ID if running, None otherwise
            - port: Port number (default: 8000)
            - host: Host address (default: 0.0.0.0)
            - message: Human-readable status message
            - error: Error message if state is "error", None otherwise
            - last_check: Timestamp of last status check (Unix timestamp)
            - pid_file_path: Path to PID file used to track the process
    
    Example:
        ```json
        {
            "state": "running",
            "process_id": 12345,
            "port": 8000,
            "host": "0.0.0.0",
            "message": "Backend is running on port 8000",
            "error": null,
            "last_check": 1700000000.0,
            "pid_file_path": "/path/to/.ainfluencer/backend.pid"
        }
        ```
    """
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
    """Get backend service health check.
    
    Returns:
        dict: Health check information including:
            - status: "healthy" if running, "unhealthy" otherwise
            - state: Current service state (unknown, running, stopped, error)
            - port: Port number the service is listening on
            - process_id: Process ID if running, None otherwise
            - message: Human-readable status message
            - last_check: Timestamp of last status check (Unix timestamp)
    
    Example:
        ```json
        {
            "status": "healthy",
            "state": "running",
            "port": 8000,
            "process_id": 12345,
            "message": "Backend is running on port 8000",
            "last_check": 1700000000.0
        }
        ```
    """
    return _backend_service_manager.health()


@router.get("/backend/info")
def backend_info() -> dict:
    """Get backend service information and instructions.
    
    Returns:
        dict: Service information including:
            - status: Current service state
            - port: Port number
            - host: Host address
            - process_id: Process ID if running, None otherwise
            - message: Human-readable status message
            - instructions: Dict with start/stop/restart instructions based on state
    
    Note:
        Backend cannot start/stop itself via API for safety reasons.
        Use external launcher scripts (launch.sh/launch.ps1) or manual commands.
    
    Example:
        ```json
        {
            "status": "stopped",
            "port": 8000,
            "host": "0.0.0.0",
            "process_id": null,
            "message": "Backend service not running",
            "instructions": {
                "start": "Use launcher script or run: uvicorn app.main:app --host 0.0.0.0 --port 8000",
                "note": "Backend cannot start itself via API. Use external launcher or manual start."
            }
        }
        ```
    """
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
    """Get frontend service status.
    
    Returns:
        dict: Frontend service status information including:
            - state: Current service state (unknown, running, stopped, error)
            - process_id: Process ID if running, None otherwise
            - port: Port number (default: 3000)
            - host: Host address (default: localhost)
            - message: Human-readable status message
            - error: Error message if state is "error", None otherwise
            - last_check: Timestamp of last status check (Unix timestamp)
            - pid_file_path: Path to PID file used to track the process
    
    Example:
        ```json
        {
            "state": "running",
            "process_id": 12346,
            "port": 3000,
            "host": "localhost",
            "message": "Frontend is running on port 3000",
            "error": null,
            "last_check": 1700000000.0,
            "pid_file_path": "/path/to/.ainfluencer/frontend.pid"
        }
        ```
    """
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
    """Get frontend service health check.
    
    Returns:
        dict: Health check information including:
            - status: "healthy" if running, "unhealthy" otherwise
            - state: Current service state (unknown, running, stopped, error)
            - port: Port number the service is listening on
            - process_id: Process ID if running, None otherwise
            - message: Human-readable status message
            - last_check: Timestamp of last status check (Unix timestamp)
    
    Example:
        ```json
        {
            "status": "healthy",
            "state": "running",
            "port": 3000,
            "process_id": 12346,
            "message": "Frontend is running on port 3000",
            "last_check": 1700000000.0
        }
        ```
    """
    return _frontend_service_manager.health()


@router.get("/frontend/info")
def frontend_info() -> dict:
    """Get frontend service information and instructions.
    
    Returns:
        dict: Service information including:
            - status: Current service state
            - port: Port number
            - host: Host address
            - process_id: Process ID if running, None otherwise
            - message: Human-readable status message
            - instructions: Dict with start/stop/restart instructions based on state
    
    Note:
        Frontend cannot start/stop itself via API for safety reasons.
        Use external launcher scripts (launch.sh/launch.ps1) or manual commands.
    
    Example:
        ```json
        {
            "status": "stopped",
            "port": 3000,
            "host": "localhost",
            "process_id": null,
            "message": "Frontend service not running",
            "instructions": {
                "start": "Use launcher script or run: npm run dev (in frontend/ directory)",
                "note": "Frontend cannot start itself via API. Use external launcher or manual start."
            }
        }
        ```
    """
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
    """Get ComfyUI service status.
    
    Returns:
        dict: ComfyUI service status information including:
            - state: Current service state (unknown, running, stopped, error)
            - process_id: Process ID if running, None otherwise
            - port: Port number (default: 8188)
            - host: Host address (default: localhost)
            - message: Human-readable status message
            - error: Error message if state is "error", None otherwise
            - last_check: Timestamp of last status check (Unix timestamp)
            - pid_file_path: Path to PID file used to track the process
            - installed: Whether ComfyUI is installed (True/False)
            - base_url: Base URL of ComfyUI API if running, None otherwise
    
    Example:
        ```json
        {
            "state": "running",
            "process_id": 12347,
            "port": 8188,
            "host": "localhost",
            "message": "ComfyUI is running on port 8188",
            "error": null,
            "last_check": 1700000000.0,
            "pid_file_path": "/path/to/.ainfluencer/comfyui.pid",
            "installed": true,
            "base_url": "http://localhost:8188"
        }
        ```
    """
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
    """Get ComfyUI service health check.
    
    Returns:
        dict: Health check information including:
            - status: "healthy" if running, "unhealthy" otherwise
            - state: Current service state (unknown, running, stopped, error)
            - port: Port number the service is listening on
            - process_id: Process ID if running, None otherwise
            - message: Human-readable status message
            - last_check: Timestamp of last status check (Unix timestamp)
            - installed: Whether ComfyUI is installed (True/False)
            - base_url: Base URL of ComfyUI API if running, None otherwise
    
    Example:
        ```json
        {
            "status": "healthy",
            "state": "running",
            "port": 8188,
            "process_id": 12347,
            "message": "ComfyUI is running on port 8188",
            "last_check": 1700000000.0,
            "installed": true,
            "base_url": "http://localhost:8188"
        }
        ```
    """
    return _comfyui_service_manager.health()


@router.get("/comfyui/info")
def comfyui_info() -> dict:
    """Get ComfyUI service information and instructions.
    
    Returns:
        dict: Service information including:
            - status: Current service state
            - port: Port number
            - host: Host address
            - process_id: Process ID if running, None otherwise
            - message: Human-readable status message
            - installed: Whether ComfyUI is installed (True/False)
            - base_url: Base URL of ComfyUI API if running, None otherwise
            - instructions: Dict with install/start/stop/restart instructions based on state
    
    Note:
        Unlike backend/frontend, ComfyUI can be installed and started/stopped via API endpoints.
        Use /api/comfyui/manager/* endpoints for management operations.
    
    Example:
        ```json
        {
            "status": "stopped",
            "port": 8188,
            "host": "localhost",
            "process_id": null,
            "message": "ComfyUI service not running",
            "installed": true,
            "base_url": null,
            "instructions": {
                "start": "Use /api/comfyui/manager/start endpoint or launcher script",
                "note": "ComfyUI can be started via API endpoint."
            }
        }
        ```
    """
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

