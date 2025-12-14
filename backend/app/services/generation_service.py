from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any, Literal

from app.core.logging import get_logger
from app.core.paths import images_dir
from app.services.comfyui_client import ComfyUiClient, ComfyUiError

logger = get_logger(__name__)

JobState = Literal["queued", "running", "cancelled", "failed", "succeeded"]


@dataclass
class ImageJob:
    id: str
    state: JobState = "queued"
    message: str | None = None
    created_at: float = 0.0
    started_at: float | None = None
    finished_at: float | None = None
    cancelled_at: float | None = None
    image_path: str | None = None
    image_paths: list[str] | None = None
    error: str | None = None
    params: dict[str, Any] | None = None
    cancel_requested: bool = False


class GenerationService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, ImageJob] = {}
        images_dir().mkdir(parents=True, exist_ok=True)

    def create_image_job(
        self,
        *,
        prompt: str,
        negative_prompt: str | None = None,
        seed: int | None = None,
        checkpoint: str | None = None,
        width: int = 1024,
        height: int = 1024,
        steps: int = 25,
        cfg: float = 7.0,
        sampler_name: str = "euler",
        scheduler: str = "normal",
        batch_size: int = 1,
    ) -> ImageJob:
        job_id = str(uuid.uuid4())
        job = ImageJob(
            id=job_id,
            state="queued",
            created_at=time.time(),
            params={
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "seed": seed,
                "checkpoint": checkpoint,
                "width": width,
                "height": height,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": sampler_name,
                "scheduler": scheduler,
                "batch_size": batch_size,
            },
        )
        with self._lock:
            self._jobs[job_id] = job

        t = threading.Thread(
            target=self._run_image_job,
            args=(
                job_id,
                prompt,
                negative_prompt,
                seed,
                checkpoint,
                width,
                height,
                steps,
                cfg,
                sampler_name,
                scheduler,
                batch_size,
            ),
            name=f"image-job-{job_id}",
            daemon=True,
        )
        t.start()
        return job

    def get_job(self, job_id: str) -> ImageJob | None:
        with self._lock:
            j = self._jobs.get(job_id)
            return None if j is None else ImageJob(**j.__dict__)

    def list_jobs(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            jobs = list(self._jobs.values())
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return [j.__dict__ for j in jobs[:limit]]

    def request_cancel(self, job_id: str) -> bool:
        with self._lock:
            j = self._jobs.get(job_id)
            if not j:
                return False
            if j.state in ("failed", "succeeded", "cancelled"):
                return True
            j.cancel_requested = True
            j.message = "Cancelling…"
            return True

    def list_images(self, limit: int = 50) -> list[dict[str, Any]]:
        root = images_dir()
        items: list[dict[str, Any]] = []
        for p in sorted(root.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
            items.append(
                {
                    "path": p.name,
                    "mtime": p.stat().st_mtime,
                    "size_bytes": p.stat().st_size,
                    "url": f"/content/images/{p.name}",
                }
            )
        return items

    def _set_job(self, job_id: str, **kwargs: Any) -> None:
        with self._lock:
            j = self._jobs[job_id]
            for k, v in kwargs.items():
                setattr(j, k, v)

    def _is_cancel_requested(self, job_id: str) -> bool:
        with self._lock:
            j = self._jobs.get(job_id)
            return bool(j and j.cancel_requested)

    def _update_job_params(self, job_id: str, **updates: Any) -> None:
        with self._lock:
            j = self._jobs[job_id]
            if not isinstance(j.params, dict):
                j.params = {}
            j.params.update(updates)

    def _basic_sdxl_workflow(
        self,
        prompt: str,
        negative_prompt: str | None,
        seed: int | None,
        checkpoint: str,
        width: int,
        height: int,
        steps: int,
        cfg: float,
        sampler_name: str,
        scheduler: str,
        batch_size: int,
    ) -> dict[str, Any]:
        # Minimal ComfyUI workflow (SDXL checkpoint name must exist in ComfyUI).
        # Users can change the checkpoint inside ComfyUI; this is MVP only.
        seed_val = seed if seed is not None else 0
        neg = negative_prompt or ""
        return {
            "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": checkpoint}},
            "2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["1", 1]}},
            "3": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["1", 1]}},
            "4": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": width, "height": height, "batch_size": batch_size},
            },
            "5": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["4", 0],
                    "seed": seed_val,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": sampler_name,
                    "scheduler": scheduler,
                    "denoise": 1.0,
                },
            },
            "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
            "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": "ainfluencer"}},
        }

    def _run_image_job(
        self,
        job_id: str,
        prompt: str,
        negative_prompt: str | None,
        seed: int | None,
        checkpoint: str | None,
        width: int,
        height: int,
        steps: int,
        cfg: float,
        sampler_name: str,
        scheduler: str,
        batch_size: int,
    ) -> None:
        self._set_job(job_id, state="running", started_at=time.time(), message="Queued in ComfyUI")
        client = ComfyUiClient()

        try:
            # Early cancel (before any external calls)
            if self._is_cancel_requested(job_id):
                now = time.time()
                self._set_job(job_id, state="cancelled", finished_at=now, cancelled_at=now, message="Cancelled")
                return

            checkpoints = client.list_checkpoints()
            if not checkpoints:
                raise ComfyUiError("No checkpoints found in ComfyUI")
            ckpt = checkpoint or checkpoints[0]
            if ckpt not in checkpoints:
                raise ComfyUiError(f"Checkpoint not found in ComfyUI: {ckpt}")

            workflow = self._basic_sdxl_workflow(
                prompt,
                negative_prompt,
                seed,
                ckpt,
                width,
                height,
                steps,
                cfg,
                sampler_name,
                scheduler,
                batch_size,
            )
            prompt_id = client.queue_prompt(workflow)
            self._update_job_params(job_id, comfy_prompt_id=prompt_id)
            self._set_job(job_id, message=f"ComfyUI prompt_id={prompt_id}")

            def _should_cancel() -> bool:
                return self._is_cancel_requested(job_id)

            outs = client.wait_for_images(prompt_id, timeout_s=600, should_cancel=_should_cancel)
            saved: list[str] = []
            for idx, out in enumerate(outs):
                filename = str(out.get("filename"))
                subfolder = str(out.get("subfolder") or "")
                image_type = str(out.get("type") or "output")
                data = client.download_image_bytes(filename=filename, subfolder=subfolder, image_type=image_type)
                out_name = f"{int(time.time())}-{job_id}-{idx}.png"
                dest = images_dir() / out_name
                dest.write_bytes(data)
                saved.append(out_name)

            self._set_job(
                job_id,
                state="succeeded",
                finished_at=time.time(),
                message="Done",
                image_path=saved[0] if saved else None,
                image_paths=saved,
            )
        except ComfyUiError as exc:
            if str(exc) == "Cancelled":
                try:
                    client.interrupt()
                except Exception:
                    pass
                self._set_job(
                    job_id,
                    state="cancelled",
                    finished_at=time.time(),
                    cancelled_at=time.time(),
                    message="Cancelled",
                    error=None,
                )
            else:
                self._set_job(job_id, state="failed", finished_at=time.time(), error=str(exc), message="ComfyUI error")
        except Exception as exc:  # noqa: BLE001
            logger.error("Image generation failed", extra={"error": str(exc)})
            self._set_job(job_id, state="failed", finished_at=time.time(), error=str(exc), message="Failed")


generation_service = GenerationService()
