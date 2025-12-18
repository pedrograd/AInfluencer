"""System installation and dependency management service."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from app.core.logging import get_logger
from app.core.paths import logs_dir, repo_root
from app.services.system_check import system_check
from app.services.comfyui_service import ComfyUIServiceManager

logger = get_logger(__name__)

InstallState = Literal["idle", "running", "failed", "succeeded"]


@dataclass
class InstallerStatus:
    """Installer service status information.
    
    Attributes:
        state: Current installation state (idle, running, completed, error).
        step: Current installation step name, None if not running.
        message: Human-readable status message describing the current step.
        progress: Installation progress percentage (0-100).
        started_at: Timestamp when installation started (Unix timestamp), None if not started.
        finished_at: Timestamp when installation finished (Unix timestamp), None if not finished.
    """
    state: InstallState = "idle"
    step: str | None = None
    message: str | None = None
    progress: int = 0
    started_at: float | None = None
    finished_at: float | None = None


class InstallerService:
    """Service for installing dependencies and setting up the environment."""

    def __init__(self) -> None:
        """Initialize installer service with thread lock and status tracking."""
        self._lock = threading.Lock()
        self._status = InstallerStatus()
        self._memory_logs: list[dict[str, Any]] = []
        self._thread: threading.Thread | None = None

        logs_dir().mkdir(parents=True, exist_ok=True)
        self._log_path = logs_dir() / "installer.jsonl"

    def status(self) -> InstallerStatus:
        with self._lock:
            return InstallerStatus(**asdict(self._status))

    def logs(self, limit: int = 1000) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._memory_logs[-limit:])

    def append_log(self, level: str, message: str, **extra: Any) -> None:
        event = {"ts": time.time(), "level": level, "message": message, **extra}

        with self._lock:
            self._memory_logs.append(event)

        # Persist for support/debugging
        try:
            with self._log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to write installer log", extra={"error": str(exc)})

        logger.info(message, extra={"installer": {"level": level, **extra}})

    def check(self) -> dict[str, Any]:
        root = repo_root()
        return system_check(root)
    
    def repair(self) -> dict[str, Any]:
        """
        Run comprehensive system repair.
        
        Performs:
        1. Re-run doctor/system checks
        2. Repair backend venv (check Python version, recreate if wrong)
        3. Reinstall backend deps if corrupted (check imports, reinstall if needed)
        4. Re-check ports (verify backend/frontend ports are available)
        5. Re-check ComfyUI health
        
        Returns:
            dict: Repair results with status and details
        """
        results = {
            "checks_run": False,
            "venv_repaired": False,
            "deps_reinstalled": False,
            "ports_checked": False,
            "comfyui_checked": False,
            "issues_found": [],
            "issues_fixed": [],
        }
        
        try:
            # Step 1: Re-run system checks
            self.append_log("info", "Repair: Running system checks...")
            check_result = self.check()
            results["checks_run"] = True
            
            # Check for issues
            issues = check_result.get("issues", [])
            if issues:
                results["issues_found"].extend([i.get("title", "Unknown issue") for i in issues])
                self.append_log("warning", f"Repair: Found {len(issues)} issue(s) in system check")
            
            # Step 2: Check and repair backend venv
            self.append_log("info", "Repair: Checking backend virtual environment...")
            root = repo_root()
            backend_dir = root / "backend"
            venv_dir = backend_dir / ".venv"
            venv_python = venv_dir / ("Scripts" / "python.exe" if os.name == "nt" else "bin" / "python")
            
            venv_needs_repair = False
            if venv_python.exists():
                # Check Python version
                code, output = self._run_cmd([str(venv_python), "--version"], cwd=backend_dir)
                if code == 0:
                    # Parse version
                    match = re.search(r"Python (\d+)\.(\d+)\.(\d+)", output)
                    if match:
                        major, minor = int(match.group(1)), int(match.group(2))
                        if major != 3 or minor != 11:
                            self.append_log("warning", f"Repair: Venv Python version mismatch ({major}.{minor}, need 3.11)")
                            venv_needs_repair = True
                else:
                    self.append_log("warning", "Repair: Cannot verify venv Python, will recreate")
                    venv_needs_repair = True
            else:
                self.append_log("info", "Repair: Venv not found, will create")
                venv_needs_repair = True
            
            if venv_needs_repair:
                # Find Python 3.11
                python_cmd = None
                for cmd in ["python3.11", "py -3.11", "python"]:
                    code, output = self._run_cmd([cmd, "--version"] if " " not in cmd else cmd.split() + ["--version"])
                    if code == 0:
                        match = re.search(r"Python (\d+)\.(\d+)", output)
                        if match and int(match.group(1)) == 3 and int(match.group(2)) == 11:
                            python_cmd = cmd.split() if " " in cmd else [cmd]
                            break
                
                if not python_cmd:
                    results["issues_found"].append("Python 3.11 not found - cannot repair venv")
                    self.append_log("error", "Repair: Python 3.11 not found")
                else:
                    # Remove old venv if exists
                    if venv_dir.exists():
                        self.append_log("info", "Repair: Removing old venv...")
                        shutil.rmtree(venv_dir, ignore_errors=True)
                    
                    # Create new venv
                    self.append_log("info", "Repair: Creating new venv...")
                    code, output = self._run_cmd(python_cmd + ["-m", "venv", ".venv"], cwd=backend_dir)
                    if code == 0:
                        results["venv_repaired"] = True
                        results["issues_fixed"].append("Recreated backend virtual environment")
                        self.append_log("info", "Repair: Venv created successfully")
                    else:
                        results["issues_found"].append(f"Failed to create venv: {output}")
                        self.append_log("error", f"Repair: Failed to create venv: {output}")
            
            # Step 3: Check and reinstall backend deps if needed
            # Re-check venv_python path in case venv was recreated
            venv_python = venv_dir / ("Scripts" / "python.exe" if os.name == "nt" else "bin" / "python")
            
            if venv_python.exists() or results["venv_repaired"]:
                self.append_log("info", "Repair: Checking backend dependencies...")
                # Check if key imports work
                if venv_python.exists():
                    code, output = self._run_cmd([str(venv_python), "-c", "import fastapi, uvicorn"], cwd=backend_dir)
                if code != 0:
                    self.append_log("warning", "Repair: Dependencies missing or corrupted, reinstalling...")
                    # Find requirements file
                    req_file = backend_dir / "requirements.core.txt"
                    if not req_file.exists():
                        req_file = backend_dir / "requirements.txt"
                    
                    if req_file.exists():
                        pip_cmd = [str(venv_python), "-m", "pip", "install", "-r", str(req_file)]
                        code, output = self._run_cmd(pip_cmd, cwd=backend_dir, timeout_s=600)
                        if code == 0:
                            results["deps_reinstalled"] = True
                            results["issues_fixed"].append("Reinstalled backend dependencies")
                            self.append_log("info", "Repair: Dependencies reinstalled successfully")
                        else:
                            results["issues_found"].append(f"Failed to reinstall deps: {output[:200]}")
                            self.append_log("error", f"Repair: Failed to reinstall deps: {output[:200]}")
                    else:
                        results["issues_found"].append("Requirements file not found")
                        self.append_log("error", "Repair: Requirements file not found")
                else:
                    self.append_log("info", "Repair: Dependencies are OK")
            
            # Step 4: Check ports
            self.append_log("info", "Repair: Checking port availability...")
            import socket
            ports_to_check = [8000, 8001, 8002, 3000, 3001, 3002]
            available_ports = []
            in_use_ports = []
            
            for port in ports_to_check:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(0.5)
                        result = sock.connect_ex(("localhost", port))
                        if result == 0:
                            in_use_ports.append(port)
                        else:
                            available_ports.append(port)
                except Exception:
                    pass
            
            results["ports_checked"] = True
            results["available_ports"] = available_ports
            results["in_use_ports"] = in_use_ports
            self.append_log("info", f"Repair: Ports checked - {len(available_ports)} available, {len(in_use_ports)} in use")
            
            # Step 5: Check ComfyUI health
            self.append_log("info", "Repair: Checking ComfyUI health...")
            try:
                comfyui_manager = ComfyUIServiceManager()
                comfyui_status = comfyui_manager.status()
                results["comfyui_checked"] = True
                results["comfyui_status"] = {
                    "state": comfyui_status.state,
                    "installed": comfyui_status.installed,
                    "running": comfyui_status.state == "running",
                    "message": comfyui_status.message,
                }
                self.append_log("info", f"Repair: ComfyUI status - {comfyui_status.state}, installed: {comfyui_status.installed}")
            except Exception as exc:
                results["issues_found"].append(f"ComfyUI check failed: {str(exc)}")
                self.append_log("warning", f"Repair: ComfyUI check failed: {exc}")
            
            # Summary
            total_fixed = len(results["issues_fixed"])
            total_issues = len(results["issues_found"])
            
            self.append_log("info", f"Repair complete - Fixed: {total_fixed}, Remaining issues: {total_issues}")
            
            return results
            
        except Exception as exc:
            self.append_log("error", f"Repair failed: {exc}")
            results["error"] = str(exc)
            return results

    def start(self) -> None:
        with self._lock:
            if self._status.state == "running":
                return

            self._status = InstallerStatus(
                state="running",
                step="check",
                message="Checking system…",
                progress=2,
                started_at=time.time(),
            )

        self.append_log("info", "Installer started")

        t = threading.Thread(target=self._run, name="installer-thread", daemon=True)
        self._thread = t
        t.start()

    def run_fix(self, action: str) -> None:
        """
        Run a remediation action. Strict allowlist only.
        This is intended for local, self-hosted usage.
        """
        allowlisted = {"install_python", "install_node", "install_git"}
        if action not in allowlisted:
            raise ValueError("Unknown fix action")

        with self._lock:
            if self._status.state == "running":
                return
            self._status = InstallerStatus(
                state="running",
                step=f"fix:{action}",
                message=f"Running fix: {action}…",
                progress=10,
                started_at=time.time(),
            )

        self.append_log("info", "Fix started", action=action)
        t = threading.Thread(target=self._run_fix_thread, args=(action,), name="installer-fix-thread", daemon=True)
        self._thread = t
        t.start()

    def run_fix_all(self) -> None:
        """
        Run all required fix actions discovered by system_check(), in a safe order.
        Only allowlisted actions are executed.
        """
        with self._lock:
            if self._status.state == "running":
                return
            self._status = InstallerStatus(
                state="running",
                step="fix_all",
                message="Fixing prerequisites…",
                progress=5,
                started_at=time.time(),
            )

        self.append_log("info", "Fix-all started")
        t = threading.Thread(target=self._run_fix_all_thread, name="installer-fix-all-thread", daemon=True)
        self._thread = t
        t.start()

    def _run_fix_all_thread(self) -> None:
        """
        Run all available fix actions in sequence.
        
        Checks system for issues, collects fix actions, and executes them
        in deterministic order (python -> node -> git). Re-checks system
        after fixes and reports any remaining errors.
        
        Raises:
            RuntimeError: If unsupported fix action is encountered or errors remain after fixes
        """
        try:
            info = self.check()
            issues = list(info.get("issues", []) or [])

            # Collect required fix actions (prefer errors, but include warn if fixable).
            actions: set[str] = set()
            for issue in issues:
                fix = (issue or {}).get("fix") or {}
                action = fix.get("fix_action")
                if isinstance(action, str) and action:
                    actions.add(action)

            # Safe deterministic order: python -> node -> git
            ordered = [a for a in ["install_python", "install_node", "install_git"] if a in actions]
            if not ordered:
                self._set_status(state="succeeded", step="done", message="Nothing to fix", progress=100, finished_at=time.time())
                self.append_log("info", "Fix-all finished (nothing to do)")
                return

            for idx, action in enumerate(ordered, start=1):
                pct = 10 + int((idx - 1) * (80 / max(1, len(ordered))))
                self._set_status(step=f"fix:{action}", message=f"Fixing: {action}…", progress=pct)
                self.append_log("info", "Fix-all running action", action=action, index=idx, total=len(ordered))
                # Reuse the same implementation but run synchronously in this thread.
                if action == "install_python":
                    self._fix_install_python()
                elif action == "install_node":
                    self._fix_install_node()
                elif action == "install_git":
                    self._fix_install_git()
                else:
                    raise RuntimeError("Unsupported fix action")

            # Re-check after fixes
            self._set_status(step="check", message="Re-checking…", progress=95)
            info2 = self.check()
            remaining = [i for i in (info2.get("issues", []) or []) if (i.get("severity") == "error")]
            if remaining:
                self.append_log("error", "Fix-all completed but errors remain", remaining=remaining)
                raise RuntimeError("Fix-all completed but some errors remain. See Issues & fixes.")

            self._set_status(state="succeeded", step="done", message="All prerequisites fixed", progress=100, finished_at=time.time())
            self.append_log("info", "Fix-all finished")
        except Exception as exc:  # noqa: BLE001
            self._set_status(state="failed", message=str(exc), finished_at=time.time())
            self.append_log("error", "Fix-all failed", error=str(exc))

    def _run_fix_thread(self, action: str) -> None:
        """
        Run a single fix action.
        
        Args:
            action: Fix action to run (install_python, install_node, install_git)
        
        Raises:
            RuntimeError: If action is unsupported or fix fails
        """
        try:
            self._set_status(step=f"fix:{action}", message=f"Running fix: {action}…", progress=20)
            if action == "install_python":
                self._fix_install_python()
            elif action == "install_node":
                self._fix_install_node()
            elif action == "install_git":
                self._fix_install_git()
            else:
                raise RuntimeError("Unsupported fix action")
            self._set_status(state="succeeded", step="done", message="Fix complete", progress=100, finished_at=time.time())
            self.append_log("info", "Fix finished", action=action)
        except Exception as exc:  # noqa: BLE001
            self._set_status(state="failed", message=str(exc), finished_at=time.time())
            self.append_log("error", "Fix failed", action=action, error=str(exc))

    def _fix_install_python(self) -> None:
        """
        Install Python using platform-specific install script.
        
        Supports macOS (bash script) and Windows (PowerShell script).
        Updates installer logs with progress and results.
        
        Raises:
            RuntimeError: If install script is missing, install fails, or OS is unsupported
        """
        root = repo_root()
        system = (os.uname().sysname if hasattr(os, "uname") else os.name).lower()
        if system in {"darwin"}:
            script = root / "scripts" / "setup" / "install_python_macos.sh"
            if not script.exists():
                raise RuntimeError("Missing scripts/setup/install_python_macos.sh")
            code, out = self._run_cmd(["bash", str(script)], cwd=root, timeout_s=3600)
            self.append_log("info" if code == 0 else "error", "Python install script finished", action="install_python", output=out)
            if code != 0:
                raise RuntimeError("Python install failed. Download diagnostics and check logs.")
            return

        # Windows: best effort using PowerShell (only if run on Windows).
        if system in {"windows", "nt"}:
            script = root / "scripts" / "setup" / "install_python_windows.ps1"
            if not script.exists():
                raise RuntimeError("Missing scripts/setup/install_python_windows.ps1")
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
            ]
            code, out = self._run_cmd(cmd, cwd=root, timeout_s=3600)
            self.append_log("info" if code == 0 else "error", "Python install script finished", action="install_python", output=out)
            if code != 0:
                raise RuntimeError("Python install failed. Download diagnostics and check logs.")
            return

        raise RuntimeError("Auto-install Python is not supported on this OS yet.")

    def _fix_install_node(self) -> None:
        """
        Install Node.js using platform-specific install script.
        
        Supports macOS (bash script) and Windows (PowerShell script).
        Updates installer logs with progress and results.
        
        Raises:
            RuntimeError: If install script is missing, install fails, or OS is unsupported
        """
        root = repo_root()
        system = (os.uname().sysname if hasattr(os, "uname") else os.name).lower()
        if system in {"darwin"}:
            script = root / "scripts" / "setup" / "install_node_macos.sh"
            if not script.exists():
                raise RuntimeError("Missing scripts/setup/install_node_macos.sh")
            code, out = self._run_cmd(["bash", str(script)], cwd=root, timeout_s=3600)
            self.append_log("info" if code == 0 else "error", "Node install script finished", action="install_node", output=out)
            if code != 0:
                raise RuntimeError("Node install failed. Download diagnostics and check logs.")
            return

        if system in {"windows", "nt"}:
            script = root / "scripts" / "setup" / "install_node_windows.ps1"
            if not script.exists():
                raise RuntimeError("Missing scripts/setup/install_node_windows.ps1")
            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)]
            code, out = self._run_cmd(cmd, cwd=root, timeout_s=3600)
            self.append_log("info" if code == 0 else "error", "Node install script finished", action="install_node", output=out)
            if code != 0:
                raise RuntimeError("Node install failed. Download diagnostics and check logs.")
            return

        raise RuntimeError("Auto-install Node.js is not supported on this OS yet.")

    def _fix_install_git(self) -> None:
        """
        Install Git using platform-specific install script.
        
        Supports macOS (bash script) and Windows (PowerShell script).
        Updates installer logs with progress and results.
        
        Raises:
            RuntimeError: If install script is missing, install fails, or OS is unsupported
        """
        root = repo_root()
        system = (os.uname().sysname if hasattr(os, "uname") else os.name).lower()
        if system in {"darwin"}:
            script = root / "scripts" / "setup" / "install_git_macos.sh"
            if not script.exists():
                raise RuntimeError("Missing scripts/setup/install_git_macos.sh")
            code, out = self._run_cmd(["bash", str(script)], cwd=root, timeout_s=3600)
            self.append_log("info" if code == 0 else "error", "Git install script finished", action="install_git", output=out)
            if code != 0:
                raise RuntimeError("Git install failed. Download diagnostics and check logs.")
            return

        if system in {"windows", "nt"}:
            script = root / "scripts" / "setup" / "install_git_windows.ps1"
            if not script.exists():
                raise RuntimeError("Missing scripts/setup/install_git_windows.ps1")
            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)]
            code, out = self._run_cmd(cmd, cwd=root, timeout_s=3600)
            self.append_log("info" if code == 0 else "error", "Git install script finished", action="install_git", output=out)
            if code != 0:
                raise RuntimeError("Git install failed. Download diagnostics and check logs.")
            return

        raise RuntimeError("Auto-install Git is not supported on this OS yet.")

    def _set_status(self, **kwargs: Any) -> None:
        """
        Update installer status fields atomically.
        
        Args:
            **kwargs: Status fields to update (e.g., state, step, message, progress)
        """
        with self._lock:
            for k, v in kwargs.items():
                setattr(self._status, k, v)

    def _run(self) -> None:
        """
        Execute installer workflow steps in sequence.
        
        Runs system check, creates directories, installs frontend dependencies,
        and performs smoke test. Updates status and logs progress.
        
        Raises:
            RuntimeError: If any step fails (Python version, Node.js missing, etc.)
        """
        try:
            self._step_check()
            self._step_create_dirs()
            self._step_frontend_deps()
            self._step_smoke_test()
            self._set_status(state="succeeded", step="done", message="Ready", progress=100, finished_at=time.time())
            self.append_log("info", "Installer finished", step="done", progress=100)
        except Exception as exc:  # noqa: BLE001
            self._set_status(state="failed", message=str(exc), finished_at=time.time())
            self.append_log("error", "Installer failed", error=str(exc))

    def _run_cmd(
        self,
        cmd: list[str],
        cwd: Path | None = None,
        timeout_s: float = 900,
        env: dict[str, str] | None = None,
    ) -> tuple[int, str]:
        """
        Execute a shell command and return exit code and combined output.
        
        Args:
            cmd: Command and arguments as list
            cwd: Working directory (default: None)
            timeout_s: Command timeout in seconds (default: 900)
            env: Environment variables (default: None)
        
        Returns:
            Tuple of (exit_code, combined_output). Exit code 0 on success, 1 on error.
            Combined output includes both stdout and stderr.
        """
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

    def _step_check(self) -> None:
        """
        Check system prerequisites (Python version, Node.js).
        
        Validates that Python version is supported and Node.js is installed.
        Updates installer status and logs results.
        
        Raises:
            RuntimeError: If Python version is unsupported or Node.js is missing
        """
        self._set_status(step="check", message="Checking system…", progress=5)
        info = self.check()
        self.append_log("info", "System check complete", step="check", python=info.get("python"), tools=info.get("tools"))

        py_supported = bool(info.get("python", {}).get("supported"))
        if not py_supported:
            supported = ", ".join(info.get("python", {}).get("supported_versions", []))
            raise RuntimeError(
                f"Unsupported Python version ({info.get('python', {}).get('version')}). Install Python {supported}."
            )

        node_ok = bool(info.get("tools", {}).get("node", {}).get("found"))
        if not node_ok:
            raise RuntimeError("Node.js is missing. Install Node.js (LTS) to run the dashboard.")

    def _step_create_dirs(self) -> None:
        """
        Create required directory structure for application data.
        
        Creates .ainfluencer directory with subdirectories for models, content,
        temporary files, and logs. Updates installer status and logs progress.
        """
        self._set_status(step="dirs", message="Creating folders…", progress=25)
        root = repo_root()
        data = root / ".ainfluencer"
        (data / "models").mkdir(parents=True, exist_ok=True)
        (data / "content").mkdir(parents=True, exist_ok=True)
        (data / "tmp").mkdir(parents=True, exist_ok=True)
        logs_dir().mkdir(parents=True, exist_ok=True)
        self.append_log("info", "Folders ready", step="dirs", path=str(data))

    def _step_frontend_deps(self) -> None:
        """
        Install frontend dependencies using npm.
        
        Checks if dependencies are already installed (by comparing package-lock.json
        and package.json timestamps). If not, runs npm install. Updates installer
        status and logs progress.
        
        Raises:
            RuntimeError: If frontend folder is missing, npm is not found, or npm install fails
        """
        self._set_status(step="frontend", message="Installing dashboard dependencies…", progress=45)
        root = repo_root()
        frontend = root / "frontend"
        if not frontend.exists():
            raise RuntimeError("frontend/ folder is missing.")

        npm = shutil.which("npm")
        if not npm:
            raise RuntimeError("npm is missing. Install Node.js which includes npm.")

        node_modules = frontend / "node_modules"
        pkg_lock = frontend / "package-lock.json"
        pkg = frontend / "package.json"

        # If dependencies are already installed and lockfile is not older than package.json, skip.
        if node_modules.exists() and pkg_lock.exists() and pkg.exists() and pkg_lock.stat().st_mtime >= pkg.stat().st_mtime:
            self.append_log("info", "Skipping npm install (already installed)", step="frontend")
            return

        started = time.time()
        self.append_log("info", "Running npm install", step="frontend", cwd=str(frontend))
        code, out = self._run_cmd(["npm", "install"], cwd=frontend, timeout_s=1200)
        duration_s = round(time.time() - started, 2)
        if code != 0:
            self.append_log("error", "npm install failed", step="frontend", duration_s=duration_s, output=out)
            raise RuntimeError("Frontend dependency install failed. Download diagnostics and check logs.")
        self.append_log("info", "npm install complete", step="frontend", duration_s=duration_s)

    def _step_smoke_test(self) -> None:
        """
        Run basic smoke test to verify application can be imported.
        
        Attempts to import the main application module to ensure basic
        setup is correct. Updates installer status and logs results.
        """
        self._set_status(step="smoke", message="Running smoke tests…", progress=75)
        # MVP smoke test: prove we can import the app and answer health.
        import importlib

        importlib.import_module("app.main")
        time.sleep(0.1)
        self.append_log("info", "Smoke test passed", step="smoke")


# Singleton instance for use across the application
installer = InstallerService()
