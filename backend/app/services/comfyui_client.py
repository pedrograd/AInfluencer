from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import httpx

from app.core.config import settings


class ComfyUiError(RuntimeError):
    pass


class ComfyUiClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.comfyui_base_url).rstrip("/")

    def queue_prompt(self, workflow: dict[str, Any]) -> str:
        url = f"{self.base_url}/prompt"
        with httpx.Client(timeout=30) as client:
            try:
                r = client.post(url, json={"prompt": workflow})
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
        with httpx.Client(timeout=15) as client:
            while time.time() < deadline:
                if should_cancel and should_cancel():
                    raise ComfyUiError("Cancelled")
                try:
                    r = client.get(url)
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
                time.sleep(1.0)

        raise ComfyUiError("Timed out waiting for ComfyUI output")

    def download_image_bytes(self, filename: str, subfolder: str = "", image_type: str = "output") -> bytes:
        url = f"{self.base_url}/view"
        params = {"filename": filename, "subfolder": subfolder, "type": image_type}
        with httpx.Client(timeout=60) as client:
            try:
                r = client.get(url, params=params)
            except httpx.RequestError as exc:
                raise ComfyUiError(f"Unable to reach ComfyUI at {self.base_url}") from exc
            if r.status_code != 200:
                raise ComfyUiError(f"ComfyUI /view failed: {r.status_code} {r.text}")
            return r.content

    def get_system_stats(self) -> dict[str, Any]:
        url = f"{self.base_url}/system_stats"
        with httpx.Client(timeout=10) as client:
            try:
                r = client.get(url)
            except httpx.RequestError as exc:
                raise ComfyUiError(f"Unable to reach ComfyUI at {self.base_url}") from exc
            if r.status_code != 200:
                raise ComfyUiError(f"ComfyUI /system_stats failed: {r.status_code} {r.text}")
            data = r.json()
            return data if isinstance(data, dict) else {"raw": data}

    def list_checkpoints(self) -> list[str]:
        url = f"{self.base_url}/models/checkpoints"
        with httpx.Client(timeout=20) as client:
            try:
                r = client.get(url)
            except httpx.RequestError as exc:
                raise ComfyUiError(f"Unable to reach ComfyUI at {self.base_url}") from exc
            if r.status_code != 200:
                raise ComfyUiError(f"ComfyUI /models/checkpoints failed: {r.status_code} {r.text}")
            data = r.json()
            if isinstance(data, list):
                return [str(x) for x in data]
            # Some versions may return {"checkpoints":[...]}
            if isinstance(data, dict) and isinstance(data.get("checkpoints"), list):
                return [str(x) for x in data["checkpoints"]]
            raise ComfyUiError("Unexpected checkpoints response from ComfyUI")

    def interrupt(self) -> None:
        """Best-effort interrupt of current ComfyUI processing (global)."""
        url = f"{self.base_url}/interrupt"
        with httpx.Client(timeout=10) as client:
            try:
                r = client.post(url)
            except httpx.RequestError as exc:
                raise ComfyUiError(f"Unable to reach ComfyUI at {self.base_url}") from exc
            if r.status_code != 200:
                raise ComfyUiError(f"ComfyUI /interrupt failed: {r.status_code} {r.text}")
