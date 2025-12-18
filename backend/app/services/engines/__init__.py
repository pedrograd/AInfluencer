"""Engine adapters for pipeline system.

This package provides engine adapters that wrap different generation engines
(local ComfyUI, remote APIs) into a unified interface.
"""

from app.services.engines.base import EngineAdapter
from app.services.engines.local_comfy_adapter import LocalComfyAdapter
from app.services.engines.registry import engine_registry

__all__ = ["EngineAdapter", "LocalComfyAdapter", "engine_registry"]
