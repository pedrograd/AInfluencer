"""Content management API endpoints for images, library, and caption generation.

This module provides API endpoints for content management operations including:
- Image listing, deletion, bulk operations, and cleanup
- Content library management (CRUD, filtering, search, batch operations)
- Content validation and quality checking
- Caption generation for images with character personality integration
"""

from __future__ import annotations

import io
import json
import os
import time
import zipfile
from datetime import datetime
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.paths import images_dir
from app.models.content import Content
from app.services.content_service import ContentService
from app.services.generation_service import generation_service
from app.services.quality_validator import quality_validator
from app.services.caption_generation_service import (
    CaptionGenerationRequest,
    caption_generation_service,
)

router = APIRouter()


@router.get("/images")
def list_images(
    q: str | None = None,
    sort: str = Query(default="newest", pattern="^(newest|oldest|name)$"),
    limit: int = Query(default=48, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    """List generated images with optional filtering, sorting, and pagination.
    
    Args:
        q: Optional search query string to filter images by filename or metadata.
        sort: Sort order - "newest" (default), "oldest", or "name" (alphabetical).
        limit: Maximum number of images to return (1-500, default: 48).
        offset: Number of images to skip for pagination (default: 0).
    
    Returns:
        dict: Response containing:
            - items: List of image objects with metadata (path, filename, size, created_at, etc.)
            - total: Total number of images matching the query
            - limit: Applied limit value
            - offset: Applied offset value
            - sort: Applied sort order
            - q: Applied search query (if any)
    
    Example:
        ```json
        {
            "items": [
                {
                    "path": "image_001.png",
                    "filename": "image_001.png",
                    "size": 1024000,
                    "created_at": "2025-01-15T10:00:00Z"
                }
            ],
            "total": 150,
            "limit": 48,
            "offset": 0,
            "sort": "newest",
            "q": null
        }
        ```
    """
    return generation_service.list_images(q=q, sort=sort, limit=limit, offset=offset)


@router.delete("/images/{filename}")
def delete_image(filename: str) -> dict:
    """Delete a single image file by filename.
    
    Args:
        filename: Name of the image file to delete (must be a PNG file).
    
    Returns:
        dict: Response containing:
            - ok: True if deletion succeeded, False otherwise
            - error: Error code if deletion failed ("invalid_filename" or "not_found")
    
    Security:
        - Only allows deletion of PNG files in the images directory
        - Prevents path traversal attacks by rejecting filenames with slashes
        - Validates filename format before deletion
    
    Raises:
        HTTPException: Not raised directly, but returns error in response dict
    
    Example:
        ```json
        {
            "ok": true
        }
        ```
        
        Or on error:
        ```json
        {
            "ok": false,
            "error": "not_found"
        }
        ```
    """
    # Basic safety: only allow deleting pngs in our images directory
    if "/" in filename or "\\" in filename or not filename.endswith(".png"):
        return {"ok": False, "error": "invalid_filename"}
    p = images_dir() / filename
    if not p.exists():
        return {"ok": False, "error": "not_found"}
    try:
        p.unlink()
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}
    return {"ok": True}


class BulkDeleteRequest(BaseModel):
    """Request model for bulk deletion of image files."""

    filenames: list[str] = Field(default_factory=list, max_length=5000)


@router.post("/images/delete")
def bulk_delete_images(req: BulkDeleteRequest) -> dict:
    """Bulk delete multiple image files.
    
    Args:
        req: BulkDeleteRequest containing list of filenames to delete (max 5000).
    
    Returns:
        dict: Response containing:
            - ok: True if operation completed (even if some files failed)
            - deleted: Number of files successfully deleted
            - skipped: Number of files skipped (invalid filename, not found, or error)
    
    Security:
        - Only processes up to 5000 filenames (additional filenames are ignored)
        - Validates each filename (must be PNG, no path traversal)
        - Skips invalid filenames instead of failing entire operation
    
    Example:
        ```json
        {
            "ok": true,
            "deleted": 45,
            "skipped": 5
        }
        ```
    """
    deleted = 0
    skipped = 0
    for filename in req.filenames[:5000]:
        if "/" in filename or "\\" in filename or not filename.endswith(".png"):
            skipped += 1
            continue
        p = images_dir() / filename
        try:
            p.unlink()
            deleted += 1
        except FileNotFoundError:
            skipped += 1
        except Exception:
            skipped += 1
    return {"ok": True, "deleted": deleted, "skipped": skipped}


class CleanupRequest(BaseModel):
    """Request model for cleaning up old image files."""

    older_than_days: int = Field(default=30, ge=1, le=3650)


@router.post("/images/cleanup")
def cleanup_images(req: CleanupRequest) -> dict:
    """Clean up old image files based on age.
    
    Args:
        req: CleanupRequest containing older_than_days (1-3650, default: 30).
    
    Returns:
        dict: Response containing:
            - ok: True if cleanup completed
            - deleted: Number of files successfully deleted
            - skipped: Number of files skipped (errors during deletion)
            - older_than_days: Applied age threshold in days
    
    Note:
        Deletes all PNG files in the images directory that are older than the
        specified number of days. Useful for freeing up disk space by removing
        old generated images. Uses file modification time (mtime) to determine age.
    
    Example:
        ```json
        {
            "ok": true,
            "deleted": 120,
            "skipped": 2,
            "older_than_days": 30
        }
        ```
    """
    cutoff = time.time() - (req.older_than_days * 86400)
    deleted = 0
    skipped = 0
    for p in images_dir().glob("*.png"):
        try:
            if p.stat().st_mtime < cutoff:
                p.unlink()
                deleted += 1
        except FileNotFoundError:
            skipped += 1
        except Exception:
            skipped += 1
    return {"ok": True, "deleted": deleted, "skipped": skipped, "older_than_days": req.older_than_days}


@router.get("/images/download")
def download_all_images():
    """Download all generated images as a ZIP archive.
    
    Returns:
        StreamingResponse: ZIP file stream with:
            - All generated PNG images in "images/" directory
            - manifest.json file listing all included files with metadata
    
    Content-Type:
        application/zip
    
    Headers:
        Content-Disposition: attachment; filename="ainfluencer-gallery.zip"
    
    Note:
        Creates a ZIP file containing all generated images along with a manifest.json
        file listing all included files. Useful for backing up or exporting the entire
        image gallery. The manifest.json includes count and list of all file paths.
    
    Example manifest.json structure:
        ```json
        {
            "count": 150,
            "files": [
                "image_001.png",
                "image_002.png"
            ]
        }
        ```
    """
    res = generation_service.list_images(q=None, sort="newest", limit=100000, offset=0)
    items = res.get("items") if isinstance(res, dict) else []
    files = [it["path"] for it in items if isinstance(it, dict) and isinstance(it.get("path"), str)]

    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps({"count": len(files), "files": files}, indent=2, sort_keys=True))
        for name in files:
            p = images_dir() / name
            if p.exists():
                zf.write(p, arcname=f"images/{name}")

    mem.seek(0)
    headers = {"Content-Disposition": 'attachment; filename="ainfluencer-gallery.zip"'}
    return StreamingResponse(mem, media_type="application/zip", headers=headers)


