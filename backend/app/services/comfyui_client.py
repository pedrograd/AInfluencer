"""ComfyUI API client for workflow execution and image generation."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import httpx

from app.core.config import settings
from app.core.runtime_settings import get_comfyui_base_url


class ComfyUiError(RuntimeError):
    """Error raised when ComfyUI API operations fail.
    
    This exception is raised for various ComfyUI-related errors including
    connection failures, API errors, workflow execution failures, and
    other ComfyUI service issues.
    """
    pass


class ComfyUiClient:
    """Client for interacting with ComfyUI API with connection pooling and caching."""

    def __init__(self, base_url: str | None = None) -> None:
        """
        Initialize ComfyUI client.

        Args:
            base_url: Optional base URL for ComfyUI. If not provided, uses runtime settings
                     or default from config.
        """
        effective = base_url or get_comfyui_base_url().value or settings.comfyui_base_url
        self.base_url = effective.rstrip("/")
        # Persistent HTTP client with connection pooling for better performance
        self._client = httpx.Client(
            timeout=httpx.Timeout(60.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
        )
        # Cache for checkpoint/sampler/scheduler lists (TTL: 60 seconds)
        self._cache: dict[str, tuple[list[str], float]] = {}
        self._cache_ttl = 60.0

    def queue_prompt(self, workflow: dict[str, Any]) -> str:
        """
        Queue a workflow prompt for execution in ComfyUI.

        Args:
            workflow: ComfyUI workflow dictionary containing nodes and connections.

        Returns:
            Prompt ID string for tracking the queued workflow.

        Raises:
            ComfyUiError: If unable to reach ComfyUI or if the request fails.
        """
        url = f"{self.base_url}/prompt"
        try:
            r = self._client.post(url, json={"prompt": workflow}, timeout=30)
        except httpx.RequestError as exc:
            raise ComfyUiError(f"Unable to reach ComfyUI at {self.base_url}") from exc
        if r.status_code != 200:
            raise ComfyUiError(f"ComfyUI /prompt failed: {r.status_code} {r.text}")
        data = r.json()
        prompt_id = data.get("prompt_id")
        if not isinstance(prompt_id, str):
            raise ComfyUiError("ComfyUI response missing prompt_id")
        return prompt_id

    def wait_for_first_image(
        self,
        prompt_id: str,
        timeout_s: float = 300,
        should_cancel: Callable[[], bool] | None = None,
    ) -> dict[str, Any]:
        """Wait until history contains output images, return first output entry."""
        url = f"{self.base_url}/history/{prompt_id}"
        deadline = time.time() + timeout_s
        start_time = time.time()
        # Adaptive polling: start with 2s intervals, increase to 1s as deadline approaches
        poll_interval = 2.0
        
        while time.time() < deadline:
            if should_cancel and should_cancel():
                raise ComfyUiError("Cancelled")
            try:
                r = self._client.get(url, timeout=15)
            except httpx.RequestError as exc:
                raise ComfyUiError(f"Unable to reach ComfyUI at {self.base_url}") from exc
            if r.status_code != 200:
                raise ComfyUiError(f"ComfyUI /history failed: {r.status_code} {r.text}")
            data = r.json()
            entry = data.get(prompt_id)
            if isinstance(entry, dict):
                outputs = entry.get("outputs")
                if isinstance(outputs, dict):
                    # Find first image file ref
                    for node_out in outputs.values():
                        images = node_out.get("images") if isinstance(node_out, dict) else None
                        if isinstance(images, list) and images:
                            first = images[0]
                            if isinstance(first, dict) and "filename" in first:
                                return first
            # Adaptive polling: reduce interval as deadline approaches
            elapsed = time.time() - start_time
            remaining = deadline - time.time()
            if remaining < 30:
                poll_interval = 0.5  # Poll more frequently near deadline
            elif remaining < 60:
                poll_interval = 1.0
            else:
                poll_interval = 2.0
            time.sleep(poll_interval)

        raise ComfyUiError("Timed out waiting for ComfyUI output")

    def wait_for_images(
        self,
        prompt_id: str,
        timeout_s: float = 300,
        should_cancel: Callable[[], bool] | None = None,
    ) -> list[dict[str, Any]]:
        """Wait until history contains output images, return all image file refs."""
        url = f"{self.base_url}/history/{prompt_id}"
        deadline = time.time() + timeout_s
        start_time = time.time()
        # Adaptive polling: start with 2s intervals, increase to 0.5s as deadline approaches
        poll_interval = 2.0
        
        while time.time() < deadline:
            if should_cancel and should_cancel():
                raise ComfyUiError("Cancelled")
            try:
                r = self._client.get(url, timeout=15)
            except httpx.RequestError as exc:
                raise ComfyUiError(f"Unable to reach ComfyUI at {self.base_url}") from exc
            if r.status_code != 200:
                raise ComfyUiError(f"ComfyUI /history failed: {r.status_code} {r.text}")
            data = r.json()
            entry = data.get(prompt_id)
            if isinstance(entry, dict):
                outputs = entry.get("outputs")
                if isinstance(outputs, dict):
                    found: list[dict[str, Any]] = []
                    for node_out in outputs.values():
                        images = node_out.get("images") if isinstance(node_out, dict) else None
                        if isinstance(images, list) and images:
                            for img in images:
                                if isinstance(img, dict) and "filename" in img:
                                    found.append(img)
                    if found:
                        return found
            # Adaptive polling: reduce interval as deadline approaches
            elapsed = time.time() - start_time
            remaining = deadline - time.time()
            if remaining < 30:
                poll_interval = 0.5  # Poll more frequently near deadline
            elif remaining < 60:
                poll_interval = 1.0
            else:
                poll_interval = 2.0
            time.sleep(poll_interval)

        raise ComfyUiError("Timed out waiting for ComfyUI output")

    def download_image_bytes(self, filename: str, subfolder: str = "", image_type: str = "output") -> bytes:
        """
        Download image bytes from ComfyUI.

        Args:
            filename: Name of the image file.
            subfolder: Optional subfolder path within the image type directory.
            image_type: Type of image directory (default: "output").

        Returns:
            Image file content as bytes.

        Raises:
            ComfyUiError: If unable to reach ComfyUI or if the request fails.
        """
        url = f"{self.base_url}/view"
        params = {"filename": filename, "subfolder": subfolder, "type": image_type}
        try:
            r = self._client.get(url, params=params, timeout=60)
        except httpx.RequestError as exc:
            raise ComfyUiError(f"Unable to reach ComfyUI at {self.base_url}") from exc
        if r.status_code != 200:
            raise ComfyUiError(f"ComfyUI /view failed: {r.status_code} {r.text}")
        return r.content

    def get_system_stats(self) -> dict[str, Any]:
        """
        Get ComfyUI system statistics.

        Returns:
            Dictionary containing system stats (GPU usage, memory, etc.).

        Raises:
            ComfyUiError: If unable to reach ComfyUI or if the request fails.
        """
        url = f"{self.base_url}/system_stats"
        try:
            r = self._client.get(url, timeout=10)
        except httpx.RequestError as exc:
            raise ComfyUiError(f"Unable to reach ComfyUI at {self.base_url}") from exc
        if r.status_code != 200:
            raise ComfyUiError(f"ComfyUI /system_stats failed: {r.status_code} {r.text}")
        data = r.json()
        return data if isinstance(data, dict) else {"raw": data}

    def list_checkpoints(self) -> list[str]:
        """
        List available checkpoint models in ComfyUI (cached for 60 seconds).

        Returns:
            List of checkpoint model names.

        Raises:
            ComfyUiError: If unable to reach ComfyUI or if the request fails.
        """
        cache_key = "checkpoints"
        now = time.time()
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if now - cached_time < self._cache_ttl:
                return cached_data
        
        url = f"{self.base_url}/models/checkpoints"
        try:
            r = self._client.get(url, timeout=20)
        except httpx.RequestError as exc:
            raise ComfyUiError(f"Unable to reach ComfyUI at {self.base_url}") from exc
        if r.status_code != 200:
            raise ComfyUiError(f"ComfyUI /models/checkpoints failed: {r.status_code} {r.text}")
        data = r.json()
        if isinstance(data, list):
            result = [str(x) for x in data]
        elif isinstance(data, dict) and isinstance(data.get("checkpoints"), list):
            result = [str(x) for x in data["checkpoints"]]
        else:
            raise ComfyUiError("Unexpected checkpoints response from ComfyUI")
        
        # Cache the result
        self._cache[cache_key] = (result, now)
        return result

    def list_samplers(self) -> list[str]:
        """
        List available samplers in ComfyUI (cached for 60 seconds).

        Returns:
            List of sampler names.

        Raises:
            ComfyUiError: If unable to reach ComfyUI or if the request fails.
        """
        cache_key = "samplers"
        now = time.time()
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if now - cached_time < self._cache_ttl:
                return cached_data
        
        url = f"{self.base_url}/samplers"
        try:
            r = self._client.get(url, timeout=20)
        except httpx.RequestError as exc:
            raise ComfyUiError(f"Unable to reach ComfyUI at {self.base_url}") from exc
        if r.status_code != 200:
            raise ComfyUiError(f"ComfyUI /samplers failed: {r.status_code} {r.text}")
        data = r.json()
        if isinstance(data, list):
            result = [str(x) for x in data]
        else:
            raise ComfyUiError("Unexpected samplers response from ComfyUI")
        
        # Cache the result
        self._cache[cache_key] = (result, now)
        return result

    def list_schedulers(self) -> list[str]:
        """
        List available schedulers in ComfyUI (cached for 60 seconds).

        Returns:
            List of scheduler names.

        Raises:
            ComfyUiError: If unable to reach ComfyUI or if the request fails.
        """
        cache_key = "schedulers"
        now = time.time()
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if now - cached_time < self._cache_ttl:
                return cached_data
        
        url = f"{self.base_url}/schedulers"
        try:
            r = self._client.get(url, timeout=20)
        except httpx.RequestError as exc:
            raise ComfyUiError(f"Unable to reach ComfyUI at {self.base_url}") from exc
        if r.status_code != 200:
            raise ComfyUiError(f"ComfyUI /schedulers failed: {r.status_code} {r.text}")
        data = r.json()
        if isinstance(data, list):
            result = [str(x) for x in data]
        else:
            raise ComfyUiError("Unexpected schedulers response from ComfyUI")
        
        # Cache the result
        self._cache[cache_key] = (result, now)
        return result

    def interrupt(self) -> None:
        """Best-effort interrupt of current ComfyUI processing (global)."""
        url = f"{self.base_url}/interrupt"
        try:
            r = self._client.post(url, timeout=10)
        except httpx.RequestError as exc:
            raise ComfyUiError(f"Unable to reach ComfyUI at {self.base_url}") from exc
        if r.status_code != 200:
            raise ComfyUiError(f"ComfyUI /interrupt failed: {r.status_code} {r.text}")
    
    def close(self) -> None:
        """Close the HTTP client and release resources."""
        if hasattr(self, "_client"):
            self._client.close()
    
    def __enter__(self) -> "ComfyUiClient":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
