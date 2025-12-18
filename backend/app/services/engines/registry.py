"""Engine registry for pipeline system.

This module provides a registry of available engine adapters.
"""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.services.engines.base import EngineAdapter
from app.services.engines.local_comfy_adapter import LocalComfyAdapter

logger = get_logger(__name__)


class EngineRegistry:
    """Registry for engine adapters."""

    def __init__(self) -> None:
        """Initialize engine registry."""
        self._engines: dict[str, EngineAdapter] = {}
        self._initialize_engines()

    def _initialize_engines(self) -> None:
        """Initialize available engines."""
        # Phase 1: Only local ComfyUI
        try:
            local_comfy = LocalComfyAdapter()
            self._engines["local_comfy"] = local_comfy
            logger.info("Registered engine: local_comfy")
        except Exception as e:
            logger.warning(f"Failed to initialize local_comfy engine: {e}")

    def get_engine(self, engine_id: str) -> EngineAdapter | None:
        """Get engine adapter by ID.
        
        Args:
            engine_id: Engine identifier
            
        Returns:
            EngineAdapter instance or None if not found
        """
        return self._engines.get(engine_id)

    def list_engines(self) -> list[dict[str, Any]]:
        """List all registered engines with status.
        
        Returns:
            List of engine info dictionaries
        """
        engines = []
        for engine_id, engine in self._engines.items():
            # Check health (synchronous for now, could be async in future)
            try:
                import asyncio
                health = asyncio.run(engine.health_check())
            except Exception:
                health = False

            engines.append({
                "engine_id": engine_id,
                "engine_type": engine.engine_type,
                "healthy": health,
            })

        return engines

    def engine_available(self, engine_id: str) -> bool:
        """Check if engine is available.
        
        Args:
            engine_id: Engine identifier
            
        Returns:
            True if engine is registered, False otherwise
        """
        return engine_id in self._engines


# Global registry instance
engine_registry = EngineRegistry()
