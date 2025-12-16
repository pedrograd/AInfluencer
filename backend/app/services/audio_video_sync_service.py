"""Audio-video synchronization service.

This service synchronizes generated audio with video files,
ensuring proper timing, duration matching, and audio-video alignment.
"""

from __future__ import annotations

import subprocess
import threading
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Optional

from app.core.logging import get_logger
from app.core.paths import video_jobs_file

logger = get_logger(__name__)

AudioVideoSyncJobState = Literal["queued", "running", "cancelled", "failed", "succeeded"]


@dataclass
class AudioVideoSyncJob:
    """Audio-video synchronization job information.
    
    Attributes:
        id: Unique job identifier.
        state: Current job state (queued, running, cancelled, failed, succeeded).
        message: Human-readable status message describing the current state.
        created_at: Timestamp when job was created (Unix timestamp).
        started_at: Timestamp when job started processing (Unix timestamp), None if not started.
        finished_at: Timestamp when job finished (Unix timestamp), None if not finished.
        cancelled_at: Timestamp when job was cancelled (Unix timestamp), None if not cancelled.
        output_path: Path to the synchronized video file, None if not completed.
        error: Error message if job failed, None otherwise.
        params: Synchronization parameters (video_path, audio_path, sync_mode, etc.).
        cancel_requested: Whether cancellation has been requested for this job.
    """
    id: str
    state: AudioVideoSyncJobState = "queued"
    message: str | None = None
    created_at: float = 0.0
    started_at: float | None = None
    finished_at: float | None = None
    cancelled_at: float | None = None
    output_path: str | None = None
    error: str | None = None
    params: dict[str, Any] | None = None
    cancel_requested: bool = False


class AudioVideoSyncMode(str, Enum):
    """Audio-video synchronization modes."""
    
    REPLACE = "replace"  # Replace existing audio track
    MIX = "mix"  # Mix with existing audio track
    LOOP_AUDIO = "loop_audio"  # Loop audio to match video duration
    TRIM_AUDIO = "trim_audio"  # Trim audio to match video duration
    STRETCH_AUDIO = "stretch_audio"  # Stretch/compress audio to match video duration


