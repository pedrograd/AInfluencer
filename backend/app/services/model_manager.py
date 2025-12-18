"""AI model catalog management, download queue, and installation tracking."""

from __future__ import annotations

import collections
import hashlib
import json
import shutil
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
    """AI model catalog entry.
    
    Attributes:
        id: Unique model identifier.
        name: Human-readable model name.
        type: Model type (checkpoint, lora, vae, etc.).
        tier: Model quality tier (1=best, 3=standard, 5=basic).
        tags: List of tags for filtering and categorization.
        url: Download URL for the model file.
        filename: Expected filename after download.
        size_mb: Model file size in megabytes, None if unknown.
        sha256: SHA256 checksum for verification, None if not available.
        notes: Additional notes or description about the model.
    """
    id: str
    name: str
    type: ModelType
    url: str
    filename: str
    tier: int = 3
    tags: list[str] | None = None
    size_mb: int | None = None
    sha256: str | None = None
    notes: str | None = None


@dataclass
class DownloadItem:
    """Model download job information.
    
    Attributes:
        id: Unique download job identifier.
        model_id: ID of the model being downloaded (references CatalogModel).
        filename: Filename of the model file being downloaded.
        state: Current download state (queued, downloading, cancelled, failed, completed).
        bytes_total: Total size of the file in bytes, None if unknown.
        bytes_downloaded: Number of bytes downloaded so far.
        created_at: Timestamp when download was queued (Unix timestamp).
        started_at: Timestamp when download started (Unix timestamp), None if not started.
        finished_at: Timestamp when download finished (Unix timestamp), None if not finished.
        error: Error message if download failed, None otherwise.
        cancel_requested: Whether cancellation has been requested for this download.
    """
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
    """Manages AI model catalog, downloads, and installation."""

    def __init__(self) -> None:
        """Initialize model manager with thread lock and download queue."""
        self._lock = threading.Lock()
        self._cv = threading.Condition(self._lock)
        self._queue: collections.deque[str] = collections.deque()
        self._items: dict[str, DownloadItem] = {}
        self._active_id: str | None = None

        self._models_root = data_dir() / "models"
        self._models_root.mkdir(parents=True, exist_ok=True)

        self._custom_catalog_path = config_dir() / "custom_models.json"
        config_dir().mkdir(parents=True, exist_ok=True)

        # Minimal curated catalog: publicly available, legally redistributable models
        # All models are from HuggingFace (public repositories) or other open sources
        self._built_in_catalog: list[CatalogModel] = [
            # SDXL Base and Refiner (Stability AI - publicly available)
            CatalogModel(
                id="sdxl-base-1.0",
                name="SDXL Base 1.0",
                type="checkpoint",
                tier=1,
                tags=["sdxl", "base", "photoreal"],
                url="https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors",
                filename="sd_xl_base_1.0.safetensors",
                size_mb=6939,  # ~6.9 GB
                notes="Stability AI SDXL base model. High quality, versatile. Recommended for most use cases.",
            ),
            CatalogModel(
                id="sdxl-refiner-1.0",
                name="SDXL Refiner 1.0",
                type="checkpoint",
                tier=2,
                tags=["sdxl", "refiner", "photoreal"],
                url="https://huggingface.co/stabilityai/stable-diffusion-xl-refiner-1.0/resolve/main/sd_xl_refiner_1.0.safetensors",
                filename="sd_xl_refiner_1.0.safetensors",
                size_mb=6939,  # ~6.9 GB
                notes="SDXL refiner model. Use after base model for enhanced detail and quality.",
            ),
            # Essential ControlNet models (publicly available)
            CatalogModel(
                id="controlnet-canny-sdxl",
                name="ControlNet Canny (SDXL)",
                type="controlnet",
                tier=1,
                tags=["controlnet", "canny", "sdxl", "edge-detection"],
                url="https://huggingface.co/xinsir/controlnet-canny-sdxl-1.0/resolve/main/diffusion_pytorch_model.safetensors",
                filename="controlnet-canny-sdxl.safetensors",
                size_mb=1024,  # ~1 GB
                notes="ControlNet for edge detection. Essential for structure-guided generation.",
            ),
            CatalogModel(
                id="controlnet-depth-sdxl",
                name="ControlNet Depth (SDXL)",
                type="controlnet",
                tier=1,
                tags=["controlnet", "depth", "sdxl"],
                url="https://huggingface.co/xinsir/controlnet-depth-sdxl-1.0/resolve/main/diffusion_pytorch_model.safetensors",
                filename="controlnet-depth-sdxl.safetensors",
                size_mb=1024,  # ~1 GB
                notes="ControlNet for depth maps. Great for 3D-aware generation.",
            ),
            CatalogModel(
                id="controlnet-openpose-sdxl",
                name="ControlNet OpenPose (SDXL)",
                type="controlnet",
                tier=2,
                tags=["controlnet", "openpose", "sdxl", "pose"],
                url="https://huggingface.co/xinsir/controlnet-openpose-sdxl-1.0/resolve/main/diffusion_pytorch_model.safetensors",
                filename="controlnet-openpose-sdxl.safetensors",
                size_mb=1024,  # ~1 GB
                notes="ControlNet for pose control. Useful for character consistency.",
            ),
            CatalogModel(
                id="controlnet-lineart-sdxl",
                name="ControlNet LineArt (SDXL)",
                type="controlnet",
                tier=2,
                tags=["controlnet", "lineart", "sdxl", "sketch"],
                url="https://huggingface.co/xinsir/controlnet-lineart-sdxl-1.0/resolve/main/diffusion_pytorch_model.safetensors",
                filename="controlnet-lineart-sdxl.safetensors",
                size_mb=1024,  # ~1 GB
                notes="ControlNet for line art. Great for sketch-to-image workflows.",
            ),
            CatalogModel(
                id="controlnet-tile-sdxl",
                name="ControlNet Tile (SDXL)",
                type="controlnet",
                tier=3,
                tags=["controlnet", "tile", "sdxl", "upscale"],
                url="https://huggingface.co/xinsir/controlnet-tile-sdxl-1.0/resolve/main/diffusion_pytorch_model.safetensors",
                filename="controlnet-tile-sdxl.safetensors",
                size_mb=1024,  # ~1 GB
                notes="ControlNet for tile-based upscaling. Useful for high-resolution generation.",
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
        """
        Get only custom models from catalog.

        Returns:
            List of custom model dictionaries, sorted by tier and name.
        """
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
        """
        Add a custom model to the catalog.

        Args:
            name: Model name.
            model_type: Type of model (checkpoint, lora, vae, etc.).
            url: Download URL for the model.
            filename: Filename for the downloaded model.
            tier: Quality tier (1-5, default: 3).
            tags: Optional list of tags.
            sha256: Optional SHA256 hash for verification.
            notes: Optional notes about the model.

        Returns:
            Dictionary representation of the added model.

        Raises:
            ValueError: If validation fails (empty name, invalid URL, etc.).
        """
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

    def delete_custom_model(self, model_id: str) -> None:
        """
        Delete a custom model from the catalog.

        Args:
            model_id: Custom model ID to delete.

        Raises:
            ValueError: If model_id is not a custom model or not found.
        """
        if not model_id.startswith("custom-"):
            raise ValueError("Not a custom model id")
        with self._cv:
            before = len(self._custom_catalog)
            self._custom_catalog = [m for m in self._custom_catalog if m.id != model_id]
            if len(self._custom_catalog) == before:
                raise ValueError("Custom model not found")
            self._save_custom_catalog()

    def update_custom_model(
        self,
        model_id: str,
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
        """
        Update an existing custom model in the catalog.

        Args:
            model_id: Custom model ID to update.
            name: Model name.
            model_type: Type of model (checkpoint, lora, vae, etc.).
            url: Download URL for the model.
            filename: Filename for the downloaded model.
            tier: Quality tier (1-5, default: 3).
            tags: Optional list of tags.
            sha256: Optional SHA256 hash for verification.
            notes: Optional notes about the model.

        Returns:
            Dictionary representation of the updated model.

        Raises:
            ValueError: If validation fails or model not found.
        """
        if not model_id.startswith("custom-"):
            raise ValueError("Not a custom model id")
        if not name.strip():
            raise ValueError("name is required")
        if not url.startswith(("http://", "https://")):
            raise ValueError("url must be http(s)")
        safe_filename = Path(filename).name
        if not safe_filename:
            raise ValueError("filename is required")
        if tier < 1 or tier > 5:
            raise ValueError("tier must be between 1 and 5")

        updated = CatalogModel(
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
            found = False
            new_list: list[CatalogModel] = []
            for m in self._custom_catalog:
                if m.id == model_id:
                    new_list.append(updated)
                    found = True
                else:
                    new_list.append(m)
            if not found:
                raise ValueError("Custom model not found")
            self._custom_catalog = new_list
            self._save_custom_catalog()
        return updated.__dict__.copy()

    def _load_custom_catalog(self) -> list[CatalogModel]:
        """
        Load custom model catalog from disk.
        
        Reads JSON file and deserializes into CatalogModel objects.
        Returns empty list if file doesn't exist or parsing fails.
        
        Returns:
            List of CatalogModel objects from custom catalog file
        """
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
        """
        Save custom model catalog to disk.
        
        Serializes custom catalog models to JSON file with indentation.
        """
        data = [c.__dict__ for c in self._custom_catalog]
        self._custom_catalog_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def installed(self) -> list[dict[str, Any]]:
        """
        Get list of installed models in the models directory.

        Returns:
            List of dictionaries with path, size_bytes, and mtime for each model file.
        """
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
        Compute SHA256 hash of an installed model file.

        Args:
            rel_path: Path relative to models root directory.

        Returns:
            Dictionary with path, sha256 hash, and size_bytes.

        Raises:
            ValueError: If path is invalid or file not found.
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
        """
        Get list of queued download items.

        Returns:
            List of download item dictionaries in queue order.
        """
        with self._lock:
            return [self._items[item_id].__dict__.copy() for item_id in list(self._queue)]

    def active(self) -> dict[str, Any] | None:
        """
        Get currently active download item.

        Returns:
            Active download item dictionary, or None if no active download.
        """
        with self._lock:
            if not self._active_id:
                return None
            return self._items[self._active_id].__dict__.copy()

    def items(self) -> list[dict[str, Any]]:
        """
        Get all download items (queued, active, completed, failed).

        Returns:
            List of download item dictionaries, sorted by creation time (newest first).
        """
        with self._lock:
            # Return most recent first
            return [v.__dict__.copy() for v in sorted(self._items.values(), key=lambda x: x.created_at, reverse=True)]

    def enqueue_download(self, model_id: str) -> dict[str, Any]:
        """
        Enqueue a model for download.

        Args:
            model_id: Model ID from catalog to download.

        Returns:
            Dictionary representation of the download item.

        Raises:
            ValueError: If model_id is unknown, already installed, already downloading, or already queued.
        """
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
        """
        Cancel a download item.

        Args:
            item_id: Download item ID to cancel.

        Returns:
            Dictionary representation of the cancelled download item.

        Raises:
            ValueError: If download item not found or cannot be cancelled.
        """
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
        """
        Background worker thread loop for processing download queue.
        
        Continuously processes queued download items, updating state and
        handling errors. Runs until thread is terminated.
        """
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
                all_catalog = self._built_in_catalog + self._custom_catalog
                model = next((m for m in all_catalog if m.id == item.model_id), None)
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
        """
        Download a single model file from URL.
        
        Downloads model to temporary file, verifies SHA256 checksum if provided,
        and moves to final destination. Updates download item progress and state.
        Handles cancellation and errors.
        
        Args:
            item: Download item to process
            model: Catalog model metadata with URL and checksum
        
        Raises:
            RuntimeError: If download fails, checksum mismatch, insufficient disk space, or cancelled
        """
        dest = self._models_root / model.type / model.filename
        dest.parent.mkdir(parents=True, exist_ok=True)

        tmp = dest.with_suffix(dest.suffix + ".part")
        
        # Check if we can resume a partial download
        resume_from = 0
        h = hashlib.sha256()
        if tmp.exists():
            resume_from = tmp.stat().st_size
            logger.info("Resuming download", extra={"model_id": model.id, "resume_from": resume_from})
            # Read existing file to continue hash calculation
            with open(tmp, "rb") as existing:
                while True:
                    chunk = existing.read(1024 * 256)
                    if not chunk:
                        break
                    h.update(chunk)
        
        try:
            logger.info("Downloading model", extra={"model_id": model.id, "url": model.url, "dest": str(dest), "resume_from": resume_from})

            req = urllib.request.Request(model.url, headers={"User-Agent": "AInfluencer/0.1"})
            
            # Add Range header if resuming
            if resume_from > 0:
                req.add_header("Range", f"bytes={resume_from}-")
            
            with urllib.request.urlopen(req, timeout=60) as resp:
                # Handle 206 Partial Content for resume, or 200 OK for fresh download
                status = resp.getcode()
                if status == 206:  # Partial Content (resume)
                    total_header = resp.headers.get("Content-Range")
                    if total_header:
                        # Content-Range: bytes 0-1023/1048576
                        total_match = total_header.split("/")
                        if len(total_match) == 2:
                            total_int = int(total_match[1])
                        else:
                            total_int = None
                    else:
                        total_int = None
                    # Total size is resume_from + content_length
                    content_length = resp.headers.get("Content-Length")
                    if content_length and content_length.isdigit():
                        total_int = resume_from + int(content_length)
                elif status == 200:  # Full download
                    total = resp.headers.get("Content-Length")
                    total_int = int(total) if total and total.isdigit() else None
                else:
                    total_int = None
                
                with self._cv:
                    item.bytes_total = total_int
                    if resume_from > 0:
                        item.bytes_downloaded = resume_from

                # Preflight: if we know size, ensure we have enough free disk (plus 1GB buffer).
                if total_int is not None:
                    free = shutil.disk_usage(self._models_root).free
                    buffer_bytes = 1024**3
                    if free < total_int + buffer_bytes:
                        raise RuntimeError(
                            f"Insufficient disk space (need ~{round((total_int + buffer_bytes)/(1024**3),2)} GB free)."
                        )

                downloaded = resume_from
                # Open in append mode if resuming, write mode if fresh
                mode = "ab" if resume_from > 0 else "wb"
                with open(tmp, mode) as f:
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
