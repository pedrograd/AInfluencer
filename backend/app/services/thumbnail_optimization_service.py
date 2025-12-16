"""Service for generating and optimizing video thumbnails for YouTube and other platforms."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from app.core.logging import get_logger
from app.core.paths import thumbnails_dir, videos_dir

logger = get_logger(__name__)


class ThumbnailOptimizationError(RuntimeError):
    """Error raised when thumbnail optimization operations fail."""
    pass


class ThumbnailOptimizationService:
    """Service for generating and optimizing video thumbnails."""

    # YouTube thumbnail requirements
    YOUTUBE_MAX_WIDTH = 1280
    YOUTUBE_MAX_HEIGHT = 720
    YOUTUBE_MAX_SIZE_MB = 2
    YOUTUBE_FORMAT = "JPEG"
    
    # Minimum dimensions for YouTube
    YOUTUBE_MIN_WIDTH = 640
    YOUTUBE_MIN_HEIGHT = 360

    def __init__(self) -> None:
        """Initialize the thumbnail optimization service."""
        self.logger = get_logger(__name__)
        if not PIL_AVAILABLE:
            self.logger.warning("PIL/Pillow not available - thumbnail optimization will be limited")

    def _check_ffmpeg_available(self) -> bool:
        """Check if ffmpeg is available on the system.
        
        Returns:
            True if ffmpeg is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False

    def generate_thumbnail_from_video(
        self,
        video_path: str | Path,
        output_path: str | Path | None = None,
        timestamp: float | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> Path:
        """
        Generate a thumbnail from a video file using ffmpeg.
        
        Args:
            video_path: Path to the video file
            output_path: Path where thumbnail should be saved (optional, auto-generated if None)
            timestamp: Timestamp in seconds to capture frame (default: middle of video or 1 second)
            width: Output width in pixels (optional, maintains aspect ratio if only one dimension specified)
            height: Output height in pixels (optional, maintains aspect ratio if only one dimension specified)
        
        Returns:
            Path to the generated thumbnail file
        
        Raises:
            ThumbnailOptimizationError: If thumbnail generation fails
        """
        video_path_obj = Path(video_path)
        if not video_path_obj.exists():
            raise ThumbnailOptimizationError(f"Video file not found: {video_path}")
        
        if not self._check_ffmpeg_available():
            raise ThumbnailOptimizationError("ffmpeg is not available. Please install ffmpeg to generate thumbnails.")
        
        # Determine output path
        if output_path is None:
            thumb_dir = thumbnails_dir()
            thumb_dir.mkdir(parents=True, exist_ok=True)
            output_path = thumb_dir / f"{video_path_obj.stem}.jpg"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get video duration if timestamp not specified
        if timestamp is None:
            try:
                result = subprocess.run(
                    [
                        "ffprobe",
                        "-v", "error",
                        "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1",
                        str(video_path_obj),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    try:
                        duration = float(result.stdout.strip())
                        # Use middle of video or 1 second, whichever is smaller
                        timestamp = min(duration / 2, 1.0)
                    except ValueError:
                        timestamp = 1.0
                else:
                    timestamp = 1.0
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                timestamp = 1.0
        
        # Build ffmpeg command
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file
            "-ss", str(timestamp),  # Seek to timestamp
            "-i", str(video_path_obj),  # Input video
            "-vframes", "1",  # Extract 1 frame
            "-q:v", "2",  # High quality (1-31, lower is better)
        ]
        
        # Add scaling if dimensions specified
        if width is not None or height is not None:
            if width is not None and height is not None:
                scale_filter = f"scale={width}:{height}"
            elif width is not None:
                scale_filter = f"scale={width}:-1"  # Maintain aspect ratio
            elif height is not None:
                scale_filter = f"scale=-1:{height}"  # Maintain aspect ratio
            else:
                scale_filter = None
            
            if scale_filter:
                cmd.extend(["-vf", scale_filter])
        
        cmd.append(str(output_path))
        
        try:
            self.logger.info(f"Generating thumbnail from video: {video_path_obj.name} at {timestamp}s")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode != 0:
                raise ThumbnailOptimizationError(
                    f"ffmpeg failed to generate thumbnail: {result.stderr}"
                )
            
            if not output_path.exists():
                raise ThumbnailOptimizationError("Thumbnail file was not created")
            
            self.logger.info(f"Thumbnail generated successfully: {output_path}")
            return output_path
            
        except subprocess.TimeoutExpired:
            raise ThumbnailOptimizationError("Thumbnail generation timed out")
        except Exception as exc:
            raise ThumbnailOptimizationError(f"Failed to generate thumbnail: {exc}") from exc

    def optimize_for_youtube(
        self,
        thumbnail_path: str | Path,
        output_path: str | Path | None = None,
    ) -> Path:
        """
        Optimize a thumbnail image for YouTube upload.
        
        YouTube requirements:
        - Recommended: 1280x720 pixels
        - Minimum: 640x360 pixels
        - Maximum file size: 2MB
        - Format: JPG, PNG, or GIF (JPG recommended)
        
        Args:
            thumbnail_path: Path to the thumbnail image to optimize
            output_path: Path where optimized thumbnail should be saved (optional, overwrites input if None)
        
        Returns:
            Path to the optimized thumbnail file
        
        Raises:
            ThumbnailOptimizationError: If optimization fails
        """
        if not PIL_AVAILABLE:
            raise ThumbnailOptimizationError("PIL/Pillow is required for thumbnail optimization")
        
        thumbnail_path_obj = Path(thumbnail_path)
        if not thumbnail_path_obj.exists():
            raise ThumbnailOptimizationError(f"Thumbnail file not found: {thumbnail_path}")
        
        if output_path is None:
            output_path = thumbnail_path_obj
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Open image
            img = Image.open(thumbnail_path_obj)
            
            # Convert to RGB if necessary (for JPG output)
            if img.mode in ("RGBA", "LA", "P"):
                # Create white background for transparent images
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                rgb_img.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                img = rgb_img
            elif img.mode != "RGB":
                img = img.convert("RGB")
            
            # Get current dimensions
            current_width, current_height = img.size
            
            # Calculate optimal dimensions (maintain aspect ratio, fit within 1280x720)
            aspect_ratio = current_width / current_height
            
            if aspect_ratio > (self.YOUTUBE_MAX_WIDTH / self.YOUTUBE_MAX_HEIGHT):
                # Wider than 16:9, fit to width
                new_width = self.YOUTUBE_MAX_WIDTH
                new_height = int(self.YOUTUBE_MAX_WIDTH / aspect_ratio)
            else:
                # Taller than 16:9, fit to height
                new_height = self.YOUTUBE_MAX_HEIGHT
                new_width = int(self.YOUTUBE_MAX_HEIGHT * aspect_ratio)
            
            # Ensure minimum dimensions
            if new_width < self.YOUTUBE_MIN_WIDTH:
                new_width = self.YOUTUBE_MIN_WIDTH
                new_height = int(self.YOUTUBE_MIN_WIDTH / aspect_ratio)
            if new_height < self.YOUTUBE_MIN_HEIGHT:
                new_height = self.YOUTUBE_MIN_HEIGHT
                new_width = int(self.YOUTUBE_MIN_HEIGHT * aspect_ratio)
            
            # Resize if needed
            if (new_width, new_height) != (current_width, current_height):
                self.logger.info(
                    f"Resizing thumbnail from {current_width}x{current_height} to {new_width}x{new_height}"
                )
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save with quality optimization to meet size requirements
            quality = 95
            max_size_bytes = self.YOUTUBE_MAX_SIZE_MB * 1024 * 1024
            
            # Try saving with decreasing quality until size is acceptable
            for attempt in range(5):
                output_path_str = str(output_path)
                img.save(output_path_str, self.YOUTUBE_FORMAT, quality=quality, optimize=True)
                
                file_size = output_path.stat().st_size
                if file_size <= max_size_bytes:
                    self.logger.info(
                        f"Thumbnail optimized: {new_width}x{new_height}, {file_size / 1024:.1f}KB, quality={quality}"
                    )
                    break
                
                # Reduce quality for next attempt
                quality = max(70, quality - 5)
                if attempt == 4:
                    self.logger.warning(
                        f"Thumbnail size ({file_size / 1024 / 1024:.2f}MB) exceeds YouTube limit "
                        f"({self.YOUTUBE_MAX_SIZE_MB}MB) even at quality {quality}"
                    )
            
            return output_path
            
        except Exception as exc:
            raise ThumbnailOptimizationError(f"Failed to optimize thumbnail: {exc}") from exc

    def generate_and_optimize_for_youtube(
        self,
        video_path: str | Path,
        output_path: str | Path | None = None,
        timestamp: float | None = None,
    ) -> Path:
        """
        Generate a thumbnail from a video and optimize it for YouTube.
        
        This is a convenience method that combines generate_thumbnail_from_video
        and optimize_for_youtube.
        
        Args:
            video_path: Path to the video file
            output_path: Path where optimized thumbnail should be saved (optional, auto-generated if None)
            timestamp: Timestamp in seconds to capture frame (default: middle of video or 1 second)
        
        Returns:
            Path to the generated and optimized thumbnail file
        
        Raises:
            ThumbnailOptimizationError: If generation or optimization fails
        """
        # Generate thumbnail first
        if output_path is None:
            thumb_dir = thumbnails_dir()
            thumb_dir.mkdir(parents=True, exist_ok=True)
            video_path_obj = Path(video_path)
            temp_thumbnail = thumb_dir / f"{video_path_obj.stem}_temp.jpg"
        else:
            temp_thumbnail = Path(output_path).parent / f"{Path(output_path).stem}_temp.jpg"
        
        try:
            # Generate thumbnail at full resolution first
            generated_path = self.generate_thumbnail_from_video(
                video_path=video_path,
                output_path=temp_thumbnail,
                timestamp=timestamp,
            )
            
            # Optimize for YouTube
            optimized_path = self.optimize_for_youtube(
                thumbnail_path=generated_path,
                output_path=output_path,
            )
            
            # Clean up temp file if different from output
            if generated_path != optimized_path and generated_path.exists():
                generated_path.unlink()
            
            return optimized_path
            
        except Exception as exc:
            # Clean up temp file on error
            if temp_thumbnail.exists() and temp_thumbnail != output_path:
                try:
                    temp_thumbnail.unlink()
                except Exception:
                    pass
            raise

