from __future__ import annotations

import hashlib
import threading
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from app.core.logging import get_logger
from app.core.paths import data_dir

logger = get_logger(__name__)

ModelType = Literal["checkpoint", "lora", "embedding", "controlnet", "other"]


@dataclass(frozen=True)
class CatalogModel:
    id: str
    name: str
    type: ModelType
    url: str
    filename: str
    size_mb: int | None = None
    sha256: str | None = None
    notes: str | None = None


@dataclass
class DownloadStatus:
    state: Literal["idle", "downloading", "failed", "completed"] = "idle"
    model_id: str | None = None
    filename: str | None = None
    bytes_total: int | None = None
    bytes_downloaded: int = 0
    started_at: float | None = None
    finished_at: float | None = None
    error: str | None = None


class ModelManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._download = DownloadStatus()

        self._models_root = data_dir() / "models"
        self._models_root.mkdir(parents=True, exist_ok=True)

        # MVP catalog: small + safe placeholder. Users can replace URLs later.
        # Note: we intentionally do NOT bundle any proprietary models.
        self._catalog: list[CatalogModel] = [
            CatalogModel(
                id="sdxl-base-1.0",
                name="SDXL Base 1.0 (placeholder link)",
                type="checkpoint",
                url="https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors",
                filename="sd_xl_base_1.0.safetensors",
                notes="Large download. Replace with your preferred model sources.",
            ),
        ]

    def catalog(self) -> list[dict[str, Any]]:
        return [c.__dict__ for c in self._catalog]

    def installed(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for p in sorted(self._models_root.rglob("*")):
            if p.is_file():
                out.append(
                    {
                        "path": str(p.relative_to(self._models_root)),
                        "size_bytes": p.stat().st_size,
                        "mtime": p.stat().st_mtime,
                    }
                )
        return out

    def download_status(self) -> dict[str, Any]:
        with self._lock:
            return self._download.__dict__.copy()

    def start_download(self, model_id: str) -> None:
        with self._lock:
            if self._download.state == "downloading":
                return

            model = next((m for m in self._catalog if m.id == model_id), None)
            if not model:
                raise ValueError("Unknown model id")

            self._download = DownloadStatus(
                state="downloading",
                model_id=model.id,
                filename=model.filename,
                bytes_total=None,
                bytes_downloaded=0,
                started_at=time.time(),
            )

        t = threading.Thread(target=self._download_thread, args=(model,), name="model-download", daemon=True)
        t.start()

    def _download_thread(self, model: CatalogModel) -> None:
        dest = self._models_root / model.type / model.filename
        dest.parent.mkdir(parents=True, exist_ok=True)

        tmp = dest.with_suffix(dest.suffix + ".part")
        try:
            logger.info("Downloading model", extra={"model_id": model.id, "url": model.url, "dest": str(dest)})

            req = urllib.request.Request(model.url, headers={"User-Agent": "AInfluencer/0.1"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                total = resp.headers.get("Content-Length")
                total_int = int(total) if total and total.isdigit() else None
                with self._lock:
                    self._download.bytes_total = total_int

                h = hashlib.sha256()
                downloaded = 0
                with open(tmp, "wb") as f:
                    while True:
                        chunk = resp.read(1024 * 256)
                        if not chunk:
                            break
                        f.write(chunk)
                        h.update(chunk)
                        downloaded += len(chunk)
                        with self._lock:
                            self._download.bytes_downloaded = downloaded

            sha = h.hexdigest()
            if model.sha256 and sha.lower() != model.sha256.lower():
                raise RuntimeError("Checksum mismatch")

            tmp.replace(dest)
            with self._lock:
                self._download.state = "completed"
                self._download.finished_at = time.time()

            logger.info("Model download complete", extra={"model_id": model.id, "sha256": sha})
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self._download.state = "failed"
                self._download.error = str(exc)
                self._download.finished_at = time.time()
            try:
                if tmp.exists():
                    tmp.unlink()
            except Exception:  # noqa: BLE001
                pass
            logger.error("Model download failed", extra={"model_id": model.id, "error": str(exc)})


model_manager = ModelManager()
