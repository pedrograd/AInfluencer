"""Image storage and management service."""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.core.paths import images_dir
from app.services.image_metadata_service import ImageMetadataService

logger = get_logger(__name__)


class ImageStorageService:
    """Service for managing image file storage and metadata."""

    def __init__(self) -> None:
        """Initialize storage directories and helpers."""
        self._root = images_dir()
        self._root.mkdir(parents=True, exist_ok=True)
        self._metadata_service = ImageMetadataService()

    def resolve_path(self, filename: str) -> Path:
        """Resolve an image filename to an absolute path within storage."""
        return self._root / Path(filename).name

    def save_image_bytes(
        self,
        data: bytes,
        *,
        filename: str | None = None,
        generation_params: dict[str, Any] | None = None,
        quality_metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Persist an image buffer to disk with optional metadata extraction.

        Args:
            data: Raw image bytes to store.
            filename: Optional filename to use; defaults to timestamp+uuid.png.
            generation_params: Optional generation parameters to persist as metadata.
            quality_metrics: Optional quality metrics to persist as metadata.

        Returns:
            Dict containing path, url, and optional metadata dictionary.
        """
        safe_name = Path(filename).name if filename else f"{int(time.time())}-{uuid.uuid4().hex}.png"
        if "." not in safe_name:
            safe_name = f"{safe_name}.png"

        dest = self.resolve_path(safe_name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)

        metadata = self._write_metadata(
            dest,
            generation_params=generation_params,
            quality_metrics=quality_metrics,
        )

        return {
            "path": dest.name,
            "url": f"/content/images/{dest.name}",
            "metadata": metadata,
        }

    def upsert_metadata(
        self,
        filename: str,
        *,
        generation_params: dict[str, Any] | None = None,
        quality_metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Re-extract and persist metadata for an existing image."""
        path = self.resolve_path(filename)
        if not path.exists():
            return None
        return self._write_metadata(path, generation_params=generation_params, quality_metrics=quality_metrics)

    def get_metadata(self, filename: str) -> dict[str, Any] | None:
        """Return stored metadata for an image, if present."""
        metadata = self._metadata_service.get_metadata(filename)
        return asdict(metadata) if metadata else None

    def list_images(
        self,
        *,
        q: str | None = None,
        sort: str = "newest",
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List stored images with optional filtering and pagination."""
        query = (q or "").strip().lower()
        paths = [p for p in self._root.glob("*.png") if p.is_file()]
        if query:
            paths = [p for p in paths if query in p.name.lower()]

        if sort == "oldest":
            paths.sort(key=lambda x: x.stat().st_mtime)
        elif sort == "name":
            paths.sort(key=lambda x: x.name.lower())
        else:
            paths.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        if offset < 0:
            offset = 0
        if limit < 1:
            limit = 1
        page = paths[offset : offset + limit]

        items: list[dict[str, Any]] = []
        for p in page:
            try:
                st = p.stat()
                metadata = self.get_metadata(p.name)
                items.append(
                    {
                        "path": p.name,
                        "mtime": st.st_mtime,
                        "size_bytes": st.st_size,
                        "url": f"/content/images/{p.name}",
                        "metadata": metadata,
                    }
                )
            except FileNotFoundError:
                continue

        return {"items": items, "total": len(paths), "limit": limit, "offset": offset, "sort": sort, "q": query}

    def storage_stats(self) -> dict[str, Any]:
        """Return storage statistics for stored images."""
        total = 0
        count = 0
        for p in self._root.glob("*.png"):
            try:
                st = p.stat()
            except FileNotFoundError:
                continue
            total += st.st_size
            count += 1
        return {"images_count": count, "images_bytes": total}

    def delete_image(self, filename: str) -> bool:
        """Delete a single image and its metadata."""
        if "/" in filename or "\\" in filename or ".." in filename:
            logger.warning("Invalid filename for deletion: %s", filename)
            return False

        path = self.resolve_path(filename)
        metadata_path = self._metadata_path_for(filename)

        if not path.exists():
            return False

        try:
            path.unlink()
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to delete image %s: %s", filename, exc)
            return False

        try:
            if metadata_path.exists():
                metadata_path.unlink()
        except Exception:
            # Metadata cleanup best-effort
            pass

        return True

    def bulk_delete_images(self, filenames: list[str]) -> dict[str, int]:
        """Delete multiple images safely."""
        deleted = 0
        skipped = 0
        for name in filenames:
            if self.delete_image(name):
                deleted += 1
            else:
                skipped += 1
        return {"deleted": deleted, "skipped": skipped, "total_requested": len(filenames)}

    def cleanup_old_images(self, older_than_days: int = 30) -> dict[str, Any]:
        """Delete images older than a threshold (in days)."""
        import time

        cutoff = time.time() - (older_than_days * 86400)
        deleted = 0
        skipped = 0

        for p in self._root.glob("*.png"):
            try:
                if p.stat().st_mtime < cutoff:
                    if self.delete_image(p.name):
                        deleted += 1
                    else:
                        skipped += 1
            except FileNotFoundError:
                skipped += 1
            except Exception:
                skipped += 1

        return {"deleted": deleted, "skipped": skipped, "older_than_days": older_than_days}

    def _metadata_path_for(self, filename: str) -> Path:
        """Get the metadata path for a given filename."""
        stem = Path(filename).stem
        return self._root / ".metadata" / f"{stem}.json"

    def _write_metadata(
        self,
        path: Path,
        *,
        generation_params: dict[str, Any] | None = None,
        quality_metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Extract metadata and persist it next to the image."""
        try:
            metadata = self._metadata_service.extract_metadata(
                path,
                generation_params=generation_params,
                quality_metrics=quality_metrics,
            )
            return asdict(metadata)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to extract image metadata for %s: %s", path.name, exc)
            return None


image_storage_service = ImageStorageService()

