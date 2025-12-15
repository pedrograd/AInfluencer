from __future__ import annotations

import io
import json
import time
import zipfile

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.paths import images_dir
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
    return generation_service.list_images(q=q, sort=sort, limit=limit, offset=offset)


@router.delete("/images/{filename}")
def delete_image(filename: str) -> dict:
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
    filenames: list[str] = Field(default_factory=list, max_length=5000)


@router.post("/images/delete")
def bulk_delete_images(req: BulkDeleteRequest) -> dict:
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
    older_than_days: int = Field(default=30, ge=1, le=3650)


@router.post("/images/cleanup")
def cleanup_images(req: CleanupRequest) -> dict:
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
    file_path: str = Field(..., description="Path to content file to validate")


@router.post("/validate")
def validate_content(req: ValidateContentRequest) -> dict:
    """
    Validate content quality.

    Validates the quality of generated content (images, videos, etc.)
    and returns a quality score (0.0 to 1.0) along with validation details.
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
    """
    Validate content quality by content ID.

    Note: This endpoint currently requires file_path. Database integration
    will be added in a future update.
    """
    return {
        "ok": False,
        "error": "content_id validation not yet implemented. Use POST /content/validate with file_path.",
    }


class GenerateCaptionRequest(BaseModel):
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
    """
    Generate caption for an image.

    Generates a personality-consistent caption for an image using the character's
    persona and the text generation service. Supports multiple platforms with
    platform-specific formatting and hashtag strategies.
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
