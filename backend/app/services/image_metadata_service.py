"""Image metadata extraction and storage service.

This module provides functionality to extract and store image metadata including:
- EXIF data
- Generation parameters
- Quality metrics
- File information
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.core.paths import images_dir

logger = get_logger(__name__)


@dataclass
class ImageMetadata:
    """Image metadata structure."""
    
    file_path: str
    file_size_bytes: int
    width: int
    height: int
    format: str
    mode: str
    created_at: str
    generation_params: dict[str, Any] | None = None
    quality_metrics: dict[str, Any] | None = None
    exif_data: dict[str, Any] | None = None


class ImageMetadataService:
    """Service for extracting and storing image metadata."""
    
    def __init__(self) -> None:
        """Initialize metadata service."""
        self._metadata_dir = images_dir() / ".metadata"
        self._metadata_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_metadata(
        self,
        image_path: str | Path,
        generation_params: dict[str, Any] | None = None,
        quality_metrics: dict[str, Any] | None = None,
    ) -> ImageMetadata:
        """
        Extract metadata from an image file.
        
        Args:
            image_path: Path to the image file
            generation_params: Optional generation parameters to store
            quality_metrics: Optional quality validation metrics to store
            
        Returns:
            ImageMetadata object with extracted information
        """
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
        except ImportError:
            raise ImportError("PIL/Pillow is required for metadata extraction")
        
        image_path_obj = Path(image_path)
        if not image_path_obj.is_absolute():
            image_path_obj = images_dir() / image_path
        
        if not image_path_obj.exists():
            raise FileNotFoundError(f"Image not found: {image_path_obj}")
        
        # Get file stats
        stat = image_path_obj.stat()
        file_size = stat.st_size
        created_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        # Load image and extract basic info
        with Image.open(image_path_obj) as img:
            width, height = img.size
            format_name = img.format or "UNKNOWN"
            mode = img.mode
        
        # Extract EXIF data
        exif_data = None
        try:
            with Image.open(image_path_obj) as img:
                exif = img.getexif()
                if exif:
                    exif_dict = {}
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        exif_dict[str(tag)] = str(value)
                    exif_data = exif_dict if exif_dict else None
        except Exception as e:
            logger.warning(f"Failed to extract EXIF data: {e}")
            exif_data = None
        
        metadata = ImageMetadata(
            file_path=str(image_path_obj.relative_to(images_dir())),
            file_size_bytes=file_size,
            width=width,
            height=height,
            format=format_name,
            mode=mode,
            created_at=created_at,
            generation_params=generation_params,
            quality_metrics=quality_metrics,
            exif_data=exif_data,
        )
        
        # Save metadata to disk
        self._save_metadata(metadata)
        
        return metadata
    
    def get_metadata(self, image_path: str | Path) -> ImageMetadata | None:
        """
        Retrieve stored metadata for an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            ImageMetadata if found, None otherwise
        """
        image_path_obj = Path(image_path)
        if not image_path_obj.is_absolute():
            image_path_obj = images_dir() / image_path
        
        metadata_file = self._get_metadata_file_path(image_path_obj)
        
        if not metadata_file.exists():
            return None
        
        try:
            data = json.loads(metadata_file.read_text(encoding="utf-8"))
            return ImageMetadata(**data)
        except Exception as e:
            logger.warning(f"Failed to load metadata: {e}")
            return None
    
    def _save_metadata(self, metadata: ImageMetadata) -> None:
        """Save metadata to disk."""
        image_path_obj = images_dir() / metadata.file_path
        metadata_file = self._get_metadata_file_path(image_path_obj)
        
        try:
            metadata_dict = asdict(metadata)
            metadata_file.write_text(
                json.dumps(metadata_dict, indent=2, default=str),
                encoding="utf-8",
            )
            logger.debug(f"Saved metadata: {metadata_file}")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def _get_metadata_file_path(self, image_path: Path) -> Path:
        """Get metadata file path for an image."""
        # Store metadata in .metadata directory with same structure
        relative_path = image_path.relative_to(images_dir())
        metadata_file = self._metadata_dir / f"{relative_path.stem}.json"
        return metadata_file

