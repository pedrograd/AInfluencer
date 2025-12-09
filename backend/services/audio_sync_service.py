"""
Audio Synchronization Service
Handles adding and synchronizing audio with videos
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import subprocess

logger = logging.getLogger(__name__)


class AudioSyncService:
    """Service for audio synchronization with videos"""
    
    def __init__(self):
        pass
    
    def add_audio_to_video(
        self,
        video_path: Path,
        audio_path: Path,
        output_path: Path,
        sync_delay: float = 0.0,
        audio_volume: float = 1.0,
        replace_audio: bool = True
    ) -> bool:
        """
        Add audio track to video
        
        Args:
            video_path: Path to video file
            audio_path: Path to audio file
            output_path: Path to output video
            sync_delay: Audio delay in seconds (positive = delay, negative = advance)
            audio_volume: Audio volume multiplier (1.0 = original, 0.5 = half, 2.0 = double)
            replace_audio: If True, replace existing audio; if False, mix with existing
            
        Returns:
            True if successful
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Build FFmpeg command
            if replace_audio:
                # Replace audio track
                if sync_delay != 0.0:
                    # Use itsoffset for delay
                    if sync_delay > 0:
                        cmd = [
                            "ffmpeg", "-i", str(video_path),
                            "-itsoffset", str(sync_delay),
                            "-i", str(audio_path),
                            "-c:v", "copy",  # Copy video stream
                            "-c:a", "aac",  # Encode audio as AAC
                            "-map", "0:v:0",  # Use video from first input
                            "-map", "1:a:0",  # Use audio from second input
                        ]
                    else:
                        # Negative delay - trim audio start
                        cmd = [
                            "ffmpeg", "-i", str(video_path),
                            "-ss", str(abs(sync_delay)),
                            "-i", str(audio_path),
                            "-c:v", "copy",
                            "-c:a", "aac",
                            "-map", "0:v:0",
                            "-map", "1:a:0",
                        ]
                else:
                    cmd = [
                        "ffmpeg", "-i", str(video_path),
                        "-i", str(audio_path),
                        "-c:v", "copy",
                        "-c:a", "aac",
                        "-map", "0:v:0",
                        "-map", "1:a:0",
                    ]
                
                # Add volume adjustment if needed
                if audio_volume != 1.0:
                    # Insert volume filter
                    cmd.insert(-1, "-filter:a")
                    cmd.insert(-1, f"volume={audio_volume}")
                
                cmd.extend(["-shortest", "-y", str(output_path)])
            else:
                # Mix audio with existing
                cmd = [
                    "ffmpeg", "-i", str(video_path),
                    "-i", str(audio_path),
                    "-filter_complex",
                    "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-shortest",
                    "-y", str(output_path)
                ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Audio added to video: {output_path}")
                return True
            else:
                logger.error(f"Audio sync failed: {result.stderr}")
                return False
                
        except FileNotFoundError:
            logger.error("FFmpeg not found. Please install FFmpeg.")
            return False
        except Exception as e:
            logger.error(f"Audio sync error: {e}")
            return False
    
    def extract_audio_from_video(
        self,
        video_path: Path,
        output_audio_path: Path,
        format: str = "mp3"
    ) -> bool:
        """
        Extract audio track from video
        
        Args:
            video_path: Path to video file
            output_audio_path: Path to output audio file
            format: Audio format (mp3, wav, aac)
            
        Returns:
            True if successful
        """
        try:
            output_audio_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Determine codec based on format
            codec_map = {
                "mp3": "libmp3lame",
                "wav": "pcm_s16le",
                "aac": "aac"
            }
            codec = codec_map.get(format.lower(), "libmp3lame")
            
            cmd = [
                "ffmpeg", "-i", str(video_path),
                "-vn",  # No video
                "-acodec", codec,
                "-y", str(output_audio_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Audio extracted: {output_audio_path}")
                return True
            else:
                logger.error(f"Audio extraction failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Audio extraction error: {e}")
            return False
    
    def sync_audio_to_video_length(
        self,
        audio_path: Path,
        video_duration: float,
        output_audio_path: Path,
        loop: bool = False,
        fade_out: bool = True
    ) -> bool:
        """
        Adjust audio length to match video duration
        
        Args:
            audio_path: Path to audio file
            video_duration: Target video duration in seconds
            output_audio_path: Path to output audio
            loop: If True, loop audio to fill duration
            fade_out: If True, apply fade out at end
            
        Returns:
            True if successful
        """
        try:
            output_audio_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get audio duration
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(audio_path)
                ],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error("Could not get audio duration")
                return False
            
            audio_duration = float(result.stdout.strip())
            
            if audio_duration >= video_duration:
                # Audio is longer - trim it
                cmd = [
                    "ffmpeg", "-i", str(audio_path),
                    "-t", str(video_duration),
                    "-c", "copy",
                    "-y", str(output_audio_path)
                ]
            else:
                # Audio is shorter
                if loop:
                    # Loop audio to fill duration
                    loops_needed = int(video_duration / audio_duration) + 1
                    cmd = [
                        "ffmpeg",
                        "-stream_loop", str(loops_needed),
                        "-i", str(audio_path),
                        "-t", str(video_duration),
                        "-c", "copy",
                        "-y", str(output_audio_path)
                    ]
                else:
                    # Just extend with silence or repeat
                    cmd = [
                        "ffmpeg", "-i", str(audio_path),
                        "-af", f"apad=pad_dur={video_duration - audio_duration}",
                        "-y", str(output_audio_path)
                    ]
            
            # Add fade out if requested
            if fade_out and video_duration > 1.0:
                # Modify command to add fade out
                if "-af" in cmd:
                    # Append to existing filter
                    fade_index = cmd.index("-af")
                    cmd[fade_index + 1] += f",afade=t=out:st={video_duration - 0.5}:d=0.5"
                else:
                    # Add new filter
                    cmd.insert(-2, "-af")
                    cmd.insert(-2, f"afade=t=out:st={video_duration - 0.5}:d=0.5")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Audio synced to video length: {output_audio_path}")
                return True
            else:
                logger.error(f"Audio sync failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Audio length sync error: {e}")
            return False
    
    def generate_silent_audio(
        self,
        duration: float,
        output_path: Path,
        sample_rate: int = 44100
    ) -> bool:
        """
        Generate silent audio track
        
        Args:
            duration: Duration in seconds
            output_path: Path to output audio file
            sample_rate: Sample rate in Hz
            
        Returns:
            True if successful
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            cmd = [
                "ffmpeg", "-f", "lavfi",
                "-i", f"anullsrc=channel_layout=stereo:sample_rate={sample_rate}",
                "-t", str(duration),
                "-y", str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Silent audio generated: {output_path}")
                return True
            else:
                logger.error(f"Silent audio generation failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Silent audio generation error: {e}")
            return False
