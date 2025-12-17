"""Service for optimizing images for platform-specific requirements.

This service handles automatic resizing, format conversion, and compression
for different social media platforms to ensure optimal image quality and
compliance with platform requirements.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from app.core.logging import get_logger
from app.core.paths import images_dir

logger = get_logger(__name__)


class PlatformImageOptimizationError(RuntimeError):
    """Error raised when platform image optimization operations fail."""
    pass


class Platform(str, Enum):
    """Supported platforms for image optimization."""
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    TELEGRAM = "telegram"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    GENERIC = "generic"


class PlatformImageOptimizationService:
    """Service for optimizing images for platform-specific requirements."""

    # Platform-specific requirements
    PLATFORM_SPECS: dict[Platform, dict[str, Any]] = {
        Platform.INSTAGRAM: {
            "optimal_width": 1080,
            "optimal_height": 1080,
            "aspect_ratios": ["1:1", "4:5", "16:9"],  # Square, portrait, landscape
            "max_width": 1080,
            "max_height": 1350,
            "min_width": 320,
            "min_height": 320,
            "max_size_mb": 8,
            "format": "JPEG",
            "quality": 92,
        },
        Platform.TWITTER: {
            "optimal_width": 1200,
            "optimal_height": 675,
            "aspect_ratios": ["16:9", "1:1"],  # Landscape, square
            "max_width": 4096,
            "max_height": 4096,
            "min_width": 300,
            "min_height": 300,
            "max_size_mb": 5,
            "format": "JPEG",
            "quality": 85,
        },
        Platform.FACEBOOK: {
            "optimal_width": 1200,
            "optimal_height": 630,
            "aspect_ratios": ["1.91:1", "1:1"],  # Landscape, square
            "max_width": 2048,
            "max_height": 2048,
            "min_width": 600,
            "min_height": 315,
            "max_size_mb": 4,
            "format": "JPEG",
            "quality": 85,
        },
        Platform.TELEGRAM: {
            "optimal_width": 1280,
            "optimal_height": 1280,
            "aspect_ratios": ["1:1", "16:9", "4:3"],  # Flexible
            "max_width": 1280,
            "max_height": 1280,
            "min_width": 100,
            "min_height": 100,
            "max_size_mb": 10,
            "format": "JPEG",
            "quality": 90,
        },
        Platform.YOUTUBE: {
            "optimal_width": 1280,
            "optimal_height": 720,
            "aspect_ratios": ["16:9"],
            "max_width": 2560,
            "max_height": 1440,
            "min_width": 640,
            "min_height": 360,
            "max_size_mb": 2,
            "format": "JPEG",
            "quality": 90,
        },
        Platform.TIKTOK: {
            "optimal_width": 1080,
            "optimal_height": 1920,
            "aspect_ratios": ["9:16"],  # Vertical
            "max_width": 1080,
            "max_height": 1920,
            "min_width": 540,
            "min_height": 960,
            "max_size_mb": 10,
            "format": "JPEG",
            "quality": 92,
        },
        Platform.GENERIC: {
            "optimal_width": 1920,
            "optimal_height": 1080,
            "aspect_ratios": ["16:9", "1:1", "4:3"],
            "max_width": 3840,
            "max_height": 2160,
            "min_width": 640,
            "min_height": 480,
            "max_size_mb": 10,
            "format": "JPEG",
            "quality": 90,
        },
    }

    def __init__(self) -> None:
        """Initialize the platform image optimization service."""
        if not PIL_AVAILABLE:
            logger.warning("PIL/Pillow not available - platform image optimization will be limited")

    def optimize_for_platform(
        self,
        image_path: str | Path,
        platform: Platform | str,
        output_path: str | Path | None = None,
        maintain_aspect_ratio: bool = True,
    ) -> Path:
        """
        Optimize an image for a specific platform.

        Args:
            image_path: Path to the source image file
            platform: Target platform (Platform enum or string)
            output_path: Path where optimized image should be saved (optional, auto-generated if None)
            maintain_aspect_ratio: Whether to maintain aspect ratio when resizing (default: True)

        Returns:
            Path to the optimized image file

        Raises:
            PlatformImageOptimizationError: If optimization fails
        """
        if not PIL_AVAILABLE:
            raise PlatformImageOptimizationError("PIL/Pillow is required for image optimization")

        # Convert string to Platform enum
        if isinstance(platform, str):
            try:
                platform = Platform(platform.lower())
            except ValueError:
                logger.warning(f"Unknown platform '{platform}', using GENERIC")
                platform = Platform.GENERIC

        # Get platform specs
        specs = self.PLATFORM_SPECS[platform]

        # Resolve paths
        image_path_obj = Path(image_path)
        if not image_path_obj.is_absolute():
            image_path_obj = images_dir() / image_path

        if not image_path_obj.exists():
            raise PlatformImageOptimizationError(f"Image file not found: {image_path_obj}")

        # Determine output path
        if output_path is None:
            opt_dir = images_dir() / "optimized"
            opt_dir.mkdir(parents=True, exist_ok=True)
            stem = image_path_obj.stem
            suffix = f".{specs['format'].lower()}"
            output_path = opt_dir / f"{stem}_{platform.value}{suffix}"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Open image
            img = Image.open(image_path_obj)

            # Convert to RGB if necessary (for JPEG output)
            if specs["format"] == "JPEG" and img.mode in ("RGBA", "LA", "P"):
                # Create white background for transparent images
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                if img.mode in ("RGBA", "LA"):
                    rgb_img.paste(img, mask=img.split()[-1])
                img = rgb_img
            elif img.mode != "RGB" and specs["format"] == "JPEG":
                img = img.convert("RGB")

            # Get current dimensions
            current_width, current_height = img.size
            target_width = specs["optimal_width"]
            target_height = specs["optimal_height"]

            # Calculate new dimensions
            if maintain_aspect_ratio:
                # Calculate aspect ratios
                current_aspect = current_width / current_height
                target_aspect = target_width / target_height

                # Fit within target dimensions while maintaining aspect ratio
                if current_aspect > target_aspect:
                    # Image is wider - fit to width
                    new_width = min(target_width, specs["max_width"])
                    new_height = int(new_width / current_aspect)
                else:
                    # Image is taller - fit to height
                    new_height = min(target_height, specs["max_height"])
                    new_width = int(new_height * current_aspect)

                # Ensure minimum dimensions
                if new_width < specs["min_width"]:
                    new_width = specs["min_width"]
                    new_height = int(new_width / current_aspect)
                if new_height < specs["min_height"]:
                    new_height = specs["min_height"]
                    new_width = int(new_height * current_aspect)

                # Ensure maximum dimensions
                if new_width > specs["max_width"]:
                    new_width = specs["max_width"]
                    new_height = int(new_width / current_aspect)
                if new_height > specs["max_height"]:
                    new_height = specs["max_height"]
                    new_width = int(new_height * current_aspect)
            else:
                # Use exact target dimensions
                new_width = target_width
                new_height = target_height

            # Resize if needed
            if (new_width, new_height) != (current_width, current_height):
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.info(f"Resized image from {current_width}x{current_height} to {new_width}x{new_height} for {platform.value}")

            # Save optimized image
            save_kwargs: dict[str, Any] = {}
            if specs["format"] == "JPEG":
                save_kwargs["quality"] = specs["quality"]
                save_kwargs["optimize"] = True
            elif specs["format"] == "PNG":
                save_kwargs["optimize"] = True

            img.save(str(output_path), format=specs["format"], **save_kwargs)

            # Check file size and compress if needed
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            if file_size_mb > specs["max_size_mb"]:
                # Reduce quality and re-save
                quality = specs["quality"]
                while file_size_mb > specs["max_size_mb"] and quality > 50:
                    quality -= 5
                    if specs["format"] == "JPEG":
                        img.save(str(output_path), format=specs["format"], quality=quality, optimize=True)
                    file_size_mb = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"Compressed image to {file_size_mb:.2f}MB (quality={quality}) for {platform.value}")

            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            logger.info(
                f"Optimized image for {platform.value}: {new_width}x{new_height}, "
                f"{file_size_mb:.2f}MB, format={specs['format']}"
            )

            return output_path

        except Exception as exc:
            raise PlatformImageOptimizationError(f"Failed to optimize image for {platform.value}: {exc}") from exc

    def get_platform_specs(self, platform: Platform | str) -> dict[str, Any]:
        """
        Get platform-specific optimization specifications.

        Args:
            platform: Platform (Platform enum or string)

        Returns:
            Dictionary with platform specifications
        """
        if isinstance(platform, str):
            try:
                platform = Platform(platform.lower())
            except ValueError:
                platform = Platform.GENERIC

        return self.PLATFORM_SPECS[platform].copy()
