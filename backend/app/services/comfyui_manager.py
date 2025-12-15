from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from app.core.logging import get_logger
from app.core.paths import comfyui_dir, data_dir, logs_dir, repo_root
from app.services.comfyui_client import ComfyUiClient, ComfyUiError

logger = get_logger(__name__)

ComfyUiState = Literal["not_installed", "installed", "starting", "running", "stopping", "stopped", "error"]


@dataclass
class ComfyUiManagerStatus:
    state: ComfyUiState = "not_installed"
    installed_path: str | None = None
    process_id: int | None = None
    port: int = 8188
    base_url: str = "http://localhost:8188"
    message: str | None = None
    error: str | None = None
    last_check: float | None = None


class ComfyUiManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._status = ComfyUiManagerStatus()
        self._process: subprocess.Popen[str] | None = None
        self._log_buffer: list[str] = []
        self._max_log_lines = 1000

        # ComfyUI installation directory
        self._comfyui_dir = comfyui_dir()
        self._comfyui_port = 8188

        # Start background thread to monitor ComfyUI status
        self._monitor_thread = threading.Thread(target=self._monitor_loop, name="comfyui-monitor", daemon=True)
        self._monitor_thread.start()

        # Initial status check
        self._update_status()

    def status(self) -> ComfyUiManagerStatus:
        """Get current ComfyUI manager status."""
        with self._lock:
            return ComfyUiManagerStatus(**asdict(self._status))

    def logs(self, limit: int = 500) -> list[str]:
        """Get recent logs from ComfyUI process."""
        with self._lock:
            return list(self._log_buffer[-limit:])

    def is_installed(self) -> bool:
        """Check if ComfyUI is installed."""
        main_py = self._comfyui_dir / "main.py"
        return main_py.exists()

    def install(self) -> None:
        """Install ComfyUI by cloning from GitHub."""
        with self._lock:
            if self._status.state == "starting" or self._status.state == "running":
                raise RuntimeError("Cannot install while ComfyUI is running")
            if self.is_installed():
                raise RuntimeError("ComfyUI is already installed")

            self._status.state = "installing"
            self._status.message = "Installing ComfyUI..."

        self._append_log("info", "Starting ComfyUI installation")

        try:
            # Check if git is available
            git_path = shutil.which("git")
            if not git_path:
                raise RuntimeError("Git is required to install ComfyUI. Install Git first.")

            # Clone ComfyUI repository
            self._append_log("info", f"Cloning ComfyUI repository to {self._comfyui_dir}")
            self._comfyui_dir.parent.mkdir(parents=True, exist_ok=True)

            # Remove existing directory if it exists but is incomplete
            if self._comfyui_dir.exists():
                shutil.rmtree(self._comfyui_dir)

            code, output = self._run_cmd(
                ["git", "clone", "https://github.com/comfyanonymous/ComfyUI.git", str(self._comfyui_dir)],
                timeout_s=600,
            )

            if code != 0:
                raise RuntimeError(f"Git clone failed: {output}")

            self._append_log("info", "ComfyUI cloned successfully")

            # Check if Python requirements need to be installed
            requirements_txt = self._comfyui_dir / "requirements.txt"
            if requirements_txt.exists():
                self._append_log("info", "Installing Python dependencies...")
                python_exe = shutil.which("python3") or shutil.which("python")
                if not python_exe:
                    raise RuntimeError("Python is required but not found")

                code, output = self._run_cmd(
                    [python_exe, "-m", "pip", "install", "-r", str(requirements_txt)],
                    cwd=self._comfyui_dir,
                    timeout_s=1800,
                )

                if code != 0:
                    self._append_log("warning", f"pip install had issues: {output}")
                    # Don't fail - user might install manually

            with self._lock:
                self._status.state = "installed"
                self._status.installed_path = str(self._comfyui_dir)
                self._status.message = "ComfyUI installed successfully"
                self._status.error = None

            self._append_log("info", "ComfyUI installation complete")
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self._status.state = "error"
                self._status.error = str(exc)
                self._status.message = f"Installation failed: {exc}"
            self._append_log("error", f"ComfyUI installation failed: {exc}")
            raise

    def start(self) -> None:
        """Start ComfyUI process."""
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                raise RuntimeError("ComfyUI is already running")

            if not self.is_installed():
                raise RuntimeError("ComfyUI is not installed. Install it first.")

            self._status.state = "starting"
            self._status.message = "Starting ComfyUI..."

        self._append_log("info", "Starting ComfyUI process")

        try:
            python_exe = shutil.which("python3") or shutil.which("python")
            if not python_exe:
                raise RuntimeError("Python is required but not found")

            main_py = self._comfyui_dir / "main.py"
            if not main_py.exists():
                raise RuntimeError("ComfyUI main.py not found. Reinstall ComfyUI.")

            # Build command
            cmd = [python_exe, str(main_py), "--port", str(self._comfyui_port)]

            # Start process with output capture
            env = os.environ.copy()
            # Set CUDA_VISIBLE_DEVICES if needed (can be configured later)

            self._append_log("info", f"Running: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                cwd=str(self._comfyui_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
            )

            with self._lock:
                self._process = process
                self._status.process_id = process.pid
                self._status.port = self._comfyui_port
                self._status.base_url = f"http://localhost:{self._comfyui_port}"

            # Start log reader thread
            log_thread = threading.Thread(
                target=self._read_logs,
                args=(process,),
                name="comfyui-log-reader",
                daemon=True,
            )
            log_thread.start()

            self._append_log("info", f"ComfyUI process started (PID: {process.pid})")

            # Wait a bit and check if process is still alive
            time.sleep(2)
            if process.poll() is not None:
                # Process died immediately
                code = process.returncode
                raise RuntimeError(f"ComfyUI process exited immediately with code {code}")

            with self._lock:
                self._status.state = "running"
                self._status.message = "ComfyUI is running"

        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self._status.state = "error"
                self._status.error = str(exc)
                self._status.message = f"Failed to start: {exc}"
                if self._process:
                    try:
                        self._process.terminate()
                    except Exception:  # noqa: BLE001
                        pass
                    self._process = None
            self._append_log("error", f"Failed to start ComfyUI: {exc}")
            raise

    def stop(self) -> None:
        """Stop ComfyUI process."""
        with self._lock:
            if self._process is None:
                raise RuntimeError("ComfyUI is not running")

            self._status.state = "stopping"
            self._status.message = "Stopping ComfyUI..."

        self._append_log("info", "Stopping ComfyUI process")

        try:
            process = self._process
            if process and process.poll() is None:
                # Try graceful termination first
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't stop
                    self._append_log("warning", "ComfyUI didn't stop gracefully, forcing kill")
                    process.kill()
                    process.wait()

            with self._lock:
                self._process = None
                self._status.process_id = None
                self._status.state = "stopped"
                self._status.message = "ComfyUI stopped"
                self._status.error = None

            self._append_log("info", "ComfyUI stopped successfully")
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self._status.state = "error"
                self._status.error = str(exc)
                self._status.message = f"Failed to stop: {exc}"
            self._append_log("error", f"Failed to stop ComfyUI: {exc}")
            raise

    def restart(self) -> None:
        """Restart ComfyUI process."""
        was_running = False
        with self._lock:
            was_running = self._process is not None and self._process.poll() is None

        if was_running:
            self.stop()
            time.sleep(1)
        self.start()

    def sync_models(self) -> dict[str, Any]:
        """
        Sync models from Model Manager to ComfyUI folders.
        Creates symlinks (macOS/Linux) or junctions (Windows).
        """
        from app.services.model_manager import model_manager

        self._append_log("info", "Syncing models to ComfyUI folders")

        try:
            if not self.is_installed():
                raise RuntimeError("ComfyUI is not installed")

            # Get installed models from Model Manager
            installed = model_manager.installed()
            if not installed:
                return {"synced": 0, "skipped": 0, "errors": []}

            # Map model types to ComfyUI folders
            type_map: dict[str, str] = {
                "checkpoint": "checkpoints",
                "lora": "loras",
                "embedding": "embeddings",
                "controlnet": "controlnet",
                "vae": "vae",
            }

            models_root = data_dir() / "models"
            comfyui_models = self._comfyui_dir / "models"

            synced = 0
            skipped = 0
            errors: list[str] = []

            for model_info in installed:
                rel_path = model_info.get("path", "")
                if not rel_path:
                    continue

                # Determine model type from path
                parts = Path(rel_path).parts
                model_type = parts[0] if parts else "other"
                filename = parts[-1] if parts else ""

                if model_type not in type_map:
                    skipped += 1
                    continue

                # Source file
                source = models_root / rel_path
                if not source.exists():
                    skipped += 1
                    continue

                # Target symlink/junction
                target_dir = comfyui_models / type_map[model_type]
                target_dir.mkdir(parents=True, exist_ok=True)
                target = target_dir / filename

                # Skip if already linked
                if target.exists():
                    skipped += 1
                    continue

                try:
                    # Create symlink (macOS/Linux) or junction (Windows)
                    system = platform.system().lower()
                    if system in {"darwin", "linux"}:
                        # Unix: use symlink
                        target.symlink_to(source)
                        synced += 1
                        self._append_log("info", f"Created symlink: {target} -> {source}")
                    elif system == "windows":
                        # Windows: use junction (requires admin or Developer Mode)
                        # Fallback: try mklink command
                        try:
                            # Try creating junction using mklink command
                            # Use junction (directory) or symlink (file)
                            if source.is_dir():
                                result = subprocess.run(
                                    ["cmd", "/c", "mklink", "/J", str(target), str(source)],
                                    check=False,
                                    capture_output=True,
                                    text=True,
                                )
                            else:
                                result = subprocess.run(
                                    ["cmd", "/c", "mklink", str(target), str(source)],
                                    check=False,
                                    capture_output=True,
                                    text=True,
                                )

                            if result.returncode == 0:
                                synced += 1
                                self._append_log("info", f"Created junction: {target} -> {source}")
                            else:
                                # On Windows without admin, we can't create junctions easily
                                # Copy the file instead (not ideal but works)
                                if source.is_file():
                                    shutil.copy2(source, target)
                                    synced += 1
                                    self._append_log("info", f"Copied file: {target} (admin required for symlinks)")
                                else:
                                    errors.append(f"Windows junction requires admin: {target}")
                        except Exception as e:  # noqa: BLE001
                            errors.append(f"Failed to create junction for {filename}: {e}")
                    else:
                        errors.append(f"Unsupported OS for symlinks: {system}")

                except Exception as e:  # noqa: BLE001
                    errors.append(f"Failed to sync {filename}: {e}")
                    self._append_log("error", f"Failed to sync {filename}: {e}")

            result = {"synced": synced, "skipped": skipped, "errors": errors}
            self._append_log("info", f"Model sync complete: {synced} synced, {skipped} skipped, {len(errors)} errors")
            return result

        except Exception as exc:  # noqa: BLE001
            self._append_log("error", f"Model sync failed: {exc}")
            raise

    def _update_status(self) -> None:
        """Update status by checking installation and process state."""
        with self._lock:
            installed = self.is_installed()
            process_running = self._process is not None and self._process.poll() is None

            if installed:
                self._status.installed_path = str(self._comfyui_dir)
            else:
                self._status.installed_path = None

            if process_running:
                if self._status.state not in {"starting", "running"}:
                    self._status.state = "running"
                    self._status.message = "ComfyUI is running"
            else:
                if self._status.state == "running":
                    self._status.state = "stopped"
                    self._status.message = "ComfyUI process stopped"
                elif self._status.state == "starting":
                    self._status.state = "error"
                    self._status.message = "ComfyUI failed to start"

            # Also check if ComfyUI is reachable via HTTP
            if process_running:
                try:
                    client = ComfyUiClient(base_url=self._status.base_url)
                    client.get_system_stats()
                    self._status.state = "running"
                    self._status.message = "ComfyUI is running and responding"
                except ComfyUiError:
                    # Process exists but not responding yet (might be starting)
                    if self._status.state == "running":
                        self._status.message = "ComfyUI is starting..."

            self._status.last_check = time.time()

    def _monitor_loop(self) -> None:
        """Background thread to monitor ComfyUI status."""
        while True:
            try:
                time.sleep(5)  # Check every 5 seconds
                self._update_status()
            except Exception as exc:  # noqa: BLE001
                logger.error("Error in ComfyUI monitor loop", extra={"error": str(exc)})
                time.sleep(10)

    def _read_logs(self, process: subprocess.Popen[str]) -> None:
        """Read logs from ComfyUI process stdout."""
        if process.stdout is None:
            return

        try:
            for line in iter(process.stdout.readline, ""):
                if not line:
                    break
                line_clean = line.rstrip()
                if line_clean:
                    self._append_log("stdout", line_clean)
        except Exception as exc:  # noqa: BLE001
            self._append_log("error", f"Error reading logs: {exc}")

    def _append_log(self, level: str, message: str) -> None:
        """Append log message to buffer."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level.upper()}] {message}"

        with self._lock:
            self._log_buffer.append(log_line)
            if len(self._log_buffer) > self._max_log_lines:
                self._log_buffer.pop(0)

        logger.info(message, extra={"comfyui_manager": {"level": level}})

    def _run_cmd(
        self,
        cmd: list[str],
        cwd: Path | None = None,
        timeout_s: float = 900,
        env: dict[str, str] | None = None,
    ) -> tuple[int, str]:
        """Run a command and return (returncode, output)."""
        try:
            p = subprocess.run(
                cmd,
                cwd=str(cwd) if cwd else None,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
                env=env,
            )
            out = (p.stdout or "").strip()
            err = (p.stderr or "").strip()
            combined = (out + ("\n" + err if err else "")).strip()
            return p.returncode, combined
        except Exception as exc:  # noqa: BLE001
            return 1, str(exc)


# Global instance
comfyui_manager = ComfyUiManager()

