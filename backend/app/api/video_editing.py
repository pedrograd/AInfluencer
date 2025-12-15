"""Video editing API endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.video_editing_service import (
    VideoEditingOperation,
    VideoEditingService,
)

router = APIRouter()
video_editing_service = VideoEditingService()


class EditVideoRequest(BaseModel):
    """Request model for video editing operations.
    
    Supports basic video editing operations including trimming, text overlays,
    concatenation, format conversion, and more.
    """
    
    operation: str = Field(..., description="Editing operation: 'trim', 'text_overlay', 'concatenate', 'convert_format', 'add_audio', 'crop', 'resize'")
    input_path: str = Field(..., description="Path to the input video file")
    output_path: str | None = Field(default=None, description="Optional path for the output video file")
    # Operation-specific parameters (will be passed as kwargs)
    start_time: float | None = Field(default=None, description="Start time in seconds (for trim operation)")
    end_time: float | None = Field(default=None, description="End time in seconds (for trim operation)")
    text: str | None = Field(default=None, description="Text to overlay (for text_overlay operation)")
    position: str | None = Field(default=None, description="Text position: 'top', 'center', 'bottom' (for text_overlay operation)")
    video_paths: list[str] | None = Field(default=None, description="List of video paths to concatenate (for concatenate operation)")
    target_format: str | None = Field(default=None, description="Target format: 'mp4', 'webm', etc. (for convert_format operation)")
    audio_path: str | None = Field(default=None, description="Path to audio file (for add_audio operation)")
    width: int | None = Field(default=None, description="Target width in pixels (for resize/crop operations)")
    height: int | None = Field(default=None, description="Target height in pixels (for resize/crop operations)")
    x: int | None = Field(default=None, description="Crop X position (for crop operation)")
    y: int | None = Field(default=None, description="Crop Y position (for crop operation)")


@router.post("/edit")
def edit_video(req: EditVideoRequest) -> dict:
    """
    Create a video editing job.
    
    Creates a video editing job for the specified operation. The job is queued
    and processed asynchronously.
    
    Args:
        req: Video editing request with operation type and parameters
        
    Returns:
        dict: Job information including job_id and status.
            On success: {"ok": True, "job_id": str, "status": str, "message": str}
            On error: {"ok": False, "error": str, "message": str}
    """
    try:
        # Validate operation
        try:
            operation = VideoEditingOperation(req.operation.lower())
        except ValueError:
            return {
                "ok": False,
                "error": "invalid_operation",
                "message": f"Invalid operation '{req.operation}'. Must be one of: trim, text_overlay, concatenate, convert_format, add_audio, crop, resize",
            }
        
        # Build operation-specific parameters
        params = {}
        if req.start_time is not None:
            params["start_time"] = req.start_time
        if req.end_time is not None:
            params["end_time"] = req.end_time
        if req.text is not None:
            params["text"] = req.text
        if req.position is not None:
            params["position"] = req.position
        if req.video_paths is not None:
            params["video_paths"] = req.video_paths
        if req.target_format is not None:
            params["target_format"] = req.target_format
        if req.audio_path is not None:
            params["audio_path"] = req.audio_path
        if req.width is not None:
            params["width"] = req.width
        if req.height is not None:
            params["height"] = req.height
        if req.x is not None:
            params["x"] = req.x
        if req.y is not None:
            params["y"] = req.y
        
        # Create editing job
        result = video_editing_service.edit_video(
            operation=operation,
            input_path=req.input_path,
            output_path=req.output_path,
            **params,
        )
        
        return {
            "ok": True,
            "job_id": result.get("job_id", "pending"),
            "status": result.get("status", "pending"),
            "operation": result.get("operation"),
            "message": result.get("message", "Video editing job created"),
        }
    except Exception as e:
        return {
            "ok": False,
            "error": "editing_failed",
            "message": f"Failed to create video editing job: {str(e)}",
        }


@router.get("/edit/{job_id}")
def get_editing_job(job_id: str) -> dict:
    """
    Get the status of a video editing job.
    
    Returns the current status and metadata for a video editing job.
    
    Args:
        job_id: Unique identifier for the editing job
        
    Returns:
        dict: Job information including status and metadata.
            On success: {"ok": True, "job": {...}}
            On not found: {"ok": False, "error": "not_found"}
    """
    status = video_editing_service.get_job_status(job_id)
    
    if status.get("status") == "not_found":
        return {
            "ok": False,
            "error": "not_found",
            "message": f"Video editing job '{job_id}' not found",
        }
    
    return {
        "ok": True,
        "job": status,
    }


@router.get("/edit/jobs")
def list_editing_jobs() -> dict:
    """
    List recent video editing jobs.
    
    Returns a list of the most recent video editing jobs.
    
    Returns:
        dict: List of job items with their status and metadata
    """
    jobs = video_editing_service.list_jobs(limit=100)
    return {
        "items": jobs,
        "total": len(jobs),
    }


@router.post("/edit/{job_id}/cancel")
def cancel_editing_job(job_id: str) -> dict:
    """
    Cancel a running video editing job.
    
    Requests cancellation of an in-progress video editing job.
    The job may not cancel immediately if editing has already started.
    
    Args:
        job_id: Unique identifier for the editing job to cancel
        
    Returns:
        dict: Success status of the cancel request
    """
    cancelled = video_editing_service.request_cancel(job_id)
    if not cancelled:
        return {
            "ok": False,
            "error": "not_found",
            "message": f"Video editing job '{job_id}' not found or cannot be cancelled",
        }
    
    return {
        "ok": True,
        "job_id": job_id,
        "message": "Cancellation requested for video editing job",
    }


@router.get("/edit/health")
def get_video_editing_health() -> dict:
    """
    Check video editing service health.
    
    Returns the health status of the video editing service.
    
    Returns:
        dict: Health status information
    """
    health = video_editing_service.health_check()
    return {
        "ok": True,
        **health,
    }

