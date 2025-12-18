"""Local ComfyUI engine adapter.

This module provides the LocalComfyAdapter that wraps the existing ComfyUiClient
to implement the EngineAdapter interface for local ComfyUI instances.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.error_taxonomy import ErrorCode, create_error_response
from app.core.logging import get_logger
from app.core.paths import content_dir
from app.core.runtime_settings import get_comfyui_base_url
from app.services.comfyui_client import ComfyUiClient, ComfyUiError
from app.services.engines.base import EngineAdapter

logger = get_logger(__name__)


class LocalComfyAdapter(EngineAdapter):
    """Adapter for local ComfyUI engine.
    
    Wraps the existing ComfyUiClient to provide a unified EngineAdapter interface.
    """

    def __init__(self, base_url: str | None = None) -> None:
        """Initialize local ComfyUI adapter.
        
        Args:
            base_url: Optional ComfyUI base URL (defaults to config/runtime settings)
        """
        # Get base URL from parameter, runtime settings, or config
        effective_url = (
            base_url
            or get_comfyui_base_url().value
            or settings.comfyui_base_url
        )
        self.base_url = effective_url.rstrip("/")
        self._client = ComfyUiClient(base_url=self.base_url)

    @property
    def engine_id(self) -> str:
        """Engine identifier."""
        return "local_comfy"

    @property
    def engine_type(self) -> str:
        """Engine type."""
        return "local"

    async def health_check(self) -> bool:
        """Check if ComfyUI is reachable and ready.
        
        Returns:
            True if ComfyUI is healthy, False otherwise
        """
        try:
            # Try to queue a simple test workflow
            # For MVP, we'll just check if the endpoint is reachable
            # by attempting to get the system stats endpoint
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/system_stats")
                return response.status_code == 200
        except Exception as e:
            logger.debug(f"ComfyUI health check failed: {e}")
            return False

    async def generate_image(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate image using ComfyUI.
        
        Args:
            prompt: Text prompt describing the image
            **kwargs: Additional parameters:
                - negative_prompt: Optional negative prompt
                - seed: Optional random seed
                - checkpoint: Optional checkpoint name
                - width: Image width (default: 1024)
                - height: Image height (default: 1024)
                - steps: Number of steps (default: 25)
                - cfg: CFG scale (default: 7.0)
                - sampler_name: Sampler name (default: "euler")
                - scheduler: Scheduler name (default: "normal")
                
        Returns:
            Dictionary with 'output_path' key pointing to generated image
            
        Raises:
            RuntimeError: If generation fails
        """
        # Extract parameters
        negative_prompt = kwargs.get("negative_prompt")
        seed = kwargs.get("seed", 0)
        checkpoint = kwargs.get("checkpoint") or settings.default_checkpoint
        width = kwargs.get("width", 1024)
        height = kwargs.get("height", 1024)
        steps = kwargs.get("steps", 25)
        cfg = kwargs.get("cfg", 7.0)
        sampler_name = kwargs.get("sampler_name", "euler")
        scheduler = kwargs.get("scheduler", "normal")

        # Build basic ComfyUI workflow
        workflow = self._build_basic_workflow(
            prompt=prompt,
            negative_prompt=negative_prompt,
            seed=seed,
            checkpoint=checkpoint,
            width=width,
            height=height,
            steps=steps,
            cfg=cfg,
            sampler_name=sampler_name,
            scheduler=scheduler,
        )

        try:
            # Queue workflow (sync call, but we're in async context)
            # For MVP, we'll run sync operations in executor if needed
            # For now, ComfyUiClient is sync, so we call it directly
            import asyncio
            loop = asyncio.get_event_loop()
            prompt_id = await loop.run_in_executor(None, self._client.queue_prompt, workflow)
            logger.info(f"Queued ComfyUI workflow: prompt_id={prompt_id}")

            # Wait for result (sync call in executor)
            result = await loop.run_in_executor(
                None, self._client.wait_for_first_image, prompt_id, 300
            )
            filename = result.get("filename")
            if not filename:
                raise RuntimeError("ComfyUI returned image without filename")

            # Construct output path
            # ComfyUI saves to its output directory, we need to find the file
            # For MVP, assume ComfyUI output is accessible via /view endpoint
            output_path = f"{self.base_url}/view?filename={filename}"

            # Also try to construct local path if we know ComfyUI output directory
            # This is a simplified version - in production, we'd track ComfyUI output dir
            local_output_path = content_dir() / "images" / filename

            return {
                "output_path": str(local_output_path),
                "output_url": output_path,
                "filename": filename,
                "prompt_id": prompt_id,
            }
        except ComfyUiError as e:
            error_msg = str(e)
            if "Unable to reach ComfyUI" in error_msg:
                raise RuntimeError(
                    f"ComfyUI is not running at {self.base_url}. "
                    "Start ComfyUI in Setup Hub."
                ) from e
            raise RuntimeError(f"ComfyUI generation failed: {error_msg}") from e

    def _build_basic_workflow(
        self,
        prompt: str,
        negative_prompt: str | None,
        seed: int,
        checkpoint: str | None,
        width: int,
        height: int,
        steps: int,
        cfg: float,
        sampler_name: str,
        scheduler: str,
    ) -> dict[str, Any]:
        """Build a basic ComfyUI workflow for image generation.
        
        This is a simplified workflow builder. In production, this would
        be more sophisticated and support custom nodes, LoRAs, etc.
        """
        # Use default checkpoint if not specified
        checkpoint_name = checkpoint or "sd_xl_base_1.0.safetensors"

        workflow = {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": checkpoint_name},
            },
            "2": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": prompt,
                    "clip": ["1", 1],
                },
            },
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": negative_prompt or "",
                    "clip": ["1", 1],
                },
            },
            "4": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1,
                },
            },
            "5": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": sampler_name,
                    "scheduler": scheduler,
                    "denoise": 1.0,
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["4", 0],
                },
            },
            "6": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["5", 0],
                    "vae": ["1", 2],
                },
            },
            "7": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "ComfyUI",
                    "images": ["6", 0],
                },
            },
        }

        return workflow
