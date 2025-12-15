"""Path utilities for application directories and files."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Get the repository root directory.
    
    Returns:
        Path to the repository root (parent of backend/ directory).
    """
    # backend/app/core/paths.py -> backend/
    return Path(__file__).resolve().parents[3]


def data_dir() -> Path:
    """Get the application data directory.
    
    All runtime state is kept in a single, gitignored directory.
    
    Returns:
        Path to .ainfluencer/ directory in repository root.
    """
    return repo_root() / ".ainfluencer"


def logs_dir() -> Path:
    """Get the logs directory.
    
    Returns:
        Path to .ainfluencer/logs/ directory.
    """
    return data_dir() / "logs"


def config_dir() -> Path:
    """Get the configuration directory.
    
    Returns:
        Path to .ainfluencer/config/ directory.
    """
    return data_dir() / "config"


def content_dir() -> Path:
    """Get the content storage directory.
    
    Returns:
        Path to .ainfluencer/content/ directory.
    """
    return data_dir() / "content"


def images_dir() -> Path:
    """Get the images storage directory.
    
    Returns:
        Path to .ainfluencer/content/images/ directory.
    """
    return content_dir() / "images"


def jobs_file() -> Path:
    """Get the path to the jobs JSON file.
    
    Returns:
        Path to .ainfluencer/content/jobs.json file.
    """
    return content_dir() / "jobs.json"


def video_jobs_file() -> Path:
    """Get the path to the video jobs JSON file.
    
    Returns:
        Path to .ainfluencer/content/video_jobs.json file.
    """
    return content_dir() / "video_jobs.json"


def comfyui_dir() -> Path:
    """Get the ComfyUI directory.
    
    Returns:
        Path to .ainfluencer/comfyui/ directory.
    """
    return data_dir() / "comfyui"
