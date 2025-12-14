from __future__ import annotations

import collections
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
class DownloadItem:
    id: str
    model_id: str
    filename: str
    state: Literal["queued", "downloading", "cancelled", "failed", "completed"] = "queued"
    bytes_total: int | None = None
    bytes_downloaded: int = 0
    created_at: float = 0.0
    started_at: float | None = None
    finished_at: float | None = None
    error: str | None = None
    cancel_requested: bool = False


class ModelManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cv = threading.Condition(self._lock)
        self._queue: collections.deque[str] = collections.deque()
        self._items: dict[str, DownloadItem] = {}
        self._active_id: str | None = None

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

        # Background worker processes the queue one item at a time.
        t = threading.Thread(target=self._worker_loop, name="model-manager-worker", daemon=True)
        t.start()

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

    def queue(self) -> list[dict[str, Any]]:
        with self._lock:
            return [self._items[item_id].__dict__.copy() for item_id in list(self._queue)]

    def active(self) -> dict[str, Any] | None:
        with self._lock:
            if not self._active_id:
                return None
            return self._items[self._active_id].__dict__.copy()

    def items(self) -> list[dict[str, Any]]:
        with self._lock:
            # Return most recent first
            return [v.__dict__.copy() for v in sorted(self._items.values(), key=lambda x: x.created_at, reverse=True)]

    def enqueue_download(self, model_id: str) -> dict[str, Any]:
        model = next((m for m in self._catalog if m.id == model_id), None)
        if not model:
            raise ValueError("Unknown model id")

        item_id = f"{int(time.time() * 1000)}-{model.id}"
        item = DownloadItem(
            id=item_id,
            model_id=model.id,
            filename=model.filename,
            state="queued",
            bytes_total=None,
            bytes_downloaded=0,
            created_at=time.time(),
        )

        with self._cv:
            self._items[item_id] = item
            self._queue.append(item_id)
            self._cv.notify_all()

        return item.__dict__.copy()

    def cancel(self, item_id: str) -> dict[str, Any]:
        with self._cv:
            item = self._items.get(item_id)
            if not item:
                raise ValueError("Unknown download id")

            if item.state == "queued":
                # Remove from queue
                try:
                    self._queue.remove(item_id)
                except ValueError:
                    pass
                item.state = "cancelled"
                item.finished_at = time.time()
                return item.__dict__.copy()

            if item.state == "downloading":
                item.cancel_requested = True
                return item.__dict__.copy()

            return item.__dict__.copy()

    def _worker_loop(self) -> None:
        while True:
            with self._cv:
                while not self._queue:
                    self._cv.wait(timeout=1.0)
                item_id = self._queue.popleft()
                self._active_id = item_id
                item = self._items[item_id]
                item.state = "downloading"
                item.started_at = time.time()

            try:
                model = next((m for m in self._catalog if m.id == item.model_id), None)
                if not model:
                    raise RuntimeError("Catalog model missing")
                self._download_one(item, model)
            except Exception as exc:  # noqa: BLE001
                with self._cv:
                    item.state = "failed"
                    item.error = str(exc)
                    item.finished_at = time.time()
            finally:
                with self._cv:
                    self._active_id = None

    def _download_one(self, item: DownloadItem, model: CatalogModel) -> None:
        dest = self._models_root / model.type / model.filename
        dest.parent.mkdir(parents=True, exist_ok=True)

        tmp = dest.with_suffix(dest.suffix + ".part")
        try:
            logger.info("Downloading model", extra={"model_id": model.id, "url": model.url, "dest": str(dest)})

            req = urllib.request.Request(model.url, headers={"User-Agent": "AInfluencer/0.1"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                total = resp.headers.get("Content-Length")
                total_int = int(total) if total and total.isdigit() else None
                with self._cv:
                    item.bytes_total = total_int

                h = hashlib.sha256()
                downloaded = 0
                with open(tmp, "wb") as f:
                    while True:
                        with self._cv:
                            if item.cancel_requested:
                                raise RuntimeError("Cancelled")
                        chunk = resp.read(1024 * 256)
                        if not chunk:
                            break
                        f.write(chunk)
                        h.update(chunk)
                        downloaded += len(chunk)
                        with self._cv:
                            item.bytes_downloaded = downloaded

            sha = h.hexdigest()
            if model.sha256 and sha.lower() != model.sha256.lower():
                raise RuntimeError("Checksum mismatch")

            tmp.replace(dest)
            with self._cv:
                item.state = "completed"
                item.finished_at = time.time()

            logger.info("Model download complete", extra={"model_id": model.id, "sha256": sha})
        except Exception as exc:  # noqa: BLE001
            with self._cv:
                if str(exc) == "Cancelled":
                    item.state = "cancelled"
                    item.finished_at = time.time()
                else:
                    item.state = "failed"
                    item.error = str(exc)
                    item.finished_at = time.time()
            try:
                if tmp.exists():
                    tmp.unlink()
            except Exception:  # noqa: BLE001
                pass
            if str(exc) == "Cancelled":
                logger.info("Model download cancelled", extra={"model_id": model.id})
            else:
                logger.error("Model download failed", extra={"model_id": model.id, "error": str(exc)})


model_manager = ModelManager()
