"""Video storage and management API endpoints."""

from __future__ import annotations

from __future__ import annotations

import io
import zipfile
from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.paths import videos_dir
from app.services.video_storage_service import VideoStorageService

router = APIRouter()
video_storage_service = VideoStorageService()


@router.get("/videos")
def list_videos(
    q: str | None = Query(default=None, description="Search query to filter video filenames"),
    sort: str = Query(default="newest", pattern="^(newest|oldest|name)$", description="Sort order: newest, oldest, or name"),
    limit: int = Query(default=50, ge=1, le=500, description="Maximum number of videos to return"),
    offset: int = Query(default=0, ge=0, description="Number of videos to skip"),
) -> dict:
    """
    List stored video files with optional search and sorting.
    
    Returns a paginated list of video files with metadata.
    
    Args:
        q: Optional search query to filter video filenames
        sort: Sort order: 'newest', 'oldest', or 'name'
        limit: Maximum number of videos to return (1-500)
        offset: Number of videos to skip
        
    Returns:
        dict: Paginated list of videos with metadata
    """
    return video_storage_service.list_videos(q=q, sort=sort, limit=limit, offset=offset)


@router.get("/videos/storage")
def get_video_storage_stats() -> dict:
    """
    Get storage statistics for stored videos.
    
    Returns:
        dict: Storage statistics including videos_count and videos_bytes
    """
    return video_storage_service.storage_stats()


@router.delete("/videos/{filename}")
def delete_video(filename: str) -> dict:
    """
    Delete a video file.
    
    Args:
        filename: Name of the video file to delete
        
    Returns:
        dict: Success status
    """
    deleted = video_storage_service.delete_video(filename)
    if not deleted:
        return {
            "ok": False,
            "error": "not_found",
            "message": f"Video file '{filename}' not found",
        }
    
    return {"ok": True, "message": f"Video '{filename}' deleted"}


class BulkDeleteRequest(BaseModel):
    """Request model for bulk video deletion."""
    
    filenames: list[str] = Field(default_factory=list, max_length=5000, description="List of video filenames to delete")


@router.post("/videos/bulk-delete")
def bulk_delete_videos(req: BulkDeleteRequest) -> dict:
    """
    Delete multiple video files.
    
    Args:
        req: Bulk delete request with list of filenames
        
    Returns:
        dict: Deletion results with counts
    """
    result = video_storage_service.bulk_delete_videos(req.filenames)
    return {
        "ok": True,
        **result,
    }


class CleanupRequest(BaseModel):
    """Request model for cleaning up old videos."""
    
    older_than_days: int = Field(default=30, ge=1, le=3650, description="Delete videos older than this many days")


@router.post("/videos/cleanup")
def cleanup_videos(req: CleanupRequest) -> dict:
    """
    Delete videos older than specified number of days.
    
    Args:
        req: Cleanup request with older_than_days parameter
        
    Returns:
        dict: Cleanup results with counts
    """
    result = video_storage_service.cleanup_old_videos(req.older_than_days)
    return {
        "ok": True,
        **result,
    }


@router.get("/videos/download-all")
def download_all_videos() -> StreamingResponse:
    """
    Download all videos as a ZIP archive.
    
    Returns:
        StreamingResponse: ZIP file containing all videos
    """
    root = videos_dir()
    if not root.exists():
        # Return empty zip
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            pass
        zip_buffer.seek(0)
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=videos.zip"},
        )
    
    video_extensions = {".mp4", ".webm", ".mov", ".avi", ".mkv", ".flv", ".m4v"}
    video_files: list[Path] = []
    for ext in video_extensions:
        video_files.extend(root.glob(f"*{ext}"))
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for video_file in video_files:
            try:
                zip_file.write(video_file, video_file.name)
            except Exception:
                continue
    
    zip_buffer.seek(0)
    return StreamingResponse(
        io.BytesIO(zip_buffer.read()),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=videos.zip"},
    )

