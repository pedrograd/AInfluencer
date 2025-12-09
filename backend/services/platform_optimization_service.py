"""
Platform Optimization Service
Optimizes videos for specific platforms (Instagram, OnlyFans, YouTube, Twitter)
"""
import logging
from pathlib import Path
from typing import Dict, Optional, Any
import subprocess

logger = logging.getLogger(__name__)


class PlatformOptimizationService:
    """Service for platform-specific video optimization"""
    
    PLATFORM_SPECS = {
        "instagram_reels": {
            "resolution": (1080, 1920),  # 9:16
            "fps": 30,
            "max_duration": 90,
            "min_duration": 15,
            "format": "mp4",
            "codec": "h264",
            "max_size_mb": 4000,
            "aspect_ratio": "9:16"
        },
        "instagram_feed": {
            "resolution": (1080, 1080),  # 1:1
            "fps": 30,
            "max_duration": 60,
            "format": "mp4",
            "codec": "h264",
            "aspect_ratio": "1:1"
        },
        "onlyfans": {
            "resolution": (1080, 1920),  # 9:16 or 1920x1080
            "fps": 24,
            "format": "mp4",
            "codec": "h264",
            "quality": "high",
            "aspect_ratio": "9:16"
        },
        "youtube": {
            "resolution": (1920, 1080),  # 16:9
            "fps": 24,
            "format": "mp4",
            "codec": "h264",
            "aspect_ratio": "16:9"
        },
        "youtube_shorts": {
            "resolution": (1080, 1920),  # 9:16
            "fps": 30,
            "max_duration": 60,
            "format": "mp4",
            "codec": "h264",
            "aspect_ratio": "9:16"
        },
        "twitter": {
            "resolution": (1280, 720),  # 16:9
            "fps": 30,
            "max_duration": 140,  # 2:20
            "format": "mp4",
            "codec": "h264",
            "max_size_mb": 512,
            "aspect_ratio": "16:9"
        },
        "tiktok": {
            "resolution": (1080, 1920),  # 9:16
            "fps": 30,
            "max_duration": 60,
            "format": "mp4",
            "codec": "h264",
            "aspect_ratio": "9:16"
        }
    }
    
    def optimize_for_platform(
        self,
        input_path: Path,
        output_path: Path,
        platform: str,
        quality: str = "high"
    ) -> bool:
        """
        Optimize video for specific platform
        
        Args:
            input_path: Input video path
            output_path: Output video path
            platform: Platform name (instagram_reels, onlyfans, youtube, etc.)
            quality: Quality preset (low, medium, high, ultra)
            
        Returns:
            True if successful
        """
        try:
            if platform not in self.PLATFORM_SPECS:
                logger.error(f"Unknown platform: {platform}")
                return False
            
            specs = self.PLATFORM_SPECS[platform]
            width, height = specs["resolution"]
            fps = specs["fps"]
            codec = specs.get("codec", "h264")
            max_duration = specs.get("max_duration")
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Quality settings
            crf_map = {
                "low": "28",
                "medium": "23",
                "high": "18",
                "ultra": "15"
            }
            crf = crf_map.get(quality, "23")
            
            # Build FFmpeg command
            cmd = [
                "ffmpeg", "-i", str(input_path),
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
                "-r", str(fps),
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", crf,
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                "-c:a", "aac",
                "-b:a", "128k"
            ]
            
            # Add duration limit if specified
            if max_duration:
                cmd.extend(["-t", str(max_duration)])
            
            # Add max size constraint for Twitter
            if platform == "twitter" and specs.get("max_size_mb"):
                # Calculate bitrate to fit size
                max_size_bytes = specs["max_size_mb"] * 1024 * 1024
                # Rough estimate: bitrate = size / duration
                # Use conservative estimate
                max_bitrate = "2000k"
                cmd.extend(["-maxrate", max_bitrate, "-bufsize", str(int(max_bitrate.replace("k", "")) * 2) + "k"])
            
            cmd.extend(["-y", str(output_path)])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Video optimized for {platform}: {output_path}")
                return True
            else:
                logger.error(f"Platform optimization failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Platform optimization error: {e}")
            return False
    
    def get_platform_specs(self, platform: str) -> Optional[Dict[str, Any]]:
        """Get platform specifications"""
        return self.PLATFORM_SPECS.get(platform)
    
    def get_recommended_settings(
        self,
        platform: str,
        video_duration: Optional[float] = None
    ) -> Dict[str, Any]:
        """Get recommended settings for platform"""
        specs = self.PLATFORM_SPECS.get(platform)
        if not specs:
            return {}
        
        settings = {
            "resolution": specs["resolution"],
            "fps": specs["fps"],
            "aspect_ratio": specs.get("aspect_ratio", "16:9"),
            "format": specs.get("format", "mp4"),
            "codec": specs.get("codec", "h264")
        }
        
        if video_duration:
            max_duration = specs.get("max_duration")
            min_duration = specs.get("min_duration")
            
            if max_duration and video_duration > max_duration:
                settings["warning"] = f"Video duration ({video_duration}s) exceeds platform max ({max_duration}s)"
            if min_duration and video_duration < min_duration:
                settings["warning"] = f"Video duration ({video_duration}s) is below platform min ({min_duration}s)"
        
        return settings
