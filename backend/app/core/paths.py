from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    # backend/app/core/paths.py -> backend/
    return Path(__file__).resolve().parents[3]


def data_dir() -> Path:
    # Keep all runtime state in a single, gitignored directory.
    return repo_root() / ".ainfluencer"


def logs_dir() -> Path:
    return data_dir() / "logs"


def config_dir() -> Path:
    return data_dir() / "config"


def content_dir() -> Path:
    return data_dir() / "content"


def images_dir() -> Path:
    return content_dir() / "images"


def jobs_file() -> Path:
    return content_dir() / "jobs.json"


def comfyui_dir() -> Path:
    return data_dir() / "comfyui"