class ValidateContentRequest(BaseModel):
    """Request model for content quality validation."""

    file_path: str = Field(..., description="Path to content file to validate")


@router.post("/validate")
def validate_content(req: ValidateContentRequest) -> dict:
    """Validate content quality.
    
    Args:
        req: ValidateContentRequest containing file_path to the content file.
    
    Returns:
        dict: Validation result containing:
            - ok: True if content is valid, False otherwise
            - quality_score: Quality score from 0.0 to 1.0 (higher is better)
            - is_valid: Boolean indicating if content passes all validation checks
            - checks_passed: List of validation checks that passed
            - checks_failed: List of validation checks that failed
            - warnings: List of warning messages
            - errors: List of error messages
            - metadata: Additional metadata about the content (dimensions, format, etc.)
    
    Note:
        Validates the quality of generated content (images, videos, etc.)
        using the quality validator service. Checks include file format, dimensions,
        file size, and other quality metrics.
    
    Example:
        ```json
        {
            "ok": true,
            "quality_score": 0.85,
            "is_valid": true,
            "checks_passed": ["format", "dimensions", "file_size"],
            "checks_failed": [],
            "warnings": [],
            "errors": [],
            "metadata": {
                "width": 1024,
                "height": 1024,
                "format": "PNG"
            }
        }
        ```
    """
    result = quality_validator.validate_content(file_path=req.file_path)

    return {
        "ok": result.is_valid,
        "quality_score": float(result.quality_score) if result.quality_score else None,
        "is_valid": result.is_valid,
        "checks_passed": result.checks_passed,
        "checks_failed": result.checks_failed,
        "warnings": result.warnings,
        "errors": result.errors,
        "metadata": result.metadata,
    }


