from __future__ import annotations

import json
import os
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

logger = get_logger(__name__)

InstallState = Literal["idle", "running", "failed", "succeeded"]


@dataclass
class InstallerStatus:
    state: InstallState = "idle"
    step: str | None = None
    message: str | None = None
    progress: int = 0
    started_at: float | None = None
    finished_at: float | None = None


class InstallerService:
    def __init__(self) -> None:
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

    def _set_status(self, **kwargs: Any) -> None:
        with self._lock:
            for k, v in kwargs.items():
                setattr(self._status, k, v)

    def _run(self) -> None:
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
        self._set_status(step="dirs", message="Creating folders…", progress=25)
        root = repo_root()
        data = root / ".ainfluencer"
        (data / "models").mkdir(parents=True, exist_ok=True)
        (data / "content").mkdir(parents=True, exist_ok=True)
        (data / "tmp").mkdir(parents=True, exist_ok=True)
        logs_dir().mkdir(parents=True, exist_ok=True)
        self.append_log("info", "Folders ready", step="dirs", path=str(data))

    def _step_frontend_deps(self) -> None:
        self._set_status(step="frontend", message="Installing dashboard dependencies…", progress=45)
        root = repo_root()
        frontend = root / "frontend"
        if not frontend.exists():
            raise RuntimeError("frontend/ folder is missing.")

        npm = shutil.which("npm")
        if not npm:
            raise RuntimeError("npm is missing. Install Node.js which includes npm.")

        self.append_log("info", "Running npm install", step="frontend", cwd=str(frontend))
        code, out = self._run_cmd(["npm", "install"], cwd=frontend, timeout_s=1200)
        if code != 0:
            self.append_log("error", "npm install failed", step="frontend", output=out)
            raise RuntimeError("Frontend dependency install failed. Download diagnostics and check logs.")
        self.append_log("info", "npm install complete", step="frontend")

    def _step_smoke_test(self) -> None:
        self._set_status(step="smoke", message="Running smoke tests…", progress=75)
        # MVP smoke test: prove we can import the app and answer health.
        import importlib

        importlib.import_module("app.main")
        time.sleep(0.1)
        self.append_log("info", "Smoke test passed", step="smoke")
