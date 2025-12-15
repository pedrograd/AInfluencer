from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.core.config import settings
from app.core.paths import config_dir


SETTINGS_FILE_NAME = "settings.json"


@dataclass(frozen=True)
class SettingsValue:
    """Runtime setting value with source tracking.
    
    Attributes:
        value: The setting value as a string.
        source: Source of the value ("env", "file", or "default").
    """
    value: str
    source: str  # "env" | "file" | "default"


def _settings_file_path() -> Path:
    """Get the path to the settings JSON file.
    
    Returns:
        Path to .ainfluencer/config/settings.json.
    """
    return config_dir() / SETTINGS_FILE_NAME


def _read_json_file(path: Path) -> dict[str, Any]:
    """Read and parse a JSON file, returning empty dict on error.
    
    Args:
        path: Path to the JSON file to read.
        
    Returns:
        Parsed JSON data as a dictionary, or empty dict if file doesn't exist
        or contains invalid JSON.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _write_json_file(path: Path, data: dict[str, Any]) -> None:
    """Write data to a JSON file, creating parent directories if needed.
    
    Args:
        path: Path to the JSON file to write.
        data: Dictionary data to write as JSON.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _is_valid_http_url(url: str) -> bool:
    """Check if a string is a valid HTTP or HTTPS URL.
    
    Args:
        url: String to validate as a URL.
        
    Returns:
        True if the string is a valid HTTP/HTTPS URL, False otherwise.
    """
    try:
        p = urlparse(url)
    except Exception:
        return False
    return p.scheme in ("http", "https") and bool(p.netloc)


def get_comfyui_base_url() -> SettingsValue:
    """
    Returns the effective ComfyUI base URL.

    Precedence:
    1) AINFLUENCER_COMFYUI_BASE_URL environment variable (explicit override)
    2) .ainfluencer/config/settings.json comfyui_base_url
    3) app.core.config.Settings default
    """
    env_key = "AINFLUENCER_COMFYUI_BASE_URL"
    if os.environ.get(env_key):
        return SettingsValue(value=settings.comfyui_base_url, source="env")

    data = _read_json_file(_settings_file_path())
    v = data.get("comfyui_base_url")
    if isinstance(v, str) and v.strip() and _is_valid_http_url(v.strip()):
        return SettingsValue(value=v.strip().rstrip("/"), source="file")

    return SettingsValue(value=settings.comfyui_base_url.rstrip("/"), source="default")


def read_settings() -> dict[str, Any]:
    """
    Returns persisted settings only (no env/default merging).
    """
    return _read_json_file(_settings_file_path())


def update_settings(*, comfyui_base_url: str | None = None) -> dict[str, Any]:
    """
    Updates persisted settings. Passing None leaves the field unchanged.
    Passing an empty string clears the field.
    """
    data = read_settings()
    if comfyui_base_url is not None:
        v = comfyui_base_url.strip()
        if not v:
            data.pop("comfyui_base_url", None)
        else:
            if not _is_valid_http_url(v):
                raise ValueError("comfyui_base_url must be a valid http(s) URL, e.g. http://localhost:8188")
            data["comfyui_base_url"] = v.rstrip("/")
    _write_json_file(_settings_file_path(), data)
    return data

