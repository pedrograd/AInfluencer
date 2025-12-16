"""Audio-video synchronization API endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.audio_video_sync_service import (
    AudioVideoSyncMode,
    audio_video_sync_service,
)

router = APIRouter()


class SyncAudioVideoRequest(BaseModel):
    """Request model for audio-video synchronization.
    
    Synchronizes generated audio with video files, ensuring proper timing,
    duration matching, and audio-video alignment.
    """
    
    video_path: str = Field(..., description="Path to the input video file")
    audio_path: str = Field(..., description="Path to the input audio file")
    output_path: str | None = Field(default=None, description="Optional path for the output synchronized video file")
    sync_mode: str = Field(
        default="replace",
        description="Synchronization mode: 'replace', 'mix', 'loop_audio', 'trim_audio', 'stretch_audio'"
    )
    audio_volume: float = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="Audio volume multiplier (0.0 to 2.0, default: 1.0)"
    )
    replace_existing_audio: bool = Field(
        default=True,
        description="Whether to replace existing audio track (default: True)"
    )


@router.post("/sync")
def sync_audio_video(req: SyncAudioVideoRequest) -> dict:
    """
    Synchronize audio with video file.
    
    Creates an audio-video synchronization job that aligns audio with video,
    matching duration and ensuring proper timing.
    
    Args:
        req: Audio-video synchronization request with video and audio paths
        
    Returns:
        dict: Job information including job_id and status.
            On success: {"ok": True, "job_id": str, "status": str, "output_path": str}
            On error: {"ok": False, "error": str, "message": str}
    """
    try:
        # Validate sync mode
        try:
            sync_mode = AudioVideoSyncMode(req.sync_mode.lower())
        except ValueError:
            return {
                "ok": False,
                "error": "invalid_sync_mode",
                "message": (
                    f"Invalid sync mode '{req.sync_mode}'. "
                    "Must be one of: replace, mix, loop_audio, trim_audio, stretch_audio"
                ),
            }
        
        # Create synchronization job
        result = audio_video_sync_service.sync_audio_video(
            video_path=req.video_path,
            audio_path=req.audio_path,
            output_path=req.output_path,
            sync_mode=sync_mode,
            audio_volume=req.audio_volume,
            replace_existing_audio=req.replace_existing_audio,
        )
        
        return {
            "ok": True,
            "job_id": result.get("job_id", "pending"),
            "status": result.get("status", "pending"),
            "output_path": result.get("output_path"),
            "message": result.get("message", "Audio-video synchronization job created"),
        }
    except ValueError as e:
        return {
            "ok": False,
            "error": "validation_error",
            "message": str(e),
        }
    except RuntimeError as e:
        return {
            "ok": False,
            "error": "runtime_error",
            "message": str(e),
        }
    except Exception as e:
        return {
            "ok": False,
            "error": "sync_failed",
            "message": f"Failed to create audio-video synchronization job: {str(e)}",
        }


@router.get("/sync/{job_id}")
def get_sync_job(job_id: str) -> dict:
    """
    Get the status of an audio-video synchronization job.
    
    Returns the current status and metadata for an audio-video synchronization job.
    
    Args:
        job_id: Unique identifier for the sync job
        
    Returns:
        dict: Job information including status and metadata.
            On success: {"ok": True, "job": {...}}
            On not found: {"ok": False, "error": "not_found"}
    """
    status = audio_video_sync_service.get_job_status(job_id)
    
    if status.get("status") == "not_found":
        return {
            "ok": False,
            "error": "not_found",
            "message": f"Audio-video sync job '{job_id}' not found",
        }
    
    return {
        "ok": True,
        "job": status,
    }


@router.get("/sync/jobs")
def list_sync_jobs() -> dict:
    """
    List recent audio-video synchronization jobs.
    
    Returns a list of the most recent audio-video synchronization jobs.
    
    Returns:
        dict: List of job items with their status and metadata
    """
    jobs = audio_video_sync_service.list_jobs(limit=100)
    return {
        "items": jobs,
        "total": len(jobs),
    }


@router.post("/sync/{job_id}/cancel")
def cancel_sync_job(job_id: str) -> dict:
    """
    Cancel a running audio-video synchronization job.
    
    Requests cancellation of an in-progress audio-video synchronization job.
    The job may not cancel immediately if synchronization has already started.
    
    Args:
        job_id: Unique identifier for the sync job to cancel
        
    Returns:
        dict: Success status of the cancel request
    """
    cancelled = audio_video_sync_service.request_cancel(job_id)
    if not cancelled:
        return {
            "ok": False,
            "error": "not_found",
            "message": f"Audio-video sync job '{job_id}' not found or cannot be cancelled",
        }
    
    return {
        "ok": True,
        "job_id": job_id,
        "message": "Cancellation requested for audio-video synchronization job",
    }


@router.get("/sync/health")
def get_sync_health() -> dict:
    """
    Check audio-video synchronization service health.
    
    Returns the health status of the audio-video synchronization service,
    including ffmpeg availability.
    
    Returns:
        dict: Health status information
    """
    health = audio_video_sync_service.health_check()
    return {
        "ok": health.get("status") in ("healthy", "degraded"),
        **health,
    }