@router.post("/validate/{content_id}")
def validate_content_by_id(content_id: str) -> dict:
    """Validate content quality by content ID.
    
    Args:
        content_id: UUID of the content item to validate.
    
    Returns:
        dict: Error response indicating this endpoint is not yet implemented.
    
    Note:
        This endpoint is planned for future implementation. Currently, content
        validation requires file_path. Database integration will be added in a
        future update to allow validation by content ID.
    
    Example:
        ```json
        {
            "ok": false,
            "error": "content_id validation not yet implemented. Use POST /content/validate with file_path."
        }
        ```
    """
    return {
        "ok": False,
        "error": "content_id validation not yet implemented. Use POST /content/validate with file_path.",
    }


class GenerateCaptionRequest(BaseModel):
    """Request model for generating captions for images with character persona."""

    character_id: str = Field(..., description="Character ID for persona-based caption")
    image_path: str | None = Field(default=None, description="Path to image file")
    content_id: str | None = Field(default=None, description="Content ID (for future database integration)")
    image_description: str | None = Field(default=None, description="Description of the image")
    platform: str = Field(default="instagram", pattern="^(instagram|twitter|facebook|tiktok)$")
    style: str | None = Field(default=None, description="Caption style (extroverted, introverted, professional, casual, creative)")
    include_hashtags: bool = Field(default=True, description="Include hashtags in caption")
    max_length: int | None = Field(default=None, ge=1, le=5000, description="Maximum caption length")


