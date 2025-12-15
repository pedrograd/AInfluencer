"""Backend service management and health monitoring."""

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

logger = get_logger(__name__)

BackendServiceState = Literal["unknown", "running", "stopped", "error"]


@dataclass
class BackendServiceStatus:
    """Backend service status information.
    
    Attributes:
        state: Current service state (unknown, running, stopped, error).
        process_id: Process ID of the backend service if running, None otherwise.
        port: Port number the backend service is listening on (default: 8000).
        host: Host address the backend service is bound to (default: 0.0.0.0).
        message: Human-readable status message describing the current state.
        error: Error message if state is "error", None otherwise.
        last_check: Timestamp of the last status check (Unix timestamp).
        pid_file_path: Path to the PID file used to track the backend process.
    """
    state: BackendServiceState = "unknown"
    process_id: int | None = None
    port: int = 8000
    host: str = "0.0.0.0"
    message: str | None = None
    error: str | None = None
    last_check: float | None = None
    pid_file_path: str | None = None


class BackendServiceManager:
    """Manages backend service status and health checks."""

    def __init__(self) -> None:
        """Initialize backend service manager with thread lock and status tracking."""
        self._lock = threading.Lock()
        self._status = BackendServiceStatus()
        self._pid_file = data_dir() / "backend.pid"
        self._port = 8000

        # Initial status check
        self._update_status()

    def status(self) -> BackendServiceStatus:
        """Get current backend service status."""
        with self._lock:
            self._update_status()
            return BackendServiceStatus(**asdict(self._status))

    def _update_status(self) -> None:
        """Update backend service status by checking PID file and port."""
        current_time = time.time()

        # Check if PID file exists (created by launcher)
        pid = None
        if self._pid_file.exists():
            try:
                pid_content = self._pid_file.read_text().strip()
                if pid_content:
                    pid = int(pid_content)
                    self._status.pid_file_path = str(self._pid_file)
            except (ValueError, OSError) as exc:
                logger.warning(f"Failed to read PID file: {exc}")

        # Check if port is listening (indicates backend is running)
        port_listening = self._check_port_listening(self._port)

        # Determine state
        if port_listening:
            self._status.state = "running"
            self._status.message = f"Backend is running on port {self._port}"
            self._status.error = None
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
            self._status.message = "Backend service not running"
            self._status.error = None

        self._status.last_check = current_time
        self._status.port = self._port
        self._status.host = "0.0.0.0"

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
        """Get backend health information."""
        status = self.status()
        return {
            "status": "healthy" if status.state == "running" else "unhealthy",
            "state": status.state,
            "port": status.port,
            "process_id": status.process_id,
            "message": status.message,
            "last_check": status.last_check,
        }

