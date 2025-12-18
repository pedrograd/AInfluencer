"""Base engine adapter interface.

This module defines the EngineAdapter abstract base class that all engine
adapters must implement to provide a unified interface for different
generation engines.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class EngineAdapter(ABC):
    """Base interface for all engine adapters (local and remote).
    
    All engine adapters must implement this interface to provide a
    consistent API for the pipeline manager.
    """

    @property
    @abstractmethod
    def engine_id(self) -> str:
        """Unique engine identifier (e.g., 'local_comfy', 'provider_kling')."""
        pass

    @property
    @abstractmethod
    def engine_type(self) -> str:
        """Engine type: 'local' or 'remote'."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if engine is reachable and ready.
        
        Returns:
            True if engine is healthy and ready, False otherwise
        """
        pass

    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate image.
        
        Args:
            prompt: Text prompt describing the image
            **kwargs: Additional generation parameters (steps, cfg, width, height, etc.)
            
        Returns:
            Dictionary with 'output_path' or 'output_url' key and optional metadata
            
        Raises:
            RuntimeError: If generation fails
        """
        pass

    async def generate_video(
        self,
        image_path: str | None = None,
        prompt: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate video (optional, not all engines support this).
        
        Args:
            image_path: Optional path to input image
            prompt: Optional text prompt
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with 'output_path' or 'output_url'
            
        Raises:
            NotImplementedError: If engine doesn't support video generation
        """
        raise NotImplementedError(f"{self.engine_id} does not support video generation")

    async def apply_lipsync(
        self,
        video_path: str,
        audio_path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Apply lip-sync to video (optional).
        
        Args:
            video_path: Path to video file
            audio_path: Path to audio file
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with 'output_path' or 'output_url'
            
        Raises:
            NotImplementedError: If engine doesn't support lip-sync
        """
        raise NotImplementedError(f"{self.engine_id} does not support lip-sync")

    async def upscale(
        self,
        image_path: str | None = None,
        video_path: str | None = None,
        scale: int = 2,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Upscale image or video (optional).
        
        Args:
            image_path: Optional path to image file
            video_path: Optional path to video file
            scale: Upscale factor (default: 2)
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with 'output_path' or 'output_url'
            
        Raises:
            NotImplementedError: If engine doesn't support upscaling
        """
        raise NotImplementedError(f"{self.engine_id} does not support upscaling")
