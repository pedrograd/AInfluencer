from __future__ import annotations

import collections
import hashlib
import json
import threading
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from app.core.logging import get_logger
from app.core.paths import config_dir, data_dir

logger = get_logger(__name__)

ModelType = Literal["checkpoint", "lora", "embedding", "controlnet", "other"]


@dataclass(frozen=True)
class CatalogModel:
    id: str
    name: str
    type: ModelType
    tier: int = 3
    tags: list[str] | None = None
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

        self._custom_catalog_path = config_dir() / "custom_models.json"
        config_dir().mkdir(parents=True, exist_ok=True)

        # MVP catalog: small + safe placeholder. Users can replace URLs later.
        # Note: we intentionally do NOT bundle any proprietary models.
        self._built_in_catalog: list[CatalogModel] = [
            CatalogModel(
                id="sdxl-base-1.0",
                name="SDXL Base 1.0 (placeholder link)",
                type="checkpoint",
                tier=2,
                tags=["sdxl", "base"],
                url="https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors",
                filename="sd_xl_base_1.0.safetensors",
                notes="Large download. Replace with your preferred model sources.",
            ),
        ]
        self._custom_catalog: list[CatalogModel] = self._load_custom_catalog()

        # Background worker processes the queue one item at a time.
        t = threading.Thread(target=self._worker_loop, name="model-manager-worker", daemon=True)
        t.start()

    def catalog(self) -> list[dict[str, Any]]:
        # Built-in first (sorted by tier), then custom.
        built_in = sorted(self._built_in_catalog, key=lambda x: (x.tier, x.name.lower()))
        custom = sorted(self._custom_catalog, key=lambda x: (x.tier, x.name.lower()))
        return [c.__dict__ for c in (built_in + custom)]

    def custom_catalog(self) -> list[dict[str, Any]]:
        return [c.__dict__ for c in sorted(self._custom_catalog, key=lambda x: (x.tier, x.name.lower()))]

    def add_custom_model(
        self,
        *,
        name: str,
        model_type: ModelType,
        url: str,
        filename: str,
        tier: int = 3,
        tags: list[str] | None = None,
        sha256: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        # Very light validation (MVP)
        if not name.strip():
            raise ValueError("name is required")
        if not url.startswith(("http://", "https://")):
            raise ValueError("url must be http(s)")
        safe_filename = Path(filename).name
        if not safe_filename:
            raise ValueError("filename is required")
        if tier < 1 or tier > 5:
            raise ValueError("tier must be between 1 and 5")

        model_id = f"custom-{int(time.time() * 1000)}"
        m = CatalogModel(
            id=model_id,
            name=name.strip(),
            type=model_type,
            tier=tier,
            tags=tags,
            url=url.strip(),
            filename=safe_filename,
            sha256=sha256.strip() if sha256 else None,
            notes=notes.strip() if notes else None,
        )

        with self._cv:
            self._custom_catalog.append(m)
            self._save_custom_catalog()
        return m.__dict__.copy()

    def _load_custom_catalog(self) -> list[CatalogModel]:
        try:
            if not self._custom_catalog_path.exists():
                return []
            raw = json.loads(self._custom_catalog_path.read_text(encoding="utf-8"))
            if not isinstance(raw, list):
                return []
            out: list[CatalogModel] = []
            for item in raw:
                if not isinstance(item, dict):
                    continue
                try:
                    out.append(
                        CatalogModel(
                            id=str(item.get("id")),
                            name=str(item.get("name")),
                            type=item.get("type") or "other",  # type: ignore[arg-type]
                            tier=int(item.get("tier") or 3),
                            tags=item.get("tags"),
                            url=str(item.get("url")),
                            filename=str(item.get("filename")),
                            size_mb=item.get("size_mb"),
                            sha256=item.get("sha256"),
                            notes=item.get("notes"),
                        )
                    )
                except Exception:  # noqa: BLE001
                    continue
            return out
        except Exception:  # noqa: BLE001
            return []

    def _save_custom_catalog(self) -> None:
        data = [c.__dict__ for c in self._custom_catalog]
        self._custom_catalog_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

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

    def import_file(self, filename: str, content: bytes, model_type: ModelType = "other") -> dict[str, Any]:
        """
        Import a model file into the shared models directory.
        MVP: store as-is; later we can auto-detect type and extract metadata.
        """
        safe_name = Path(filename).name
        target_dir = self._models_root / model_type
        target_dir.mkdir(parents=True, exist_ok=True)

        dest = target_dir / safe_name
        if dest.exists():
            # Avoid overwriting: add timestamp suffix
            stem = dest.stem
            suffix = dest.suffix
            dest = target_dir / f"{stem}-{int(time.time())}{suffix}"

        dest.write_bytes(content)
        return {
            "path": str(dest.relative_to(self._models_root)),
            "size_bytes": dest.stat().st_size,
            "mtime": dest.stat().st_mtime,
        }

    def verify_sha256(self, rel_path: str) -> dict[str, Any]:
        """
        Compute sha256 of an installed file (path relative to models root).
        """
        p = (self._models_root / rel_path).resolve()
        if self._models_root not in p.parents and p != self._models_root:
            raise ValueError("Invalid path")
        if not p.exists() or not p.is_file():
            raise ValueError("File not found")

        h = hashlib.sha256()
        with open(p, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                h.update(chunk)

        return {"path": rel_path, "sha256": h.hexdigest(), "size_bytes": p.stat().st_size}

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
        all_catalog = self._built_in_catalog + self._custom_catalog
        model = next((m for m in all_catalog if m.id == model_id), None)
        if not model:
            raise ValueError("Unknown model id")

        # Don't enqueue if already installed (based on catalog path).
        expected = self._models_root / model.type / model.filename
        if expected.exists():
            raise ValueError("Model already installed")

        with self._cv:
            # Don't enqueue duplicates if already queued or active.
            if self._active_id:
                active = self._items.get(self._active_id)
                if active and active.model_id == model_id and active.state in {"downloading"}:
                    raise ValueError("Model already downloading")
            for qid in self._queue:
                qi = self._items.get(qid)
                if qi and qi.model_id == model_id and qi.state == "queued":
                    raise ValueError("Model already queued")

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
