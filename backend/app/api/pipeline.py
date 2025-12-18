"""Pipeline API endpoints for workflow presets and job management.

This module provides API endpoints for:
- Listing workflow presets
- Generating content using presets
- Querying job status and history
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.core.error_taxonomy import ErrorCode, create_error_response
from app.core.middleware import limiter
from app.models.pipeline_contracts import GenerateRequest, GenerateResponse, JobStatus
from app.services.pipeline_manager import pipeline_manager
from app.services.workflow_preset_registry import preset_registry

router = APIRouter()


@router.get("/presets")
def list_presets(category: str | None = None, engine: str | None = None) -> dict:
    """List all available workflow presets.
    
    Args:
        category: Optional category filter
        engine: Optional engine requirement filter
        
    Returns:
        Dictionary with list of presets
    """
    presets = preset_registry.list_presets(category=category, engine_requirement=engine)
    return {
        "ok": True,
        "presets": [preset.model_dump() for preset in presets],
    }


@router.get("/presets/{preset_id}")
def get_preset(preset_id: str) -> dict:
    """Get a specific preset by ID.
    
    Args:
        preset_id: Preset identifier
        
    Returns:
        Dictionary with preset data or error
    """
    preset = preset_registry.get_preset(preset_id)
    if not preset:
        error_response = create_error_response(
            error_code=ErrorCode.FILE_NOT_FOUND,
            message=f"Preset not found: {preset_id}",
        )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response,
        )

    return {
        "ok": True,
        "preset": preset.model_dump(),
    }


@router.post("/generate/image")
@limiter.limit("10/minute")
async def generate_image(request: Request, req: GenerateRequest) -> dict:
    """Generate image using a workflow preset.
    
    Args:
        request: FastAPI request object
        req: Generation request with preset_id, prompt, and parameters
        
    Returns:
        GenerateResponse with job_id and status
    """
    try:
        # Validate consent if identity_reference provided
        if req.identity_reference and not req.consent_given:
            error_response = create_error_response(
                error_code=ErrorCode.CONSENT_MISSING,
                message="Identity-based workflows require consent. Set consent_given=True.",
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response,
            )

        # Prepare inputs
        inputs = {
            "prompt": req.prompt,
            "negative_prompt": req.negative_prompt,
            "seed": req.seed,
        }
        if req.identity_reference:
            inputs["identity_reference"] = req.identity_reference
            inputs["consent_given"] = req.consent_given

        # Execute preset
        job_id = await pipeline_manager.execute_preset(
            preset_id=req.preset_id,
            inputs=inputs,
            quality_level=req.quality_level,
        )

        # Get job status
        job = await pipeline_manager.get_job_status(job_id)
        if not job:
            raise RuntimeError(f"Job {job_id} not found after creation")

        return GenerateResponse(
            job_id=job_id,
            status=job.status,  # type: ignore[arg-type]
            preset_id=req.preset_id,
            estimated_time_seconds=None,  # TODO: Calculate based on quality level
            output_url=job.outputs.get("output_url") if job.status == "completed" else None,
            error=job.error if job.status == "failed" else None,
        ).model_dump()

    except ValueError as e:
        error_response = create_error_response(
            error_code=ErrorCode.CONTRACT_MISMATCH,
            message=str(e),
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response,
        )
    except RuntimeError as e:
        error_msg = str(e)
        if "not available" in error_msg or "not running" in error_msg:
            error_code = ErrorCode.ENGINE_OFFLINE
        else:
            error_code = ErrorCode.UNKNOWN_ERROR

        error_response = create_error_response(
            error_code=error_code,
            message=error_msg,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response,
        )


@router.get("/jobs/{job_id}")
async def get_job(job_id: str) -> dict:
    """Get job status and details.
    
    Args:
        job_id: Job identifier
        
    Returns:
        JobStatus dictionary or error
    """
    job = await pipeline_manager.get_job_status(job_id)
    if not job:
        error_response = create_error_response(
            error_code=ErrorCode.FILE_NOT_FOUND,
            message=f"Job not found: {job_id}",
        )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response,
        )

    return JobStatus(
        job_id=job.job_id,
        status=job.status,  # type: ignore[arg-type]
        preset_id=job.preset_id,
        progress=0.0,  # TODO: Track progress
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        estimated_time_seconds=None,
        output_url=job.outputs.get("output_url") if job.status == "completed" else None,
        error=job.error if job.status == "failed" else None,
        error_code=job.error_code if job.status == "failed" else None,
    ).model_dump()


@router.get("/jobs/{job_id}/artifacts")
async def get_job_artifacts(job_id: str) -> dict:
    """List artifacts for a job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Dictionary with list of artifacts
    """
    job = await pipeline_manager.get_job_status(job_id)
    if not job:
        error_response = create_error_response(
            error_code=ErrorCode.FILE_NOT_FOUND,
            message=f"Job not found: {job_id}",
        )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response,
        )

    artifacts = pipeline_manager.artifact_store.list_artifacts(job_id)
    return {
        "ok": True,
        "job_id": job_id,
        "artifacts": artifacts,
    }
