"""Content repurposing service for cross-platform content adaptation.

This service handles repurposing content (images and videos) for different
social media platforms by creating platform-specific versions with appropriate
dimensions, formats, and optimizations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.paths import images_dir, videos_dir
from app.models.content import Content
from app.services.platform_image_optimization_service import (
    Platform,
    PlatformImageOptimizationService,
)
from app.services.video_editing_service import VideoEditingService

logger = get_logger(__name__)


class ContentRepurposingError(RuntimeError):
    """Error raised when content repurposing operations fail."""

    pass


class ContentRepurposingService:
    """Service for repurposing content for cross-platform distribution."""

    # Platform-specific video requirements
    VIDEO_PLATFORM_SPECS: dict[str, dict[str, Any]] = {
        "instagram": {
            "aspect_ratio": "9:16",  # Reels
            "max_duration": 90,  # seconds
            "min_duration": 15,
            "resolution": (1080, 1920),
            "fps": 30,
        },
        "instagram_reels": {
            "aspect_ratio": "9:16",
            "max_duration": 90,
            "min_duration": 15,
            "resolution": (1080, 1920),
            "fps": 30,
        },
        "youtube": {
            "aspect_ratio": "16:9",
            "max_duration": None,  # No limit for regular videos
            "min_duration": 1,
            "resolution": (1920, 1080),
            "fps": 30,
        },
        "youtube_shorts": {
            "aspect_ratio": "9:16",
            "max_duration": 60,
            "min_duration": 15,
            "resolution": (1080, 1920),
            "fps": 30,
        },
        "tiktok": {
            "aspect_ratio": "9:16",
            "max_duration": 180,  # 3 minutes
            "min_duration": 15,
            "resolution": (1080, 1920),
            "fps": 30,
        },
        "facebook": {
            "aspect_ratio": "16:9",
            "max_duration": None,
            "min_duration": 1,
            "resolution": (1280, 720),
            "fps": 30,
        },
        "facebook_reels": {
            "aspect_ratio": "9:16",
            "max_duration": 90,
            "min_duration": 15,
            "resolution": (1080, 1920),
            "fps": 30,
        },
        "twitter": {
            "aspect_ratio": "16:9",  # or 9:16
            "max_duration": 140,  # 2min 20s
            "min_duration": 1,
            "resolution": (1280, 720),
            "fps": 30,
        },
        "telegram": {
            "aspect_ratio": "16:9",  # Flexible
            "max_duration": None,
            "min_duration": 1,
            "resolution": (1280, 720),
            "fps": 30,
        },
    }

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize content repurposing service.

        Args:
            db: Database session for accessing content.
        """
        self.db = db
        self.image_optimizer = PlatformImageOptimizationService()
        self.video_editor = VideoEditingService()

    async def repurpose_content_for_platform(
        self,
        content_id: UUID,
        platform: str,
        output_path: Path | None = None,
    ) -> Path:
        """
        Repurpose content for a specific platform.

        Creates a platform-optimized version of the content (image or video)
        with appropriate dimensions, format, and quality settings.

        Args:
            content_id: UUID of the content to repurpose.
            platform: Target platform name (instagram, twitter, facebook, etc.).
            output_path: Optional output path for repurposed content.

        Returns:
            Path to the repurposed content file.

        Raises:
            ContentRepurposingError: If repurposing fails.
        """
        # Get content from database
        from sqlalchemy import select

        result = await self.db.execute(select(Content).where(Content.id == content_id))
        content = result.scalar_one_or_none()

        if not content:
            raise ContentRepurposingError(f"Content {content_id} not found")

        if not content.file_path:
            raise ContentRepurposingError(f"Content {content_id} has no file path")

        source_path = Path(content.file_path)
        if not source_path.exists():
            raise ContentRepurposingError(f"Content file not found: {source_path}")

        # Repurpose based on content type
        if content.content_type == "image":
            return await self._repurpose_image(content, platform, output_path)
        elif content.content_type == "video":
            return await self._repurpose_video(content, platform, output_path)
        else:
            raise ContentRepurposingError(
                f"Content repurposing not supported for type: {content.content_type}"
            )

    async def repurpose_content_for_multiple_platforms(
        self,
        content_id: UUID,
        platforms: list[str],
    ) -> dict[str, Path]:
        """
        Repurpose content for multiple platforms simultaneously.

        Args:
            content_id: UUID of the content to repurpose.
            platforms: List of target platform names.

        Returns:
            Dictionary mapping platform names to paths of repurposed content.

        Raises:
            ContentRepurposingError: If repurposing fails for any platform.
        """
        results: dict[str, Path] = {}
        errors: dict[str, str] = {}

        for platform in platforms:
            try:
                repurposed_path = await self.repurpose_content_for_platform(
                    content_id, platform
                )
                results[platform] = repurposed_path
                logger.info(
                    f"Repurposed content {content_id} for {platform}: {repurposed_path}"
                )
            except Exception as exc:
                error_msg = f"Failed to repurpose for {platform}: {exc}"
                errors[platform] = error_msg
                logger.error(error_msg)

        if errors and not results:
            raise ContentRepurposingError(
                f"Failed to repurpose content for any platform: {errors}"
            )

        if errors:
            logger.warning(
                f"Some platforms failed during repurposing: {errors}. "
                f"Successfully repurposed for: {list(results.keys())}"
            )

        return results

    async def _repurpose_image(
        self,
        content: Content,
        platform: str,
        output_path: Path | None = None,
    ) -> Path:
        """
        Repurpose an image for a specific platform.

        Args:
            content: Content object (must be image type).
            platform: Target platform name.
            output_path: Optional output path.

        Returns:
            Path to repurposed image.
        """
        if content.content_type != "image":
            raise ContentRepurposingError(
                f"Expected image content, got: {content.content_type}"
            )

        source_path = Path(content.file_path)

        try:
            # Use platform image optimization service
            repurposed_path = self.image_optimizer.optimize_for_platform(
                image_path=source_path,
                platform=platform,
                output_path=output_path,
                maintain_aspect_ratio=True,
            )

            logger.info(
                f"Repurposed image {content.id} for {platform}: "
                f"{source_path} -> {repurposed_path}"
            )

            return repurposed_path

        except Exception as exc:
            raise ContentRepurposingError(
                f"Failed to repurpose image for {platform}: {exc}"
            ) from exc

    async def _repurpose_video(
        self,
        content: Content,
        platform: str,
        output_path: Path | None = None,
    ) -> Path:
        """
        Repurpose a video for a specific platform.

        Args:
            content: Content object (must be video type).
            platform: Target platform name.
            output_path: Optional output path.

        Returns:
            Path to repurposed video.
        """
        if content.content_type != "video":
            raise ContentRepurposingError(
                f"Expected video content, got: {content.content_type}"
            )

        source_path = Path(content.file_path)
        platform_lower = platform.lower()

        # Get platform specs
        if platform_lower not in self.VIDEO_PLATFORM_SPECS:
            logger.warning(
                f"Unknown platform {platform}, using generic settings. "
                f"Available platforms: {list(self.VIDEO_PLATFORM_SPECS.keys())}"
            )
            # Use generic/YouTube settings as fallback
            specs = self.VIDEO_PLATFORM_SPECS.get("youtube", {})
        else:
            specs = self.VIDEO_PLATFORM_SPECS[platform_lower]

        # Determine output path
        if output_path is None:
            repurpose_dir = videos_dir() / "repurposed"
            repurpose_dir.mkdir(parents=True, exist_ok=True)
            stem = source_path.stem
            output_path = repurpose_dir / f"{stem}_{platform_lower}.mp4"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # For now, we'll use video editing service for basic operations
            # In a full implementation, this would handle:
            # - Resizing to target resolution
            # - Cropping/letterboxing for aspect ratio
            # - Trimming if duration exceeds max_duration
            # - Re-encoding with platform-specific codec settings

            # Check if video needs trimming
            needs_trimming = False
            trim_end = None
            if content.duration and specs.get("max_duration"):
                if content.duration > specs["max_duration"]:
                    needs_trimming = True
                    trim_end = specs["max_duration"]

            # For MVP, we'll create a job for resizing/format conversion
            # In production, this would use ffmpeg or similar
            if needs_trimming:
                # Create trim job
                job_id = self.video_editor.trim_video(
                    video_path=str(source_path),
                    start_time=0,
                    end_time=trim_end,
                    output_path=str(output_path),
                )
                logger.info(
                    f"Created video trim job {job_id} for {platform} "
                    f"(trimming to {trim_end}s)"
                )
                # Note: In a real implementation, we'd wait for job completion
                # For MVP, we'll return the output path
            else:
                # For now, just copy the file (in production, would resize/re-encode)
                import shutil

                shutil.copy2(source_path, output_path)
                logger.info(
                    f"Copied video {content.id} for {platform} "
                    f"(no trimming needed): {output_path}"
                )

            logger.info(
                f"Repurposed video {content.id} for {platform}: "
                f"{source_path} -> {output_path}"
            )

            return output_path

        except Exception as exc:
            raise ContentRepurposingError(
                f"Failed to repurpose video for {platform}: {exc}"
            ) from exc

    def get_supported_platforms(self, content_type: str) -> list[str]:
        """
        Get list of supported platforms for a content type.

        Args:
            content_type: Content type (image or video).

        Returns:
            List of supported platform names.
        """
        if content_type == "image":
            return [p.value for p in Platform]
        elif content_type == "video":
            return list(self.VIDEO_PLATFORM_SPECS.keys())
        else:
            return []

    def get_platform_requirements(
        self, content_type: str, platform: str
    ) -> dict[str, Any]:
        """
        Get platform-specific requirements for content repurposing.

        Args:
            content_type: Content type (image or video).
            platform: Platform name.

        Returns:
            Dictionary with platform requirements (dimensions, format, etc.).
        """
        if content_type == "image":
            return self.image_optimizer.get_platform_specs(platform)
        elif content_type == "video":
            platform_lower = platform.lower()
            return self.VIDEO_PLATFORM_SPECS.get(
                platform_lower, self.VIDEO_PLATFORM_SPECS.get("youtube", {})
            )
        else:
            return {}
