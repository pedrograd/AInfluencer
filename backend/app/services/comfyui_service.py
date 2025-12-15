from __future__ import annotations

import os
import platform
import socket
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from app.core.logging import get_logger
from app.core.paths import data_dir
from app.services.comfyui_manager import comfyui_manager

logger = get_logger(__name__)

ComfyUIServiceState = Literal["unknown", "running", "stopped", "error"]


@dataclass
class ComfyUIServiceStatus:
    state: ComfyUIServiceState = "unknown"
    process_id: int | None = None
    port: int = 8188
    host: str = "localhost"
    message: str | None = None
    error: str | None = None
    last_check: float | None = None
    pid_file_path: str | None = None
    installed: bool = False
    base_url: str | None = None


class ComfyUIServiceManager:
    """Manages ComfyUI service status and health checks."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._status = ComfyUIServiceStatus()
        self._pid_file = data_dir() / "comfyui.pid"
        self._port = 8188

        # Initial status check
        self._update_status()

    def status(self) -> ComfyUIServiceStatus:
        """Get current ComfyUI service status."""
        with self._lock:
            self._update_status()
            return ComfyUIServiceStatus(**asdict(self._status))

    def _update_status(self) -> None:
        """Update ComfyUI service status by checking ComfyUI manager, PID file, and port."""
        current_time = time.time()

        # Check ComfyUI manager status
        manager_status = comfyui_manager.status()
        self._status.installed = manager_status.state != "not_installed"
        self._status.base_url = manager_status.base_url

        # Check if PID file exists (created by launcher or ComfyUI manager)
        pid = None
        if self._pid_file.exists():
            try:
                pid_content = self._pid_file.read_text().strip()
                if pid_content:
                    pid = int(pid_content)
                    self._status.pid_file_path = str(self._pid_file)
            except (ValueError, OSError) as exc:
                logger.warning(f"Failed to read PID file: {exc}")

        # Also check manager's process ID
        if manager_status.process_id:
            pid = manager_status.process_id

        # Check if port is listening (indicates ComfyUI is running)
        port_listening = self._check_port_listening(self._port)

        # Determine state based on manager status and port
        if manager_status.state == "running" and port_listening:
            self._status.state = "running"
            self._status.message = f"ComfyUI is running on port {self._port}"
            self._status.error = None
            if pid:
                self._status.process_id = pid
        elif manager_status.state == "starting":
            self._status.state = "running"  # Treat starting as running
            self._status.message = "ComfyUI is starting..."
            self._status.error = None
            if pid:
                self._status.process_id = pid
        elif manager_status.state == "stopped":
            self._status.state = "stopped"
            self._status.message = "ComfyUI service not running"
            self._status.error = None
            self._status.process_id = None
        elif manager_status.state == "not_installed":
            self._status.state = "stopped"
            self._status.message = "ComfyUI is not installed"
            self._status.error = None
            self._status.process_id = None
        elif manager_status.state == "error":
            self._status.state = "error"
            self._status.message = manager_status.message or "ComfyUI service error"
            self._status.error = manager_status.error
            if pid:
                self._status.process_id = pid
        elif pid:
            # PID file exists but port not listening - process might have died
            if self._check_process_running(pid):
                self._status.state = "error"
                self._status.message = f"Process {pid} exists but port {self._port} not listening"
                self._status.error = "Port not accessible"
            else:
                self._status.state = "stopped"
                self._status.message = f"Process {pid} no longer running"
                self._status.error = None
        else:
            self._status.state = "stopped"
            self._status.message = "ComfyUI service not running"
            self._status.error = None

        self._status.last_check = current_time
        self._status.port = self._port
        self._status.host = "localhost"

    def _check_port_listening(self, port: int) -> bool:
        """Check if a port is listening."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.5)
                result = sock.connect_ex(("localhost", port))
                return result == 0
        except Exception:
            return False

    def _check_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running."""
        try:
            if platform.system() == "Windows":
                # On Windows, try to signal process 0 (no-op) to check if it exists
                os.kill(pid, 0)
            else:
                # On Unix, signal 0 checks if process exists
                os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

    def health(self) -> dict:
        """Get ComfyUI health information."""
        status = self.status()
        return {
            "status": "healthy" if status.state == "running" else "unhealthy",
            "state": status.state,
            "port": status.port,
            "process_id": status.process_id,
            "message": status.message,
            "last_check": status.last_check,
            "installed": status.installed,
            "base_url": status.base_url,
        }

