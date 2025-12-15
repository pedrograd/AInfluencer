"""Quality validation service for generated content."""

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.core.paths import content_dir

logger = get_logger(__name__)


@dataclass
class QualityResult:
    """Result of quality validation."""

    quality_score: Decimal | None  # 0.0 to 1.0
    is_valid: bool
    checks_passed: list[str]
    checks_failed: list[str]
    warnings: list[str]
    errors: list[str]
    metadata: dict[str, Any]


class QualityValidator:
    """Validates quality of generated content."""

    def __init__(self) -> None:
        """Initialize quality validator."""
        self._min_resolution = (512, 512)  # Minimum acceptable resolution
        self._preferred_resolution = (1024, 1024)  # Preferred resolution

    def validate_content(
        self, content_id: str | None = None, file_path: str | None = None
    ) -> QualityResult:
        """
        Validate content quality.

        Args:
            content_id: Content ID (for database lookup, not implemented yet)
            file_path: Path to content file

        Returns:
            QualityResult with quality score and validation details
        """
        if not file_path:
            return QualityResult(
                quality_score=None,
                is_valid=False,
                checks_passed=[],
                checks_failed=[],
                warnings=[],
                errors=["file_path is required"],
                metadata={},
            )

        # Resolve file path
        file_path_obj = Path(file_path)
        if not file_path_obj.is_absolute():
            # Try relative to content directory
            file_path_obj = content_dir() / file_path

        return self._validate_file(file_path_obj)

    def _validate_file(self, file_path: Path) -> QualityResult:
        """Validate a single file."""
        checks_passed: list[str] = []
        checks_failed: list[str] = []
        warnings: list[str] = []
        errors: list[str] = []
        metadata: dict[str, Any] = {}

        # Check file exists
        if not file_path.exists():
            errors.append(f"File does not exist: {file_path}")
            return QualityResult(
                quality_score=None,
                is_valid=False,
                checks_passed=[],
                checks_failed=[],
                warnings=[],
                errors=errors,
                metadata={},
            )

        checks_passed.append("file_exists")

        # Check file is readable
        if not os.access(file_path, os.R_OK):
            errors.append(f"File is not readable: {file_path}")
            return QualityResult(
                quality_score=None,
                is_valid=False,
                checks_passed=checks_passed,
                checks_failed=[],
                warnings=[],
                errors=errors,
                metadata={},
            )

        checks_passed.append("file_readable")

        # Get file size
        try:
            file_size = file_path.stat().st_size
            metadata["file_size"] = file_size

            # Check minimum file size (very small files might be corrupted)
            if file_size < 1024:  # Less than 1KB
                warnings.append(f"File size is very small: {file_size} bytes")
            else:
                checks_passed.append("file_size_valid")
        except OSError as exc:
            errors.append(f"Failed to get file size: {exc}")

        # Validate based on file type
        file_ext = file_path.suffix.lower()
        if file_ext in (".png", ".jpg", ".jpeg", ".webp"):
            return self._validate_image(file_path, checks_passed, checks_failed, warnings, errors, metadata)
        elif file_ext in (".mp4", ".webm", ".mov"):
            return self._validate_video(file_path, checks_passed, checks_failed, warnings, errors, metadata)
        else:
            # For other file types, do basic validation only
            warnings.append(f"File type {file_ext} validation not fully implemented")
            quality_score = self._calculate_basic_score(checks_passed, checks_failed, warnings, errors)
            return QualityResult(
                quality_score=quality_score,
                is_valid=len(errors) == 0,
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                warnings=warnings,
                errors=errors,
                metadata=metadata,
            )

    def _validate_image(
        self,
        file_path: Path,
        checks_passed: list[str],
        checks_failed: list[str],
        warnings: list[str],
        errors: list[str],
        metadata: dict[str, Any],
    ) -> QualityResult:
        """Validate image file."""
        try:
            from PIL import Image

            with Image.open(file_path) as img:
                width, height = img.size
                metadata["width"] = width
                metadata["height"] = height
                metadata["format"] = img.format
                metadata["mode"] = img.mode

                # Check resolution
                if width >= self._min_resolution[0] and height >= self._min_resolution[1]:
                    checks_passed.append("resolution_minimum")
                else:
                    checks_failed.append(
                        f"Resolution below minimum: {width}x{height} (min: {self._min_resolution[0]}x{self._min_resolution[1]})"
                    )

                # Check if resolution is preferred or better
                if width >= self._preferred_resolution[0] and height >= self._preferred_resolution[1]:
                    checks_passed.append("resolution_preferred")
                else:
                    warnings.append(
                        f"Resolution below preferred: {width}x{height} (preferred: {self._preferred_resolution[0]}x{self._preferred_resolution[1]})"
                    )

                # Basic blur detection using Laplacian variance (if we had OpenCV)
                # For now, we'll skip this and add it later if needed
                # checks_passed.append("blur_check_skipped")

        except ImportError:
            warnings.append("PIL/Pillow not available, skipping image validation")
        except Exception as exc:
            errors.append(f"Failed to validate image: {exc}")

        quality_score = self._calculate_quality_score(checks_passed, checks_failed, warnings, errors, metadata)

        return QualityResult(
            quality_score=quality_score,
            is_valid=len(errors) == 0,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            warnings=warnings,
            errors=errors,
            metadata=metadata,
        )

    def _validate_video(
        self,
        file_path: Path,
        checks_passed: list[str],
        checks_failed: list[str],
        warnings: list[str],
        errors: list[str],
        metadata: dict[str, Any],
    ) -> QualityResult:
        """Validate video file."""
        # Basic video validation - can be enhanced later
        warnings.append("Video validation is basic (file exists and readable)")
        checks_passed.append("video_file_valid")

        quality_score = self._calculate_basic_score(checks_passed, checks_failed, warnings, errors)

        return QualityResult(
            quality_score=quality_score,
            is_valid=len(errors) == 0,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            warnings=warnings,
            errors=errors,
            metadata=metadata,
        )

    def _calculate_quality_score(
        self,
        checks_passed: list[str],
        checks_failed: list[str],
        warnings: list[str],
        errors: list[str],
        metadata: dict[str, Any],
    ) -> Decimal | None:
        """Calculate quality score (0.0 to 1.0)."""
        if errors:
            return None

        total_checks = len(checks_passed) + len(checks_failed)
        if total_checks == 0:
            return Decimal("0.5")  # Default score if no checks

        # Base score from passed checks
        base_score = len(checks_passed) / total_checks

        # Deduct for warnings (small penalty)
        warning_penalty = len(warnings) * 0.05
        score = max(0.0, min(1.0, base_score - warning_penalty))

        # Bonus for preferred resolution (if image)
        if "resolution_preferred" in checks_passed:
            score = min(1.0, score + 0.1)

        return Decimal(str(round(score, 2)))

    def _calculate_basic_score(
        self,
        checks_passed: list[str],
        checks_failed: list[str],
        warnings: list[str],
        errors: list[str],
    ) -> Decimal | None:
        """
        Calculate basic quality score from check results without metadata bonuses.
        
        Args:
            checks_passed: List of passed check names
            checks_failed: List of failed check names
            warnings: List of warning messages
            errors: List of error messages
        
        Returns:
            Quality score as Decimal (0.0 to 1.0), or None if errors present.
            Score is based on passed/total checks ratio with warning penalties.
        """
        if errors:
            return None

        total_checks = len(checks_passed) + len(checks_failed)
        if total_checks == 0:
            return Decimal("0.5")

        base_score = len(checks_passed) / total_checks
        warning_penalty = len(warnings) * 0.05
        score = max(0.0, min(1.0, base_score - warning_penalty))

        return Decimal(str(round(score, 2)))


# Singleton instance
quality_validator = QualityValidator()

