from __future__ import annotations

import io
import json
import zipfile

from fastapi import APIRouter
from fastapi.responses import Response

from app.services.installer_service import InstallerService

router = APIRouter()
installer = InstallerService()


@router.get("/check")
def check() -> dict:
    return installer.check()


@router.get("/status")
def status() -> dict:
    s = installer.status()
    return {
        "state": s.state,
        "step": s.step,
        "message": s.message,
        "progress": s.progress,
        "started_at": s.started_at,
        "finished_at": s.finished_at,
    }


@router.get("/logs")
def logs() -> dict:
    return {"items": installer.logs(limit=1000)}


@router.post("/start")
def start() -> dict:
    installer.start()
    return {"ok": True, "state": installer.status().state}


@router.get("/diagnostics")
def diagnostics() -> Response:
    """
    Download a small diagnostics bundle for support/debugging.
    Includes: system_check.json, installer_status.json, installer_logs.jsonl
    """
    sysinfo = installer.check()
    status = installer.status()
    logs = installer.logs(limit=5000)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("system_check.json", json.dumps(sysinfo, indent=2, sort_keys=True))
        z.writestr("installer_status.json", json.dumps(status.__dict__, indent=2, sort_keys=True))
        z.writestr("installer_logs.jsonl", "\n".join(json.dumps(x, ensure_ascii=False) for x in logs) + "\n")

    data = buf.getvalue()
    headers = {"Content-Disposition": "attachment; filename=ainfluencer-diagnostics.zip"}
    return Response(content=data, media_type="application/zip", headers=headers)
