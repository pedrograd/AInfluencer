from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def _run(cmd: list[str], timeout_s: float = 2.5) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, check=False)
        out = (p.stdout or "").strip() or (p.stderr or "").strip()
        return p.returncode, out
    except Exception as exc:  # noqa: BLE001
        return 1, str(exc)


def _which(binary: str) -> str | None:
    path = shutil.which(binary)
    return path


def _bytes_to_gb(n: int) -> float:
    return round(n / (1024**3), 2)


def _get_ram_bytes_best_effort() -> int | None:
    system = platform.system().lower()

    # macOS
    if system == "darwin":
        code, out = _run(["sysctl", "-n", "hw.memsize"])
        if code == 0:
            try:
                return int(out.strip())
            except ValueError:
                return None

    # Linux
    if system == "linux":
        try:
            with open("/proc/meminfo", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        parts = line.split()
                        kb = int(parts[1])
                        return kb * 1024
        except Exception:  # noqa: BLE001
            return None

    # Windows (best effort)
    if system == "windows":
        code, out = _run(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"])
        if code == 0:
            try:
                return int(float(out.strip()))
            except ValueError:
                return None

    return None


def system_check(project_root: Path) -> dict[str, Any]:
    now = time.time()

    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = (sys.version_info.major, sys.version_info.minor) in {(3, 12), (3, 13)}
    supported_versions = ["3.12", "3.13"]

    node_path = _which("node")
    git_path = _which("git")

    nvidia_smi = _which("nvidia-smi")
    gpu = {
        "nvidia_smi": bool(nvidia_smi),
        "nvidia_smi_path": nvidia_smi,
        "nvidia_smi_output": None,
    }
    if nvidia_smi:
        _, out = _run(["nvidia-smi", "-L"], timeout_s=2.5)
        gpu["nvidia_smi_output"] = out

    disk = shutil.disk_usage(project_root)
    ram_bytes = _get_ram_bytes_best_effort()
    os_system = platform.system()

    issues: list[dict[str, Any]] = []
    if not py_ok:
        fix: dict[str, Any] = {
            "summary": f"Install Python {' or '.join(supported_versions)}",
            "repo_scripts": [
                {"os": "macos", "path": "scripts/setup/install_python_macos.sh"},
                {"os": "windows", "path": "scripts/setup/install_python_windows.ps1"},
            ],
        }
        issues.append(
            {
                "code": "PYTHON_UNSUPPORTED",
                "severity": "error",
                "title": "Unsupported Python version",
                "detail": f"Detected Python {py_ver}. Supported: {', '.join(supported_versions)}.",
                "fix": fix,
            }
        )

    if not node_path:
        issues.append(
            {
                "code": "NODE_MISSING",
                "severity": "error",
                "title": "Node.js is missing",
                "detail": "Install Node.js (LTS recommended). It is required to run the dashboard.",
                "fix": {"summary": "Install Node.js from nodejs.org"},
            }
        )

    if not git_path:
        issues.append(
            {
                "code": "GIT_MISSING",
                "severity": "warn",
                "title": "Git is missing",
                "detail": "Git is recommended for updates and troubleshooting.",
                "fix": {"summary": "Install Git"},
            }
        )

    # Disk sanity (very lightweight thresholds for MVP)
    free_gb = _bytes_to_gb(disk.free)
    if free_gb < 20:
        issues.append(
            {
                "code": "DISK_LOW",
                "severity": "warn",
                "title": "Low disk space",
                "detail": f"Only {free_gb} GB free. Model downloads can be large.",
                "fix": {"summary": "Free up disk space (recommended 100GB+)"},
            }
        )

    return {
        "ts": now,
        "os": {
            "system": os_system,
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
        },
        "python": {
            "executable": sys.executable,
            "version": py_ver,
            "supported": py_ok,
            "supported_versions": supported_versions,
        },
        "tools": {
            "node": {"found": bool(node_path), "path": node_path},
            "git": {"found": bool(git_path), "path": git_path},
        },
        "resources": {
            "disk_total_gb": _bytes_to_gb(disk.total),
            "disk_free_gb": _bytes_to_gb(disk.free),
            "ram_total_gb": _bytes_to_gb(ram_bytes) if ram_bytes else None,
        },
        "gpu": gpu,
        "issues": issues,
        "notes": [
            "This is an MVP system check; it will expand as we add model engines.",
        ],
    }


def system_check_json(project_root: Path) -> str:
    return json.dumps(system_check(project_root), indent=2, sort_keys=True)