class AudioVideoSyncService:
    """Service for synchronizing audio with video files."""
    
    def __init__(self):
        """Initialize the audio-video synchronization service."""
        self.logger = get_logger(__name__)
        self._lock = threading.Lock()
        self._jobs: dict[str, AudioVideoSyncJob] = {}
        video_jobs_file().parent.mkdir(parents=True, exist_ok=True)
        self._load_jobs_from_disk()
    
    def _load_jobs_from_disk(self) -> None:
        """Load jobs from disk if available."""
        try:
            if video_jobs_file().exists():
                with open(video_jobs_file(), "r") as f:
                    import json
                    data = json.load(f)
                    for job_data in data.get("sync_jobs", []):
                        job = AudioVideoSyncJob(**job_data)
                        self._jobs[job.id] = job
        except Exception as e:
            self.logger.warning(f"Failed to load audio-video sync jobs from disk: {e}")
    
    def _save_jobs_to_disk(self) -> None:
        """Save jobs to disk."""
        try:
            import json
            data = {
                "sync_jobs": [
                    {
                        "id": job.id,
                        "state": job.state,
                        "message": job.message,
                        "created_at": job.created_at,
                        "started_at": job.started_at,
                        "finished_at": job.finished_at,
                        "cancelled_at": job.cancelled_at,
                        "output_path": job.output_path,
                        "error": job.error,
                        "params": job.params,
                        "cancel_requested": job.cancel_requested,
                    }
                    for job in self._jobs.values()
                ]
            }
            with open(video_jobs_file(), "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save audio-video sync jobs to disk: {e}")
    
    def _check_ffmpeg_available(self) -> bool:
        """Check if ffmpeg is available on the system.
        
        Returns:
            True if ffmpeg is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False
    
    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds using ffprobe.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Duration in seconds
            
        Raises:
            RuntimeError: If duration cannot be determined
        """
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    video_path,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return float(result.stdout.strip())
            else:
                raise RuntimeError(f"ffprobe failed: {result.stderr}")
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError) as e:
            raise RuntimeError(f"Failed to get video duration: {e}") from e
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds using ffprobe.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds
            
        Raises:
            RuntimeError: If duration cannot be determined
        """
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    audio_path,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return float(result.stdout.strip())
            else:
                raise RuntimeError(f"ffprobe failed: {result.stderr}")
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError) as e:
            raise RuntimeError(f"Failed to get audio duration: {e}") from e
    
    def sync_audio_video(
        self,
        video_path: str,
        audio_path: str,
        output_path: str | None = None,
        sync_mode: AudioVideoSyncMode = AudioVideoSyncMode.REPLACE,
        audio_volume: float = 1.0,
        replace_existing_audio: bool = True,
    ) -> dict[str, Any]:
        """Synchronize audio with video file.
        
        Args:
            video_path: Path to the input video file
            audio_path: Path to the input audio file
            output_path: Optional path for the output synchronized video file
            sync_mode: Synchronization mode (replace, mix, loop_audio, trim_audio, stretch_audio)
            audio_volume: Audio volume multiplier (0.0 to 2.0, default: 1.0)
            replace_existing_audio: Whether to replace existing audio track (default: True)
            
        Returns:
            Dictionary with job information and status
        """
        self.logger.info(
            f"Audio-video sync requested: video={video_path}, audio={audio_path}, mode={sync_mode.value}"
        )
        
        # Validate inputs
        video_file = Path(video_path)
        audio_file = Path(audio_path)
        
        if not video_file.exists():
            raise ValueError(f"Video file not found: {video_path}")
        if not audio_file.exists():
            raise ValueError(f"Audio file not found: {audio_path}")
        
        # Check ffmpeg availability
        if not self._check_ffmpeg_available():
            raise RuntimeError(
                "ffmpeg is not available. Please install ffmpeg to use audio-video synchronization."
            )
        
        # Generate output path if not provided
        if not output_path:
            output_dir = video_file.parent / "synced"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"{video_file.stem}_synced{video_file.suffix}")
        
        # Create job
        job_id = str(uuid.uuid4())
        job = AudioVideoSyncJob(
            id=job_id,
            state="queued",
            message="Audio-video synchronization job queued",
            created_at=time.time(),
            params={
                "video_path": video_path,
                "audio_path": audio_path,
                "output_path": output_path,
                "sync_mode": sync_mode.value,
                "audio_volume": audio_volume,
                "replace_existing_audio": replace_existing_audio,
            },
        )
        
        with self._lock:
            self._jobs[job_id] = job
            self._save_jobs_to_disk()
        
        # Start processing in background thread
        thread = threading.Thread(
            target=self._process_sync_job,
            args=(job_id,),
            daemon=True,
        )
        thread.start()
        
        self.logger.info(f"Audio-video sync job created: {job_id}")
        
        return {
            "job_id": job_id,
            "status": "queued",
            "message": "Audio-video synchronization job queued",
            "output_path": output_path,
        }
    
    def _process_sync_job(self, job_id: str) -> None:
        """Process an audio-video synchronization job.
        
        Args:
            job_id: Unique identifier for the sync job
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                self.logger.error(f"Sync job not found: {job_id}")
                return
            
            if job.state != "queued":
                self.logger.warning(f"Sync job {job_id} is not in queued state: {job.state}")
                return
            
            job.state = "running"
            job.started_at = time.time()
            job.message = "Processing audio-video synchronization"
            self._save_jobs_to_disk()
        
        try:
            video_path = job.params["video_path"]
            audio_path = job.params["audio_path"]
            output_path = job.params["output_path"]
            sync_mode = AudioVideoSyncMode(job.params["sync_mode"])
            audio_volume = job.params.get("audio_volume", 1.0)
            replace_existing_audio = job.params.get("replace_existing_audio", True)
            
            # Get durations
            video_duration = self._get_video_duration(video_path)
            audio_duration = self._get_audio_duration(audio_path)
            
            self.logger.info(
                f"Sync job {job_id}: video_duration={video_duration:.2f}s, "
                f"audio_duration={audio_duration:.2f}s, mode={sync_mode.value}"
            )
            
            # Build ffmpeg command based on sync mode
            cmd = self._build_ffmpeg_command(
                video_path=video_path,
                audio_path=audio_path,
                output_path=output_path,
                sync_mode=sync_mode,
                video_duration=video_duration,
                audio_duration=audio_duration,
                audio_volume=audio_volume,
                replace_existing_audio=replace_existing_audio,
            )
            
            # Execute ffmpeg command
            self.logger.info(f"Executing ffmpeg command for sync job {job_id}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            
            if result.returncode != 0:
                error_msg = f"ffmpeg failed: {result.stderr}"
                self.logger.error(f"Sync job {job_id} failed: {error_msg}")
                with self._lock:
                    job.state = "failed"
                    job.finished_at = time.time()
                    job.error = error_msg
                    job.message = f"Synchronization failed: {error_msg[:100]}"
                    self._save_jobs_to_disk()
                return
            
            # Verify output file exists
            output_file = Path(output_path)
            if not output_file.exists():
                error_msg = "Output file was not created"
                self.logger.error(f"Sync job {job_id} failed: {error_msg}")
                with self._lock:
                    job.state = "failed"
                    job.finished_at = time.time()
                    job.error = error_msg
                    job.message = error_msg
                    self._save_jobs_to_disk()
                return
            
            # Success
            with self._lock:
                job.state = "succeeded"
                job.finished_at = time.time()
                job.output_path = output_path
                job.message = f"Audio-video synchronization completed successfully"
                self._save_jobs_to_disk()
            
            self.logger.info(f"Sync job {job_id} completed successfully: {output_path}")
            
        except Exception as e:
            error_msg = f"Unexpected error during synchronization: {str(e)}"
            self.logger.error(f"Sync job {job_id} failed: {error_msg}", exc_info=True)
            with self._lock:
                job = self._jobs.get(job_id)
                if job:
                    job.state = "failed"
                    job.finished_at = time.time()
                    job.error = error_msg
                    job.message = f"Synchronization failed: {error_msg[:100]}"
                    self._save_jobs_to_disk()
    
    def _build_ffmpeg_command(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        sync_mode: AudioVideoSyncMode,
        video_duration: float,
        audio_duration: float,
        audio_volume: float,
        replace_existing_audio: bool,
    ) -> list[str]:
        """Build ffmpeg command for audio-video synchronization.
        
        Args:
            video_path: Path to input video file
            audio_path: Path to input audio file
            output_path: Path to output synchronized video file
            sync_mode: Synchronization mode
            video_duration: Video duration in seconds
            audio_duration: Audio duration in seconds
            audio_volume: Audio volume multiplier
            replace_existing_audio: Whether to replace existing audio
            
        Returns:
            List of command arguments for subprocess.run
        """
        cmd = ["ffmpeg", "-y"]  # -y to overwrite output file
        
        # Input video
        cmd.extend(["-i", video_path])
        
        # Input audio with volume filter
        if audio_volume != 1.0:
            cmd.extend(["-i", audio_path, "-filter_complex"])
            filter_complex = f"[1:a]volume={audio_volume}[a1]"
            
            # Handle sync mode
            if sync_mode == AudioVideoSyncMode.LOOP_AUDIO:
                # Loop audio to match video duration
                if audio_duration < video_duration:
                    loops = int(video_duration / audio_duration) + 1
                    filter_complex = f"[1:a]aloop=loop={loops}:size=2e+09,volume={audio_volume}[a1]"
                else:
                    filter_complex = f"[1:a]volume={audio_volume}[a1]"
            elif sync_mode == AudioVideoSyncMode.STRETCH_AUDIO:
                # Stretch/compress audio to match video duration
                if audio_duration > 0:
                    tempo = video_duration / audio_duration
                    filter_complex = f"[1:a]atempo={tempo:.3f},volume={audio_volume}[a1]"
                else:
                    filter_complex = f"[1:a]volume={audio_volume}[a1]"
            else:
                filter_complex = f"[1:a]volume={audio_volume}[a1]"
            
            # Mix or replace audio
            if sync_mode == AudioVideoSyncMode.MIX and not replace_existing_audio:
                filter_complex += ";[0:a][a1]amix=inputs=2:duration=longest:dropout_transition=2[aout]"
            else:
                # Replace audio (default)
                filter_complex += ";[a1]apad=pad_dur={video_duration}[aout]".format(
                    video_duration=video_duration
                )
            
            cmd.append(filter_complex)
            cmd.extend(["-map", "0:v", "-map", "[aout]"])
        else:
            # Simple audio replacement without volume adjustment
            cmd.extend(["-i", audio_path])
            
            if sync_mode == AudioVideoSyncMode.LOOP_AUDIO:
                # Loop audio to match video duration
                if audio_duration < video_duration:
                    loops = int(video_duration / audio_duration) + 1
                    cmd.extend(["-filter_complex", f"[1:a]aloop=loop={loops}:size=2e+09[a1]"])
                    cmd.extend(["-map", "0:v", "-map", "[a1]"])
                else:
                    cmd.extend(["-map", "0:v", "-map", "1:a"])
            elif sync_mode == AudioVideoSyncMode.STRETCH_AUDIO:
                # Stretch/compress audio to match video duration
                if audio_duration > 0:
                    tempo = video_duration / audio_duration
                    cmd.extend(["-filter_complex", f"[1:a]atempo={tempo:.3f}[a1]"])
                    cmd.extend(["-map", "0:v", "-map", "[a1]"])
                else:
                    cmd.extend(["-map", "0:v", "-map", "1:a"])
            elif sync_mode == AudioVideoSyncMode.MIX and not replace_existing_audio:
                cmd.extend(["-filter_complex", "[0:a][1:a]amix=inputs=2:duration=longest:dropout_transition=2[aout]"])
                cmd.extend(["-map", "0:v", "-map", "[aout]"])
            else:
                # Replace audio (default)
                cmd.extend(["-map", "0:v", "-map", "1:a"])
        
        # Trim audio if needed (trim_audio mode)
        if sync_mode == AudioVideoSyncMode.TRIM_AUDIO and audio_duration > video_duration:
            # Audio will be trimmed to video duration by default with -shortest
            cmd.append("-shortest")
        
        # Codec settings for output
        cmd.extend(["-c:v", "copy"])  # Copy video codec (no re-encoding)
        cmd.append("-c:a")  # Audio codec
        cmd.append("aac")  # Use AAC codec for compatibility
        cmd.append("-b:a")  # Audio bitrate
        cmd.append("192k")  # 192 kbps audio bitrate
        
        # Output file
        cmd.append(output_path)
        
        return cmd
    
    def get_job_status(self, job_id: str) -> dict[str, Any]:
        """Get the status of an audio-video synchronization job.
        
        Args:
            job_id: Unique identifier for the sync job
            
        Returns:
            Dictionary with job status and metadata
        """
        with self._lock:
            job = self._jobs.get(job_id)
        
        if not job:
            return {
                "status": "not_found",
                "message": f"Audio-video sync job '{job_id}' not found",
            }
        
        return {
            "id": job.id,
            "status": job.state,
            "message": job.message,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
            "output_path": job.output_path,
            "error": job.error,
            "params": job.params,
        }
    
    def list_jobs(self, limit: int = 100) -> list[dict[str, Any]]:
        """List recent audio-video synchronization jobs.
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of job dictionaries sorted by creation time (newest first)
        """
        with self._lock:
            jobs = sorted(
                self._jobs.values(),
                key=lambda j: j.created_at,
                reverse=True,
            )[:limit]
        
        return [
            {
                "id": job.id,
                "status": job.state,
                "message": job.message,
                "created_at": job.created_at,
                "output_path": job.output_path,
                "sync_mode": job.params.get("sync_mode") if job.params else None,
            }
            for job in jobs
        ]
    
    def request_cancel(self, job_id: str) -> bool:
        """Request cancellation of an audio-video synchronization job.
        
        Args:
            job_id: Unique identifier for the sync job to cancel
            
        Returns:
            True if cancellation was requested, False if job not found
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            if job.state in ("queued", "running"):
                job.cancel_requested = True
                job.state = "cancelled"
                job.cancelled_at = time.time()
                job.message = "Cancellation requested"
                self._save_jobs_to_disk()
                return True
        
        return False
    
    def health_check(self) -> dict[str, Any]:
        """Check the health status of the audio-video synchronization service.
        
        Returns:
            Dictionary with health status information
        """
        ffmpeg_available = self._check_ffmpeg_available()
        
        with self._lock:
            total_jobs = len(self._jobs)
            queued_jobs = sum(1 for j in self._jobs.values() if j.state == "queued")
            running_jobs = sum(1 for j in self._jobs.values() if j.state == "running")
            succeeded_jobs = sum(1 for j in self._jobs.values() if j.state == "succeeded")
            failed_jobs = sum(1 for j in self._jobs.values() if j.state == "failed")
        
        return {
            "status": "healthy" if ffmpeg_available else "degraded",
            "ffmpeg_available": ffmpeg_available,
            "total_jobs": total_jobs,
            "queued_jobs": queued_jobs,
            "running_jobs": running_jobs,
            "succeeded_jobs": succeeded_jobs,
            "failed_jobs": failed_jobs,
        }


# Singleton instance
audio_video_sync_service = AudioVideoSyncService()

