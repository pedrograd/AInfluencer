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
