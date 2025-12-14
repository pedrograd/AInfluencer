from __future__ import annotations

import io
import json
import zipfile

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.paths import images_dir
from app.services.generation_service import generation_service

router = APIRouter()


@router.get("/images")
def list_images() -> dict:
    return {"items": generation_service.list_images(limit=100)}


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


@router.get("/images/download")
def download_all_images():
    items = generation_service.list_images(limit=10_000)
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
