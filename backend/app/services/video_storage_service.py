"""Video storage and management service.

This service provides video file storage, organization, and management functionality.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.core.paths import thumbnails_dir, videos_dir

logger = get_logger(__name__)


class VideoStorageService:
    """Service for managing video file storage and organization."""
    
    def __init__(self):
        """Initialize the video storage service."""
        self.logger = get_logger(__name__)
        videos_dir().mkdir(parents=True, exist_ok=True)
    
    def list_videos(
        self,
        *,
        q: str | None = None,
        sort: str = "newest",
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        List stored video files with optional search and sorting.
        
        Args:
            q: Optional search query to filter video filenames
            sort: Sort order: 'newest', 'oldest', or 'name' (default: 'newest')
            limit: Maximum number of videos to return (default: 50)
            offset: Number of videos to skip (default: 0)
            
        Returns:
            Dictionary with items list, total count, and pagination info
        """
        root = videos_dir()
        if not root.exists():
            return {"items": [], "total": 0, "limit": limit, "offset": offset, "sort": sort, "q": q}
        
        # Find all video files
        video_extensions = {".mp4", ".webm", ".mov", ".avi", ".mkv", ".flv", ".m4v"}
        paths: list[Path] = []
        for ext in video_extensions:
            paths.extend(root.glob(f"*{ext}"))
        
        # Filter by search query
        query = q.lower() if q else None
        if query:
            paths = [p for p in paths if query in p.name.lower()]
        
        # Sort
        if sort == "newest":
            paths.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        elif sort == "oldest":
            paths.sort(key=lambda p: p.stat().st_mtime)
        elif sort == "name":
            paths.sort(key=lambda p: p.name.lower())
        
        total = len(paths)
        page = paths[offset : offset + limit]
        
        items: list[dict[str, Any]] = []
        thumb_dir = thumbnails_dir()
        for p in page:
            try:
                st = p.stat()
                # Check if thumbnail exists
                thumb_filename = f"{p.stem}.jpg"
                thumb_path = thumb_dir / thumb_filename
                thumbnail_url = None
                if thumb_path.exists():
                    thumbnail_url = f"/content/thumbnails/{thumb_filename}"
                
                items.append({
                    "filename": p.name,
                    "size_bytes": st.st_size,
                    "size_mb": round(st.st_size / (1024 * 1024), 2),
                    "created_at": datetime.fromtimestamp(st.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(st.st_mtime).isoformat(),
                    "url": f"/content/videos/{p.name}",
                    "thumbnail_url": thumbnail_url,
                })
            except (FileNotFoundError, OSError):
                continue
        
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "sort": sort,
            "q": query,
        }
    
    def storage_stats(self) -> dict[str, Any]:
        """
        Get storage statistics for stored videos.
        
        Returns:
            Dictionary with videos_count and videos_bytes
        """
        root = videos_dir()
        if not root.exists():
            return {"videos_count": 0, "videos_bytes": 0}
        
        total = 0
        count = 0
        video_extensions = {".mp4", ".webm", ".mov", ".avi", ".mkv", ".flv", ".m4v"}
        
        for ext in video_extensions:
            for p in root.glob(f"*{ext}"):
                try:
                    st = p.stat()
                    total += st.st_size
                    count += 1
                except (FileNotFoundError, OSError):
                    continue
        
        return {"videos_count": count, "videos_bytes": total}
    
    def delete_video(self, filename: str) -> bool:
        """
        Delete a video file.
        
        Args:
            filename: Name of the video file to delete
            
        Returns:
            True if video was deleted, False if not found
        """
        # Security: prevent directory traversal
        if "/" in filename or "\\" in filename or ".." in filename:
            self.logger.warning(f"Invalid filename for deletion: {filename}")
            return False
        
        video_path = videos_dir() / filename
        if not video_path.exists():
            return False
        
        try:
            video_path.unlink()
            self.logger.info(f"Deleted video: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete video {filename}: {e}")
            return False
    
    def bulk_delete_videos(self, filenames: list[str]) -> dict[str, Any]:
        """
        Delete multiple video files.
        
        Args:
            filenames: List of video filenames to delete
            
        Returns:
            Dictionary with deleted count and skipped count
        """
        deleted = 0
        skipped = 0
        
        for filename in filenames:
            if self.delete_video(filename):
                deleted += 1
            else:
                skipped += 1
        
        return {
            "deleted": deleted,
            "skipped": skipped,
            "total_requested": len(filenames),
        }
    
    def cleanup_old_videos(self, older_than_days: int = 30) -> dict[str, Any]:
        """
        Delete videos older than specified number of days.
        
        Args:
            older_than_days: Delete videos older than this many days (default: 30)
            
        Returns:
            Dictionary with deleted count and skipped count
        """
        import time
        
        root = videos_dir()
        if not root.exists():
            return {"deleted": 0, "skipped": 0, "older_than_days": older_than_days}
        
        cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)
        video_extensions = {".mp4", ".webm", ".mov", ".avi", ".mkv", ".flv", ".m4v"}
        
        deleted = 0
        skipped = 0
        
        for ext in video_extensions:
            for p in root.glob(f"*{ext}"):
                try:
                    if p.stat().st_mtime < cutoff_time:
                        p.unlink()
                        deleted += 1
                    else:
                        skipped += 1
                except (FileNotFoundError, OSError):
                    skipped += 1
                except Exception as e:
                    self.logger.error(f"Failed to delete old video {p.name}: {e}")
                    skipped += 1
        
        return {
            "deleted": deleted,
            "skipped": skipped,
            "older_than_days": older_than_days,
        }

