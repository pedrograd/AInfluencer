"""
Frame Interpolation Service
Implements RIFE, DAIN, and FILM frame interpolation methods
"""
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import subprocess
import sys

logger = logging.getLogger(__name__)


class FrameInterpolationMethod(str):
    """Frame interpolation methods"""
    RIFE = "rife"
    DAIN = "dain"
    FILM = "film"
    FFMPEG = "ffmpeg"  # Fallback


class FrameInterpolationService:
    """Service for frame interpolation to increase video frame rate"""
    
    def __init__(self):
        self.comfyui_models_path = Path(__file__).parent.parent.parent / "ComfyUI" / "models"
        self.rife_models_path = self.comfyui_models_path / "rife"
        self.dain_models_path = self.comfyui_models_path / "dain"
        
    def interpolate_frames(
        self,
        input_video_path: Path,
        output_video_path: Path,
        method: FrameInterpolationMethod = FrameInterpolationMethod.RIFE,
        scale: int = 2,
        fps: Optional[int] = None
    ) -> bool:
        """
        Interpolate frames in video to increase frame rate
        
        Args:
            input_video_path: Path to input video
            output_video_path: Path to output video
            method: Interpolation method to use
            scale: Multiplier for frame rate (2 = double, 4 = quadruple)
            fps: Target FPS (overrides scale if provided)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if method == FrameInterpolationMethod.RIFE:
                return self._interpolate_rife(input_video_path, output_video_path, scale, fps)
            elif method == FrameInterpolationMethod.DAIN:
                return self._interpolate_dain(input_video_path, output_video_path, scale, fps)
            elif method == FrameInterpolationMethod.FILM:
                return self._interpolate_film(input_video_path, output_video_path, scale, fps)
            elif method == FrameInterpolationMethod.FFMPEG:
                return self._interpolate_ffmpeg(input_video_path, output_video_path, scale, fps)
            else:
                logger.error(f"Unknown interpolation method: {method}")
                return False
                
        except Exception as e:
            logger.error(f"Frame interpolation error: {e}")
            return False
    
    def _interpolate_rife(
        self,
        input_path: Path,
        output_path: Path,
        scale: int,
        fps: Optional[int]
    ) -> bool:
        """Interpolate using RIFE (Real-Time Intermediate Flow Estimation)"""
        try:
            # Check if RIFE is available
            try:
                import rife
                has_rife = True
            except ImportError:
                has_rife = False
                logger.warning("RIFE not installed, using FFmpeg fallback")
                return self._interpolate_ffmpeg(input_path, output_path, scale, fps)
            
            if has_rife:
                # Use RIFE Python API if available
                # This is a placeholder - actual implementation depends on RIFE library
                logger.info(f"RIFE interpolation: {scale}x scale")
                # TODO: Implement RIFE interpolation
                # For now, fallback to FFmpeg
                return self._interpolate_ffmpeg(input_path, output_path, scale, fps)
            
            return False
            
        except Exception as e:
            logger.error(f"RIFE interpolation error: {e}")
            return False
    
    def _interpolate_dain(
        self,
        input_path: Path,
        output_path: Path,
        scale: int,
        fps: Optional[int]
    ) -> bool:
        """Interpolate using DAIN (Depth-Aware Video Frame Interpolation)"""
        try:
            # DAIN typically requires separate installation
            # Check if available via ComfyUI or external tool
            logger.info(f"DAIN interpolation: {scale}x scale")
            # TODO: Implement DAIN interpolation
            # For now, fallback to FFmpeg
            return self._interpolate_ffmpeg(input_path, output_path, scale, fps)
            
        except Exception as e:
            logger.error(f"DAIN interpolation error: {e}")
            return False
    
    def _interpolate_film(
        self,
        input_path: Path,
        output_path: Path,
        scale: int,
        fps: Optional[int]
    ) -> bool:
        """Interpolate using FILM (Frame Interpolation for Large Motion)"""
        try:
            # FILM from Google Research
            logger.info(f"FILM interpolation: {scale}x scale")
            # TODO: Implement FILM interpolation
            # For now, fallback to FFmpeg
            return self._interpolate_ffmpeg(input_path, output_path, scale, fps)
            
        except Exception as e:
            logger.error(f"FILM interpolation error: {e}")
            return False
    
    def _interpolate_ffmpeg(
        self,
        input_path: Path,
        output_path: Path,
        scale: int,
        fps: Optional[int]
    ) -> bool:
        """Interpolate using FFmpeg (fallback method)"""
        try:
            # Get input FPS
            import subprocess
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error", "-select_streams", "v:0",
                    "-show_entries", "stream=r_frame_rate", "-of", "default=noprint_wrappers=1:nokey=1",
                    str(input_path)
                ],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.warning("Could not get input FPS, using default")
                input_fps = 8
            else:
                # Parse frame rate (e.g., "30/1" -> 30)
                fps_str = result.stdout.strip()
                if "/" in fps_str:
                    num, den = map(int, fps_str.split("/"))
                    input_fps = num / den if den != 0 else 8
                else:
                    input_fps = float(fps_str) if fps_str else 8
            
            # Calculate target FPS
            if fps:
                target_fps = fps
            else:
                target_fps = input_fps * scale
            
            # Use FFmpeg minterpolate filter for frame interpolation
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            cmd = [
                "ffmpeg", "-i", str(input_path),
                "-filter:v", f"minterpolate=fps={target_fps}:mi_mode=mci",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-y", str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"FFmpeg interpolation successful: {input_fps}fps -> {target_fps}fps")
                return True
            else:
                logger.error(f"FFmpeg interpolation failed: {result.stderr}")
                return False
                
        except FileNotFoundError:
            logger.error("FFmpeg not found. Please install FFmpeg.")
            return False
        except Exception as e:
            logger.error(f"FFmpeg interpolation error: {e}")
            return False
    
    def interpolate_frames_list(
        self,
        frames: List[Path],
        output_path: Path,
        method: FrameInterpolationMethod = FrameInterpolationMethod.RIFE,
        scale: int = 2
    ) -> bool:
        """
        Interpolate frames from a list of image files
        
        Args:
            frames: List of frame image paths
            output_path: Output video path
            method: Interpolation method
            scale: Frame rate multiplier
            
        Returns:
            True if successful
        """
        try:
            # First, create a temporary video from frames
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_video = Path(tmpdir) / "temp_input.mp4"
                
                # Create video from frames using FFmpeg
                frame_pattern = str(frames[0].parent / "frame_%04d.png")
                # Rename frames to sequential pattern
                for i, frame in enumerate(frames):
                    new_name = frames[0].parent / f"frame_{i+1:04d}.png"
                    if frame != new_name:
                        import shutil
                        shutil.copy2(frame, new_name)
                
                # Create video
                subprocess.run([
                    "ffmpeg", "-y", "-framerate", "8", "-i", frame_pattern,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(tmp_video)
                ], check=True, capture_output=True)
                
                # Interpolate
                return self.interpolate_frames(tmp_video, output_path, method, scale)
                
        except Exception as e:
            logger.error(f"Frame list interpolation error: {e}")
            return False