@router.post("/caption")
def generate_caption(req: GenerateCaptionRequest) -> dict:
    """Generate caption for an image with character personality integration.
    
    Args:
        req: GenerateCaptionRequest containing:
            - character_id: Character ID for persona-based caption generation
            - image_path: Optional path to image file
            - content_id: Optional content ID (for future database integration)
            - image_description: Optional description of the image
            - platform: Target platform (instagram, twitter, facebook, tiktok)
            - style: Optional caption style (extroverted, introverted, professional, casual, creative)
            - include_hashtags: Whether to include hashtags (default: True)
            - max_length: Optional maximum caption length (1-5000 characters)
    
    Returns:
        dict: Caption generation result containing:
            - ok: True if generation succeeded, False otherwise
            - caption: Generated caption text (without hashtags)
            - hashtags: List of generated hashtags
            - full_caption: Complete caption with hashtags appended
            - style: Detected or applied caption style
            - platform: Target platform used for generation
            - character_id: Character ID used for persona
            - error: Error message if generation failed
    
    Note:
        Generates a personality-consistent caption for an image using the character's
        persona and the text generation service. Supports multiple platforms with
        platform-specific formatting and hashtag strategies. The caption style is
        auto-detected from character personality if not explicitly provided.
    
    Example:
        ```json
        {
            "ok": true,
            "caption": "Just finished an amazing photoshoot! The lighting was perfect today.",
            "hashtags": ["#photography", "#photoshoot", "#lighting"],
            "full_caption": "Just finished an amazing photoshoot! The lighting was perfect today. #photography #photoshoot #lighting",
            "style": "extroverted",
            "platform": "instagram",
            "character_id": "123e4567-e89b-12d3-a456-426614174000"
        }
        ```
    """
    try:
        # TODO: Load character persona from database
        # For now, we'll use None and let the service use defaults
        character_persona = None

        request = CaptionGenerationRequest(
            character_id=req.character_id,
            image_path=req.image_path,
            content_id=req.content_id,
            image_description=req.image_description,
            platform=req.platform,
            style=req.style,
            include_hashtags=req.include_hashtags,
            max_length=req.max_length,
        )

        result = caption_generation_service.generate_caption(request, character_persona)

        return {
            "ok": True,
            "caption": result.caption,
            "hashtags": result.hashtags,
            "full_caption": result.full_caption,
            "style": result.style,
            "platform": result.platform,
            "character_id": result.character_id,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# Content Library Management Endpoints

@router.get("/library")
async def list_content_library(
    character_id: str | None = Query(default=None, description="Filter by character ID"),
    content_type: str | None = Query(default=None, description="Filter by content type (image, video, text, audio)"),
    content_category: str | None = Query(default=None, description="Filter by content category"),
    approval_status: str | None = Query(default=None, description="Filter by approval status (pending, approved, rejected)"),
    is_approved: bool | None = Query(default=None, description="Filter by approved flag"),
    is_nsfw: bool | None = Query(default=None, description="Filter by NSFW flag"),
    date_from: str | None = Query(default=None, description="Filter by date from (ISO format)"),
    date_to: str | None = Query(default=None, description="Filter by date to (ISO format)"),
    search: str | None = Query(default=None, description="Search in prompt and file path"),
    limit: int = Query(default=50, ge=1, le=500, description="Limit results"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    List content library with filtering, search, and pagination.

    Supports filtering by character, type, category, approval status, date range, and search.
    """
    try:
        service = ContentService(db)

        # Parse date filters
        date_from_dt = None
        date_to_dt = None
        if date_from:
            try:
                date_from_dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_from format. Use ISO format.")
        if date_to:
            try:
                date_to_dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_to format. Use ISO format.")

        # Parse character_id
        character_uuid = None
        if character_id:
            try:
                character_uuid = UUID(character_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid character_id format. Must be UUID.")

        # List content
        content_list, total_count = await service.list_content(
            character_id=character_uuid,
            content_type=content_type,
            content_category=content_category,
            approval_status=approval_status,
            is_approved=is_approved,
            is_nsfw=is_nsfw,
            date_from=date_from_dt,
            date_to=date_to_dt,
            search=search,
            limit=limit,
            offset=offset,
            include_character=True,
        )

        # Serialize content
        items = []
        for content in content_list:
            item = {
                "id": str(content.id),
                "character_id": str(content.character_id),
                "character_name": content.character.name if content.character else None,
                "content_type": content.content_type,
                "content_category": content.content_category,
                "file_url": content.file_url,
                "file_path": content.file_path,
                "thumbnail_url": content.thumbnail_url,
                "thumbnail_path": content.thumbnail_path,
                "file_size": content.file_size,
                "width": content.width,
                "height": content.height,
                "duration": content.duration,
                "mime_type": content.mime_type,
                "prompt": content.prompt,
                "negative_prompt": content.negative_prompt,
                "generation_settings": content.generation_settings,
                "quality_score": float(content.quality_score) if content.quality_score else None,
                "is_approved": content.is_approved,
                "approval_status": content.approval_status,
                "rejection_reason": content.rejection_reason,
                "is_nsfw": content.is_nsfw,
                "times_used": content.times_used,
                "last_used_at": content.last_used_at.isoformat() if content.last_used_at else None,
                "created_at": content.created_at.isoformat() if content.created_at else None,
                "updated_at": content.updated_at.isoformat() if content.updated_at else None,
            }
            items.append(item)

        return {
            "ok": True,
            "items": items,
            "total": total_count,
            "limit": limit,
            "offset": offset,
        }
    except HTTPException:
        raise
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.get("/library/{content_id}")
async def get_content_item(
    content_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get specific content item by ID with full metadata.
    
    Args:
        content_id: UUID of the content item to retrieve.
        db: Database session (injected via dependency).
    
    Returns:
        dict: Response containing:
            - ok: True if content found, False otherwise
            - content: Content object with all metadata including:
                - id, character_id, character_name
                - content_type, content_category
                - file_url, file_path, thumbnail_url, thumbnail_path
                - file_size, width, height, duration, mime_type
                - prompt, negative_prompt, generation_settings
                - quality_score, is_approved, approval_status
                - rejection_reason, is_nsfw
                - times_used, last_used_at
                - created_at, updated_at
    
    Raises:
        HTTPException: 400 if content_id format is invalid, 404 if content not found.
    
    Example:
        ```json
        {
            "ok": true,
            "content": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "character_id": "123e4567-e89b-12d3-a456-426614174001",
                "character_name": "My Character",
                "content_type": "image",
                "file_path": "/path/to/image.png",
                "quality_score": 0.85,
                "is_approved": true
            }
        }
        ```
    """
    try:
        content_uuid = UUID(content_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid content_id format. Must be UUID.")

    service = ContentService(db)
    content = await service.get_content(content_uuid, include_character=True)

    if not content:
        raise HTTPException(status_code=404, detail="Content not found.")

    return {
        "ok": True,
        "content": {
            "id": str(content.id),
            "character_id": str(content.character_id),
            "character_name": content.character.name if content.character else None,
            "content_type": content.content_type,
            "content_category": content.content_category,
            "file_url": content.file_url,
            "file_path": content.file_path,
            "thumbnail_url": content.thumbnail_url,
            "thumbnail_path": content.thumbnail_path,
            "file_size": content.file_size,
            "width": content.width,
            "height": content.height,
            "duration": content.duration,
            "mime_type": content.mime_type,
            "prompt": content.prompt,
            "negative_prompt": content.negative_prompt,
            "generation_settings": content.generation_settings,
            "quality_score": float(content.quality_score) if content.quality_score else None,
            "is_approved": content.is_approved,
            "approval_status": content.approval_status,
            "rejection_reason": content.rejection_reason,
            "is_nsfw": content.is_nsfw,
            "times_used": content.times_used,
            "last_used_at": content.last_used_at.isoformat() if content.last_used_at else None,
            "created_at": content.created_at.isoformat() if content.created_at else None,
            "updated_at": content.updated_at.isoformat() if content.updated_at else None,
        },
    }


@router.get("/library/{content_id}/preview", response_model=None)
async def preview_content(
    content_id: str,
    db: AsyncSession = Depends(get_db),
) -> FileResponse | dict:
    """Preview content file by serving it directly (if file exists on disk).
    
    Args:
        content_id: UUID of the content item to preview.
        db: Database session (injected via dependency).
    
    Returns:
        FileResponse: If file exists, returns the file with appropriate Content-Type.
        dict: If file not found, returns error response with ok=False.
    
    Raises:
        HTTPException: 400 if content_id format is invalid, 404 if content not found in database.
    
    Note:
        Serves the content file directly from disk using the file_path stored in the database.
        Uses the mime_type from the database record, or defaults to "application/octet-stream".
        This endpoint is useful for displaying images, videos, or other content in the browser.
    
    Example:
        Returns the actual file (image, video, etc.) if found, or:
        ```json
        {
            "ok": false,
            "error": "File not found on disk"
        }
        ```
    """
    try:
        content_uuid = UUID(content_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid content_id format. Must be UUID.")

    service = ContentService(db)
    content = await service.get_content(content_uuid, include_character=False)

    if not content:
        raise HTTPException(status_code=404, detail="Content not found.")

    # Try to serve file from file_path
    if content.file_path:
        file_path = Path(content.file_path)
        if file_path.exists() and file_path.is_file():
            return FileResponse(
                path=str(file_path),
                media_type=content.mime_type or "application/octet-stream",
            )

    # If file doesn't exist, return error
    return {"ok": False, "error": "File not found on disk"}


@router.get("/library/{content_id}/download", response_model=None)
async def download_content(
    content_id: str,
    db: AsyncSession = Depends(get_db),
) -> FileResponse | dict:
    """Download content file with proper filename and Content-Disposition header.
    
    Args:
        content_id: UUID of the content item to download.
        db: Database session (injected via dependency).
    
    Returns:
        FileResponse: If file exists, returns the file with download headers and filename.
        dict: If file not found, returns error response with ok=False.
    
    Raises:
        HTTPException: 400 if content_id format is invalid, 404 if content not found in database.
    
    Note:
        Similar to preview endpoint, but sets Content-Disposition header to trigger
        browser download dialog instead of inline display. Uses the original filename
        from the file_path for the download.
    
    Example:
        Returns the actual file with download headers if found, or:
        ```json
        {
            "ok": false,
            "error": "File not found on disk"
        }
        ```
    """
    try:
        content_uuid = UUID(content_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid content_id format. Must be UUID.")

    service = ContentService(db)
    content = await service.get_content(content_uuid, include_character=False)

    if not content:
        raise HTTPException(status_code=404, detail="Content not found.")

    # Try to serve file from file_path
    if content.file_path:
        file_path = Path(content.file_path)
        if file_path.exists() and file_path.is_file():
            filename = file_path.name
            return FileResponse(
                path=str(file_path),
                media_type=content.mime_type or "application/octet-stream",
                filename=filename,
            )

    # If file doesn't exist, return error
    return {"ok": False, "error": "File not found on disk"}


class BatchApproveRequest(BaseModel):
    """Request model for batch approval of content items."""

    content_ids: list[str] = Field(..., description="List of content IDs to approve")


@router.post("/library/batch/approve")
async def batch_approve_content(
    req: BatchApproveRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Batch approve multiple content items in a single operation.
    
    Args:
        req: BatchApproveRequest containing list of content_ids to approve.
        db: Database session (injected via dependency).
    
    Returns:
        dict: Response containing:
            - ok: True if operation completed, False on error
            - approved: Number of content items successfully approved
            - failed: Number of content items that failed (invalid ID or not found)
            - total: Total number of content IDs in request
            - error: Error message if operation failed
    
    Note:
        Sets is_approved=True and approval_status="approved" for all valid content items.
        Invalid UUIDs are counted as failed. Transaction is committed on success, rolled back on error.
    
    Example:
        ```json
        {
            "ok": true,
            "approved": 45,
            "failed": 5,
            "total": 50
        }
        ```
    """
    try:
        content_uuids = []
        for content_id in req.content_ids:
            try:
                content_uuids.append(UUID(content_id))
            except ValueError:
                return {"ok": False, "error": f"Invalid content_id format: {content_id}"}

        service = ContentService(db)
        approved, failed = await service.batch_approve(content_uuids)
        await db.commit()

        return {
            "ok": True,
            "approved": approved,
            "failed": failed,
            "total": len(content_uuids),
        }
    except Exception as exc:
        await db.rollback()
        return {"ok": False, "error": str(exc)}


class BatchRejectRequest(BaseModel):
    """Request model for batch rejection of content items."""

    content_ids: list[str] = Field(..., description="List of content IDs to reject")
    rejection_reason: str | None = Field(default=None, description="Rejection reason")


@router.post("/library/batch/reject")
async def batch_reject_content(
    req: BatchRejectRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Batch reject multiple content items in a single operation.
    
    Args:
        req: BatchRejectRequest containing:
            - content_ids: List of content IDs to reject
            - rejection_reason: Optional reason for rejection
        db: Database session (injected via dependency).
    
    Returns:
        dict: Response containing:
            - ok: True if operation completed, False on error
            - rejected: Number of content items successfully rejected
            - failed: Number of content items that failed (invalid ID or not found)
            - total: Total number of content IDs in request
            - error: Error message if operation failed
    
    Note:
        Sets is_approved=False and approval_status="rejected" for all valid content items.
        Optionally sets rejection_reason if provided. Invalid UUIDs are counted as failed.
        Transaction is committed on success, rolled back on error.
    
    Example:
        ```json
        {
            "ok": true,
            "rejected": 10,
            "failed": 0,
            "total": 10
        }
        ```
    """
    try:
        content_uuids = []
        for content_id in req.content_ids:
            try:
                content_uuids.append(UUID(content_id))
            except ValueError:
                return {"ok": False, "error": f"Invalid content_id format: {content_id}"}

        service = ContentService(db)
        rejected, failed = await service.batch_reject(content_uuids, req.rejection_reason)
        await db.commit()

        return {
            "ok": True,
            "rejected": rejected,
            "failed": failed,
            "total": len(content_uuids),
        }
    except Exception as exc:
        await db.rollback()
        return {"ok": False, "error": str(exc)}


class BatchDeleteRequest(BaseModel):
    """Request model for batch deletion of content items."""

    content_ids: list[str] = Field(..., description="List of content IDs to delete")
    hard_delete: bool = Field(default=False, description="Hard delete (permanent) vs soft delete")


@router.post("/library/batch/delete")
async def batch_delete_content(
    req: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Batch delete multiple content items in a single operation.
    
    Args:
        req: BatchDeleteRequest containing:
            - content_ids: List of content IDs to delete
            - hard_delete: If True, permanently delete from database (default: False for soft delete)
        db: Database session (injected via dependency).
    
    Returns:
        dict: Response containing:
            - ok: True if operation completed, False on error
            - deleted: Number of content items successfully deleted
            - failed: Number of content items that failed (invalid ID or not found)
            - total: Total number of content IDs in request
            - error: Error message if operation failed
    
    Note:
        Currently performs hard delete regardless of hard_delete flag (soft delete not yet implemented).
        Invalid UUIDs are counted as failed. Transaction is committed on success, rolled back on error.
    
    Example:
        ```json
        {
            "ok": true,
            "deleted": 20,
            "failed": 0,
            "total": 20
        }
        ```
    """
    try:
        content_uuids = []
        for content_id in req.content_ids:
            try:
                content_uuids.append(UUID(content_id))
            except ValueError:
                return {"ok": False, "error": f"Invalid content_id format: {content_id}"}

        service = ContentService(db)
        deleted, failed = await service.batch_delete(content_uuids, hard_delete=req.hard_delete)
        await db.commit()

        return {
            "ok": True,
            "deleted": deleted,
            "failed": failed,
            "total": len(content_uuids),
        }
    except Exception as exc:
        await db.rollback()
        return {"ok": False, "error": str(exc)}


class BatchDownloadRequest(BaseModel):
    """Request model for batch download of content items as ZIP archive."""

    content_ids: list[str] = Field(..., description="List of content IDs to download")


@router.post("/library/batch/download", response_model=None)
async def batch_download_content(
    req: BatchDownloadRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse | dict:
    """Batch download content items as ZIP."""
    try:
        content_uuids = []
        for content_id in req.content_ids:
            try:
                content_uuids.append(UUID(content_id))
            except ValueError:
                return {"ok": False, "error": f"Invalid content_id format: {content_id}"}

        service = ContentService(db)
        mem = io.BytesIO()

        with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            manifest = {"count": 0, "files": []}

            for content_uuid in content_uuids:
                content = await service.get_content(content_uuid, include_character=False)
                if content and content.file_path:
                    file_path = Path(content.file_path)
                    if file_path.exists() and file_path.is_file():
                        arcname = f"{content.content_type}/{file_path.name}"
                        zf.write(file_path, arcname=arcname)
                        manifest["files"].append({
                            "id": str(content.id),
                            "type": content.content_type,
                            "path": arcname,
                        })
                        manifest["count"] += 1

            zf.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True))

        mem.seek(0)
        headers = {"Content-Disposition": 'attachment; filename="ainfluencer-content-library.zip"'}
        return StreamingResponse(mem, media_type="application/zip", headers=headers)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.get("/library/stats")
async def get_content_stats(
    character_id: str | None = Query(default=None, description="Filter by character ID"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get content library statistics with optional character filtering.
    
    Args:
        character_id: Optional UUID to filter statistics by specific character.
        db: Database session (injected via dependency).
    
    Returns:
        dict: Response containing:
            - ok: True if operation succeeded, False otherwise
            - stats: Statistics object containing:
                - total: Total number of content items
                - by_type: Count of content items grouped by type (image, video, text, audio)
                - by_approval_status: Count of content items grouped by approval status
            - error: Error message if operation failed
    
    Raises:
        HTTPException: 400 if character_id format is invalid.
    
    Example:
        ```json
        {
            "ok": true,
            "stats": {
                "total": 150,
                "by_type": {
                    "image": 120,
                    "video": 20,
                    "text": 10
                },
                "by_approval_status": {
                    "approved": 100,
                    "pending": 30,
                    "rejected": 20
                }
            }
        }
        ```
    """
    try:
        character_uuid = None
        if character_id:
            try:
                character_uuid = UUID(character_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid character_id format. Must be UUID.")

        service = ContentService(db)
        stats = await service.get_content_stats(character_id=character_uuid)

        return {
            "ok": True,
            "stats": stats,
        }
    except HTTPException:
        raise
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.put("/library/{content_id}")
async def update_content_item(
    content_id: str,
    approval_status: str | None = None,
    is_approved: bool | None = None,
    rejection_reason: str | None = None,
    quality_score: float | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update content item metadata (approval status, quality score, etc.).
    
    Args:
        content_id: UUID of the content item to update.
        approval_status: Optional approval status to set (pending, approved, rejected).
        is_approved: Optional boolean flag to set approval state.
        rejection_reason: Optional reason for rejection (if rejecting content).
        quality_score: Optional quality score (0.0 to 1.0) to set.
        db: Database session (injected via dependency).
    
    Returns:
        dict: Response containing:
            - ok: True if update succeeded, False otherwise
            - content: Updated content object with:
                - id: Content ID
                - approval_status: Updated approval status
                - is_approved: Updated approval flag
                - rejection_reason: Updated rejection reason (if any)
                - quality_score: Updated quality score (if set)
    
    Raises:
        HTTPException: 400 if content_id format is invalid, 404 if content not found.
    
    Note:
        Only the provided fields are updated. All other fields remain unchanged.
        Transaction is committed on success.
    
    Example:
        ```json
        {
            "ok": true,
            "content": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "approval_status": "approved",
                "is_approved": true,
                "rejection_reason": null,
                "quality_score": 0.85
            }
        }
        ```
    """
    try:
        content_uuid = UUID(content_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid content_id format. Must be UUID.")

    service = ContentService(db)
    updates = {}

    if approval_status is not None:
        updates["approval_status"] = approval_status
    if is_approved is not None:
        updates["is_approved"] = is_approved
    if rejection_reason is not None:
        updates["rejection_reason"] = rejection_reason
    if quality_score is not None:
        updates["quality_score"] = quality_score

    content = await service.update_content(content_uuid, **updates)
    await db.commit()

    if not content:
        raise HTTPException(status_code=404, detail="Content not found.")

    return {
        "ok": True,
        "content": {
            "id": str(content.id),
            "approval_status": content.approval_status,
            "is_approved": content.is_approved,
            "rejection_reason": content.rejection_reason,
            "quality_score": float(content.quality_score) if content.quality_score else None,
        },
    }


@router.delete("/library/{content_id}")
async def delete_content_item(
    content_id: str,
    hard_delete: bool = Query(default=False, description="Hard delete (permanent)"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a single content item from the library.
    
    Args:
        content_id: UUID of the content item to delete.
        hard_delete: If True, permanently delete from database (default: False for soft delete).
        db: Database session (injected via dependency).
    
    Returns:
        dict: Response containing:
            - ok: True if deletion succeeded, False otherwise
            - deleted: True if content was deleted
    
    Raises:
        HTTPException: 400 if content_id format is invalid, 404 if content not found.
    
    Note:
        Currently performs hard delete regardless of hard_delete flag (soft delete not yet implemented).
        Transaction is committed on success.
    
    Example:
        ```json
        {
            "ok": true,
            "deleted": true
        }
        ```
    """
    try:
        content_uuid = UUID(content_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid content_id format. Must be UUID.")

    service = ContentService(db)
    success = await service.delete_content(content_uuid, hard_delete=hard_delete)
    await db.commit()

    if not success:
        raise HTTPException(status_code=404, detail="Content not found.")

    return {"ok": True, "deleted": True}
