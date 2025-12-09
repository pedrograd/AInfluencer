"""
FastAPI Backend for AInfluencer Web Application

Complete implementation of all API endpoints as per PRD
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.websockets import WebSocket

from database import get_db, init_db
from config.settings import settings
from config.feature_flags import get_feature_flags
from models import *
from services.comfyui_client import ComfyUIClient
from services.generation_service import GenerationService
from services.media_service import MediaService
from services.character_service import CharacterService
from services.batch_generation_service import BatchGenerationService
from services.websocket_service import WebSocketService
from services.post_processing_service import PostProcessingService
from services.face_consistency_service import FaceConsistencyService
from services.job_monitor_service import JobMonitorService
from services.anti_detection_service import AntiDetectionService
from services.quality_service import QualityService
from services.prompt_service import PromptService
from services.system_setup_service import SystemSetupService
from services.model_management_service import ModelManagementService
from services.quality_assurance_service import QualityAssuranceService
from services.troubleshooting_service import TroubleshootingService, ErrorCode
from services.platform_integration_service import PlatformIntegrationService
from services.platform_optimization_service import PlatformOptimizationService
from services.prompt_engineering_service import PromptEngineeringService
from services.anti_detection_service import MetadataCleaner
from services.quality_scorer_service import QualityScorer
from services.detection_tester_service import DetectionTester
from services.quality_metrics_service import QualityMetrics
from services.quality_dashboard_service import QualityDashboard
from services.quality_improver_service import QualityImprover
from services.best_practices_service import BestPracticesService
from middleware.best_practices_middleware import BestPracticesMiddleware
# Note: QualityAssuranceService is different from QualityService
# - QualityAssuranceService: Realism checklist and AI detection per setup guide (docs/18-AI-TOOLS-NVIDIA-SETUP.md)
# - QualityService: General quality scoring (existing service)
# - QualityScorer: Comprehensive quality scoring per QA document (docs/28-QUALITY-ASSURANCE-SYSTEM.md)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AInfluencer Backend API",
    description="Ultra-Realistic AI Media Generator API",
    version="1.0.0"
)

# CORS middleware (env-driven for deployments)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware (rate limiting, HTTPS enforcement, security headers)
from middleware.security_middleware import SecurityMiddleware

app.add_middleware(
    SecurityMiddleware,
    enable_rate_limiting=settings.rate_limiting_enabled,
    max_requests_per_minute=settings.rate_limit_per_minute,
    max_requests_per_hour=settings.rate_limit_per_hour,
    max_request_size_mb=settings.max_request_size_mb,
    request_timeout_seconds=settings.request_timeout_seconds,
)

# Best Practices middleware (performance monitoring, best practices checks)
app.add_middleware(BestPracticesMiddleware)

# Directories
BASE_DIR = Path(__file__).parent
MEDIA_ROOT = BASE_DIR / "media_library"
CHARACTERS_ROOT = BASE_DIR / "characters"
COMFYUI_OUTPUT = BASE_DIR.parent / "ComfyUI" / "output"
COMFYUI_INPUT = BASE_DIR.parent / "ComfyUI" / "input"

# Create directories
MEDIA_ROOT.mkdir(exist_ok=True)
CHARACTERS_ROOT.mkdir(exist_ok=True)
COMFYUI_OUTPUT.mkdir(exist_ok=True)
COMFYUI_INPUT.mkdir(exist_ok=True)

# Initialize ComfyUI client
comfyui_client = ComfyUIClient(settings.comfyui_server)

# Limit concurrent heavy jobs for free/CPU deployments
generation_semaphore = asyncio.Semaphore(settings.max_concurrent_jobs)

# Feature flags
feature_flags = get_feature_flags()

# ComfyUI availability flag
comfyui_available = True

# Initialize WebSocket service
websocket_service = WebSocketService()

# Initialize Platform Optimization service
from services.platform_optimization_service import PlatformOptimizationService
platform_optimization_service = PlatformOptimizationService()

# Initialize Anti-Detection service
anti_detection_service = AntiDetectionService()
metadata_cleaner = MetadataCleaner()

# Initialize Prompt Engineering service
prompt_engineering_service = PromptEngineeringService()

# Initialize Troubleshooting service
troubleshooting_service = TroubleshootingService()

# Initialize Best Practices service
best_practices_service = BestPracticesService()

# Initialize Model Management service
model_management_service = ModelManagementService()

# Initialize Performance Monitor
from services.performance_monitor import PerformanceMonitor
performance_monitor = PerformanceMonitor()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    global comfyui_available
    init_db()
    logger.info("Database initialized")

    try:
        comfyui_available = comfyui_client.check_connection()
    except Exception as exc:
        comfyui_available = False
        logger.warning(f"ComfyUI health check failed: {exc}")

# Helper function for error responses
def error_response(code: str, message: str, details: Any = None, error_code: Optional[str] = None):
    """Create error response with optional troubleshooting error code"""
    error_data = {
        "code": code,
        "message": message,
        "details": details
    }
    
    # Add troubleshooting error code if provided
    if error_code:
        error_data["troubleshooting_code"] = error_code
        # Get resolution if available
        try:
            resolution = troubleshooting_service.get_error_resolution(error_code)
            if resolution:
                error_data["troubleshooting"] = {
                    "title": resolution.get("title"),
                    "solutions": resolution.get("solutions", [])
                }
        except Exception:
            pass  # Don't fail if troubleshooting service has issues
    
    return JSONResponse(
        status_code=400 if code != "NOT_FOUND" else 404,
        content={
            "success": False,
            "error": error_data
        }
    )


def demo_limit_response(message: str, details: Optional[Dict[str, Any]] = None):
    return JSONResponse(
        status_code=503,
        content={
            "success": False,
            "error": {
                "code": "DEMO_MODE_LIMIT",
                "message": message,
                "details": details or {},
            },
        },
    )


def ensure_comfyui_available() -> Optional[JSONResponse]:
    """Return a 503 response when ComfyUI is unreachable."""
    global comfyui_available
    if not comfyui_available:
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": {
                    "code": "COMFYUI_UNAVAILABLE",
                    "message": "ComfyUI backend is not reachable on this host. Demo mode is limited to UI only.",
                },
            },
        )
    # Re-validate lazily to detect runtime failures
    if not comfyui_client.check_connection():
        comfyui_available = False
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": {
                    "code": "COMFYUI_UNAVAILABLE",
                    "message": "ComfyUI backend is not reachable on this host. Demo mode is limited to UI only.",
                },
            },
        )
    return None

# Helper function for success responses
def success_response(data: Any, message: Optional[str] = None):
    response = {"success": True, "data": data}
    if message:
        response["message"] = message
    return response

# ============================================================================
# Health Check
# ============================================================================

@app.get("/")
async def root():
    return {"message": "AInfluencer Backend API", "status": "running"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    global comfyui_available
    comfyui_connected = comfyui_available and comfyui_client.check_connection()
    comfyui_available = comfyui_connected
    redis_connected = cache_service.enabled
    return success_response({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "comfyui_connected": comfyui_connected,
        "redis_connected": redis_connected
    })

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return get_metrics()

# ============================================================================
# Image Generation
# ============================================================================

@app.post("/api/generate/image")
async def generate_image(
    request: Dict[str, Any],
    db = Depends(get_db)
):
    """Generate an ultra-realistic image
    
    Request body:
    {
        "prompt": str,
        "negative_prompt": str (optional),
        "character_id": str (optional),
        "settings": dict (optional),
        "face_consistency": dict (optional),
        "post_processing": dict (optional),
        "platform": str (optional),
        "optimize_prompt": bool (optional, default: true)
    }
    """
    try:
        guard = ensure_comfyui_available()
        if guard:
            return guard

        async with generation_semaphore:
            prompt = request.get("prompt")
            if not prompt:
                raise HTTPException(status_code=400, detail="Prompt is required")
            
            req_settings = request.get("settings", {}) or {}
            post_processing = request.get("post_processing", {}) or {}

            width = req_settings.get("width", 0)
            height = req_settings.get("height", 0)
            batch = (
                request.get("batch_count")
                or request.get("batchCount")
                or req_settings.get("batch_count")
                or req_settings.get("batch")
                or 1
            )

            if feature_flags.demo_mode:
                if width and width > feature_flags.demo_max_width:
                    return demo_limit_response(
                        f"Width limited to {feature_flags.demo_max_width}px in demo mode",
                        {"max_width": feature_flags.demo_max_width},
                    )
                if height and height > feature_flags.demo_max_height:
                    return demo_limit_response(
                        f"Height limited to {feature_flags.demo_max_height}px in demo mode",
                        {"max_height": feature_flags.demo_max_height},
                    )
                if batch and int(batch) > feature_flags.demo_max_batch:
                    return demo_limit_response(
                        "Batch generation is limited on the public demo",
                        {"max_batch": feature_flags.demo_max_batch},
                    )
                if post_processing.get("upscale"):
                    return demo_limit_response("Upscaling is disabled in demo mode")
                if post_processing.get("face_restoration"):
                    return demo_limit_response("Face restoration is disabled in demo mode")

            if not feature_flags.enable_upscale and post_processing.get("upscale"):
                return demo_limit_response("Upscaling is currently disabled")
            if not feature_flags.enable_face_restore and post_processing.get("face_restoration"):
                return demo_limit_response("Face restoration is currently disabled")
            if not feature_flags.enable_batch and batch and int(batch) > 1:
                return demo_limit_response("Batch generation is disabled on this deployment")
            if not feature_flags.enable_high_res and (width and width > 1024 or height and height > 1024):
                return demo_limit_response("High resolution generation is disabled on this deployment")

            generation_service = GenerationService(db, comfyui_client)
            job = generation_service.generate_image(
                prompt=prompt,
                negative_prompt=request.get("negative_prompt"),
                character_id=request.get("character_id"),
                settings=request.get("settings", {}),
                face_consistency=request.get("face_consistency", {}),
                post_processing=request.get("post_processing", {}),
                platform=request.get("platform"),
                optimize_prompt=request.get("optimize_prompt", True)
            )
            
            # Start monitoring job in background
            # Note: Job monitoring will check ComfyUI and save results automatically
            # The websocket service also monitors, but this provides a fallback
            try:
                import threading

                monitor = JobMonitorService(db, comfyui_client, MEDIA_ROOT)

                def start_monitor():
                    try:
                        # Create new event loop for this thread
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(monitor.monitor_job(job.id))
                    except Exception as e:
                        logger.error(f"Job monitor thread error: {e}")
                
                monitor_thread = threading.Thread(target=start_monitor, daemon=True)
                monitor_thread.start()
            except Exception as e:
                logger.warning(f"Failed to start job monitoring: {e}")
                # Continue anyway - websocket service will handle it
            
            return success_response({
                "job_id": job.id,
                "status": job.status,
                "estimated_time": 120  # TODO: Calculate based on settings
            })
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        # Determine error code for troubleshooting
        error_code = None
        error_str = str(e).lower()
        if "cuda out of memory" in error_str or "out of memory" in error_str:
            error_code = ErrorCode.CUDA_OUT_OF_MEMORY.value
        elif "cuda" in error_str and "not found" in error_str:
            error_code = ErrorCode.CUDA_DEVICE_NOT_FOUND.value
        elif "model" in error_str and "not found" in error_str:
            error_code = ErrorCode.MODEL_FILE_NOT_FOUND.value
        elif "connection" in error_str or "refused" in error_str:
            error_code = ErrorCode.COMFYUI_NOT_RUNNING.value
        else:
            error_code = ErrorCode.GENERATION_FAILED.value
        
        # Return error with troubleshooting info
        return error_response(
            "GENERATION_FAILED",
            str(e),
            {"error_code": error_code},
            error_code=error_code
        )

@app.get("/api/generate/image/{job_id}")
async def get_image_generation_status(job_id: str, db = Depends(get_db)):
    """Get image generation status"""
    generation_service = GenerationService(db, comfyui_client)
    job = generation_service.get_job_status(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get result media if available
    media_id = None
    if job.result_media:
        media_id = job.result_media.id
    
    return success_response({
        "job_id": job.id,
        "status": job.status,
        "progress": job.progress,
        "media_id": media_id,
        "error": job.error_message
    })

# ============================================================================
# Video Generation
# ============================================================================

@app.post("/api/generate/video")
async def generate_video(
    request: Dict[str, Any],
    db = Depends(get_db)
):
    """
    Generate an ultra-realistic video
    
    Methods: animatediff, svd, modelscope, veo, luma, kling, wan, pika, sora
    
    Request body:
    {
        "prompt": str,
        "negativePrompt": str (optional),
        "method": str (optional),
        "imageId": str (optional),
        "characterId": str (optional),
        "settings": dict (optional),
        "faceConsistency": dict (optional),
        "postProcessing": dict (optional),
        "platform": str (optional)
    }
    """
    try:
        guard = ensure_comfyui_available()
        if guard:
            return guard

        async with generation_semaphore:
            # Extract parameters from request body
            prompt = request.get("prompt")
            if not prompt:
                raise HTTPException(status_code=400, detail="Prompt is required")

            if feature_flags.demo_mode or not feature_flags.enable_advanced:
                return demo_limit_response("Video generation is disabled in demo mode on free tiers")
            
            generation_service = GenerationService(db, comfyui_client)
            job = generation_service.generate_video(
                prompt=prompt,
                negative_prompt=request.get("negativePrompt"),
                character_id=request.get("characterId"),
                image_id=request.get("imageId"),
                method=request.get("method"),
                settings=request.get("settings", {}),
                face_consistency=request.get("faceConsistency", {}),
                post_processing=request.get("postProcessing", {})
            )
            
            # Estimate time based on method
            method_estimates = {
                "animatediff": 120,
                "svd": 180,
                "modelscope": 200,
                "veo": 300,
                "luma": 240,
                "kling": 320,
                "wan": 180,
                "pika": 200,
                "sora": 300
            }
            estimated_time = method_estimates.get(
                job.settings.get("method", "animatediff"),
                300
            )
            
            return success_response({
                "job_id": job.id,
                "status": job.status,
                "method": job.settings.get("method"),
                "estimated_time": estimated_time
            })
    except Exception as e:
        logger.error(f"Video generation error: {e}")
        # Determine error code for troubleshooting
        error_code = None
        error_str = str(e).lower()
        if "cuda out of memory" in error_str or "out of memory" in error_str:
            error_code = ErrorCode.CUDA_OUT_OF_MEMORY.value
        elif "cuda" in error_str and "not found" in error_str:
            error_code = ErrorCode.CUDA_DEVICE_NOT_FOUND.value
        elif "model" in error_str and "not found" in error_str:
            error_code = ErrorCode.MODEL_FILE_NOT_FOUND.value
        elif "connection" in error_str or "refused" in error_str:
            error_code = ErrorCode.COMFYUI_NOT_RUNNING.value
        else:
            error_code = ErrorCode.GENERATION_FAILED.value
        
        # Return error with troubleshooting info
        return error_response(
            "GENERATION_FAILED",
            str(e),
            {"error_code": error_code},
            error_code=error_code
        )

@app.get("/api/generate/video/{job_id}")
async def get_video_generation_status(job_id: str, db = Depends(get_db)):
    """Get video generation status"""
    generation_service = GenerationService(db, comfyui_client)
    job = generation_service.get_job_status(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return success_response({
        "job_id": job.id,
        "status": job.status,
        "progress": job.progress,
        "method": job.settings.get("method") if job.settings else None,
        "current_frame": int(job.progress * 720) if job.meta_data.get("total_frames") else None,
        "total_frames": job.meta_data.get("total_frames"),
        "media_id": job.result_media.id if job.result_media else None,
        "error": job.error_message
    })

@app.post("/api/video/optimize")
async def optimize_video_for_platform(
    media_id: str,
    platform: str,
    quality: str = "high",
    db = Depends(get_db)
):
    """Optimize video for specific platform"""
    try:
        from services.media_service import MediaService
        media_service = MediaService(db, MEDIA_ROOT)
        media = media_service.get_media(media_id)
        
        if not media or media.type != "video":
            raise HTTPException(status_code=404, detail="Video not found")
        
        input_path = Path(media.file_path)
        if not input_path.exists():
            raise HTTPException(status_code=404, detail="Video file not found")
        
        # Create optimized output
        output_path = MEDIA_ROOT / "optimized" / platform / f"{media.id}_{platform}.mp4"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        success = platform_optimization_service.optimize_for_platform(
            input_path=input_path,
            output_path=output_path,
            platform=platform,
            quality=quality
        )
        
        if success:
            # Create new media item for optimized video
            optimized_media = media_service.create_media_item(
                file_path=output_path,
                media_type="video",
                source="optimized",
                character_id=media.character_id,
                tags=media.tags + [f"platform:{platform}", "optimized"]
            )
            
            return success_response({
                "media_id": optimized_media.id,
                "platform": platform,
                "file_path": str(output_path)
            })
        else:
            raise HTTPException(status_code=500, detail="Optimization failed")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/video/platforms/{platform}/specs")
async def get_platform_specs(platform: str):
    """Get platform specifications"""
    specs = platform_optimization_service.get_platform_specs(platform)
    if not specs:
        raise HTTPException(status_code=404, detail="Platform not found")
    
    return success_response(specs)

# ============================================================================
# Batch Generation
# ============================================================================

@app.post("/api/generate/batch")
async def batch_generate(
    type: str,
    count: int,
    prompt_template: str,
    variations: Optional[List[str]] = None,
    character_id: Optional[str] = None,
    settings: Optional[Dict[str, Any]] = None,
    priority: str = "normal",
    db = Depends(get_db)
):
    """Start batch generation"""
    try:
        generation_service = GenerationService(db, comfyui_client)
        batch_service = BatchGenerationService(db, generation_service)
        
        batch_job = batch_service.create_batch_job(
            batch_type=type,
            count=count,
            prompt_template=prompt_template,
            variations=variations,
            character_id=character_id,
            settings=settings,
            priority=priority
        )
        
        # Start processing in background
        batch_service.start_batch_job(batch_job.id)
        
        return success_response({
            "batch_job_id": batch_job.id,
            "status": batch_job.status,
            "total_count": batch_job.total_count,
            "estimated_time": count * 120
        })
    except Exception as e:
        logger.error(f"Batch generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/generate/batch/{batch_job_id}")
async def get_batch_generation_status(batch_job_id: str, db = Depends(get_db)):
    """Get batch generation status"""
    try:
        generation_service = GenerationService(db, comfyui_client)
        batch_service = BatchGenerationService(db, generation_service)
        
        status = batch_service.get_batch_job_status(batch_job_id)
        if not status:
            raise HTTPException(status_code=404, detail="Batch job not found")
        
        return success_response(status)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Media Management
# ============================================================================

@app.get("/api/media")
async def list_media(
    type: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    character_id: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    sort: str = Query("created_at"),
    order: str = Query("desc"),
    db = Depends(get_db)
):
    """List media items"""
    media_service = MediaService(db, MEDIA_ROOT)
    
    tag_list = tags.split(",") if tags else None
    
    result = media_service.list_media(
        media_type=type,
        source=source,
        character_id=character_id,
        tags=tag_list,
        page=page,
        limit=limit,
        sort=sort,
        order=order
    )
    
    # Format response
    items = []
    for item in result["items"]:
        items.append({
            "id": item.id,
            "type": item.type,
            "source": item.source,
            "file_name": item.file_name,
            "file_size": item.file_size,
            "width": item.width,
            "height": item.height,
            "thumbnail_path": item.thumbnail_path,
            "character_id": item.character_id,
            "character_name": item.character.name if item.character else None,
            "tags": item.tags,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "quality_score": 0.0  # TODO: Get from quality_scores
        })
    
    return success_response({
        "items": items,
        "total": result["total"],
        "page": result["page"],
        "limit": result["limit"],
        "total_pages": result["total_pages"]
    })

@app.get("/api/media/{media_id}")
async def get_media(media_id: str, db = Depends(get_db)):
    """Get a specific media item"""
    media_service = MediaService(db, MEDIA_ROOT)
    media = media_service.get_media(media_id)
    
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    return success_response({
        "id": media.id,
        "type": media.type,
        "source": media.source,
        "file_path": media.file_path,
        "file_name": media.file_name,
        "file_size": media.file_size,
        "width": media.width,
        "height": media.height,
        "mime_type": media.mime_type,
        "thumbnail_path": media.thumbnail_path,
        "character_id": media.character_id,
        "character_name": media.character.name if media.character else None,
        "tags": media.tags,
        "created_at": media.created_at.isoformat() if media.created_at else None,
        "updated_at": media.updated_at.isoformat() if media.updated_at else None,
        "metadata": media.meta_data,
        "quality_score": {
            "overall": 0.0,
            "realism": 0.0,
            "artifact": 0.0,
            "face_quality": 0.0
        }
    })

@app.post("/api/media/upload")
async def upload_media(
    file: UploadFile = File(...),
    character_id: Optional[str] = None,
    tags: Optional[str] = None,
    db = Depends(get_db)
):
    """Upload personal media"""
    try:
        # Determine media type
        media_type = "video" if file.content_type and "video" in file.content_type else "image"
        
        # Save file
        file_path = MEDIA_ROOT / media_type / file.filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Create media item
        media_service = MediaService(db, MEDIA_ROOT)
        tag_list = tags.split(",") if tags else []
        
        media = media_service.create_media_item(
            file_path=file_path,
            media_type=media_type,
            source="personal",
            character_id=character_id,
            tags=tag_list
        )
        
        return success_response({
            "media_id": media.id,
            "file_name": media.file_name,
            "file_size": media.file_size,
            "width": media.width,
            "height": media.height,
            "created_at": media.created_at.isoformat() if media.created_at else None
        })
    except Exception as e:
        logger.error(f"Media upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/media/{media_id}")
async def delete_media(media_id: str, db = Depends(get_db)):
    """Delete a media item"""
    media_service = MediaService(db, MEDIA_ROOT)
    success = media_service.delete_media(media_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Media not found")
    
    return success_response({"media_id": media_id, "deleted": True})

@app.post("/api/media/{media_id}/tags")
async def update_media_tags(
    media_id: str,
    tags: List[str],
    db = Depends(get_db)
):
    """Update media tags"""
    media_service = MediaService(db, MEDIA_ROOT)
    media = media_service.update_tags(media_id, tags)
    
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    return success_response({
        "media_id": media.id,
        "tags": media.tags
    })

@app.get("/api/media/{media_id}/download")
async def download_media(media_id: str, db = Depends(get_db)):
    """Download media file"""
    media_service = MediaService(db, MEDIA_ROOT)
    media = media_service.get_media(media_id)
    
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    file_path = Path(media.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=media.file_name,
        media_type=media.mime_type
    )

# ============================================================================
# Character Management
# ============================================================================

@app.get("/api/characters")
async def list_characters(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    db = Depends(get_db)
):
    """List all characters with optional search"""
    character_service = CharacterService(db, CHARACTERS_ROOT)
    result = character_service.list_characters(page=page, limit=limit, search=search)
    
    characters = []
    for char in result["characters"]:
        # Format face references
        face_refs = []
        for fr in char.face_references:
            if not fr.deleted_at:
                face_refs.append({
                    "id": fr.id,
                    "file_name": fr.file_name,
                    "file_path": fr.file_path,
                    "width": fr.width,
                    "height": fr.height,
                    "metadata": fr.meta_data,
                    "created_at": fr.created_at.isoformat() if fr.created_at else None
                })
        
        characters.append({
            "id": char.id,
            "name": char.name,
            "age": char.age,
            "description": char.description,
            "face_references": face_refs,
            "face_reference_count": char.face_reference_count,
            "media_count": char.media_count,
            "persona": char.persona,
            "appearance": char.appearance,
            "style": char.style,
            "content_preferences": char.content_preferences,
            "consistency_rules": char.consistency_rules,
            "created_at": char.created_at.isoformat() if char.created_at else None,
            "updated_at": char.updated_at.isoformat() if char.updated_at else None
        })
    
    return success_response({
        "characters": characters,
        "total": result["total"],
        "page": result["page"],
        "limit": result["limit"],
        "total_pages": result["total_pages"]
    })

@app.get("/api/characters/{character_id}")
async def get_character(character_id: str, db = Depends(get_db)):
    """Get a specific character with full Character Management System data"""
    character_service = CharacterService(db, CHARACTERS_ROOT)
    character = character_service.get_character(character_id)
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Get statistics
    stats = character_service.get_character_statistics(character_id)
    
    # Format face references
    face_refs = []
    for fr in character.face_references:
        if not fr.deleted_at:
            face_refs.append({
                "id": fr.id,
                "file_name": fr.file_name,
                "file_path": fr.file_path,
                "width": fr.width,
                "height": fr.height,
                "metadata": fr.meta_data,
                "created_at": fr.created_at.isoformat() if fr.created_at else None
            })
    
    return success_response({
        "id": character.id,
        "name": character.name,
        "age": character.age,
        "description": character.description,
        "persona": character.persona,
        "appearance": character.appearance,
        "style": character.style,
        "content_preferences": character.content_preferences,
        "consistency_rules": character.consistency_rules,
        "face_references": face_refs,
        "settings": character.settings,
        "metadata": character.meta_data,
        "statistics": stats,
        "created_at": character.created_at.isoformat() if character.created_at else None,
        "updated_at": character.updated_at.isoformat() if character.updated_at else None
    })

@app.post("/api/characters")
async def create_character(
    request: Dict[str, Any],
    db = Depends(get_db)
):
    """
    Create a new character with full Character Management System support
    
    Request body:
    {
        "name": str (required),
        "age": int (optional),
        "description": str (optional),
        "persona": dict (optional),
        "appearance": dict (optional),
        "style": dict (optional),
        "content_preferences": dict (optional),
        "consistency_rules": dict (optional),
        "settings": dict (optional),
        "metadata": dict (optional),
        "template": str (optional) - template name to use
    }
    """
    character_service = CharacterService(db, CHARACTERS_ROOT)
    
    # Check if using template
    template_name = request.get("template")
    if template_name:
        character = character_service.create_character_from_template(
            template_name=template_name,
            name=request.get("name", "Character"),
            persona=request.get("persona"),
            appearance=request.get("appearance"),
            style=request.get("style"),
            content_preferences=request.get("content_preferences"),
            consistency_rules=request.get("consistency_rules")
        )
    else:
        character = character_service.create_character(
            name=request.get("name"),
            age=request.get("age"),
            description=request.get("description"),
            persona=request.get("persona"),
            appearance=request.get("appearance"),
            style=request.get("style"),
            content_preferences=request.get("content_preferences"),
            consistency_rules=request.get("consistency_rules"),
            settings=request.get("settings"),
            metadata=request.get("metadata")
        )
    
    return success_response({
        "character_id": character.id,
        "name": character.name,
        "created_at": character.created_at.isoformat() if character.created_at else None
    })

@app.put("/api/characters/{character_id}")
async def update_character(
    character_id: str,
    request: Dict[str, Any],
    db = Depends(get_db)
):
    """
    Update a character with full Character Management System support
    
    Request body can include any of:
    {
        "name": str (optional),
        "age": int (optional),
        "description": str (optional),
        "persona": dict (optional),
        "appearance": dict (optional),
        "style": dict (optional),
        "content_preferences": dict (optional),
        "consistency_rules": dict (optional),
        "settings": dict (optional),
        "metadata": dict (optional)
    }
    """
    character_service = CharacterService(db, CHARACTERS_ROOT)
    character = character_service.update_character(
        character_id=character_id,
        name=request.get("name"),
        age=request.get("age"),
        description=request.get("description"),
        persona=request.get("persona"),
        appearance=request.get("appearance"),
        style=request.get("style"),
        content_preferences=request.get("content_preferences"),
        consistency_rules=request.get("consistency_rules"),
        settings=request.get("settings"),
        metadata=request.get("metadata")
    )
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return success_response({
        "character_id": character.id,
        "updated_at": character.updated_at.isoformat() if character.updated_at else None
    })

@app.delete("/api/characters/{character_id}")
async def delete_character(character_id: str, db = Depends(get_db)):
    """Delete a character"""
    character_service = CharacterService(db, CHARACTERS_ROOT)
    success = character_service.delete_character(character_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return success_response({"character_id": character_id, "deleted": True})

@app.post("/api/characters/{character_id}/face-references")
async def upload_face_reference(
    character_id: str,
    file: UploadFile = File(...),
    db = Depends(get_db)
):
    """Upload a face reference image"""
    try:
        # Save file
        character_service = CharacterService(db, CHARACTERS_ROOT)
        char_dir = CHARACTERS_ROOT / character_id / "face_references"
        char_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename to avoid conflicts
        import uuid
        file_ext = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = char_dir / unique_filename
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Create face reference
        face_ref = character_service.add_face_reference(character_id, file_path)
        
        if not face_ref:
            raise HTTPException(status_code=404, detail="Character not found")
        
        # Return file path that can be used for face consistency
        # In production, you might want to return a URL or handle file serving differently
        return success_response({
            "face_reference_id": face_ref.id,
            "file_name": face_ref.file_name,
            "file_path": str(file_path),  # Return path for use in face consistency
            "width": face_ref.width,
            "height": face_ref.height,
            "created_at": face_ref.created_at.isoformat() if face_ref.created_at else None
        })
    except Exception as e:
        logger.error(f"Face reference upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/characters/{character_id}/face-references/{face_reference_id}")
async def delete_face_reference(
    character_id: str,
    face_reference_id: str,
    db = Depends(get_db)
):
    """Delete a face reference"""
    character_service = CharacterService(db, CHARACTERS_ROOT)
    success = character_service.remove_face_reference(character_id, face_reference_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Face reference not found")
    
    return success_response({"face_reference_id": face_reference_id, "deleted": True})

@app.get("/api/characters/{character_id}/face-references/{face_reference_id}/image")
async def get_face_reference_image(
    character_id: str,
    face_reference_id: str,
    db = Depends(get_db)
):
    """Get face reference image file"""
    character_service = CharacterService(db, CHARACTERS_ROOT)
    character = character_service.get_character(character_id)
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Find face reference
    face_ref = None
    for fr in character.face_references:
        if fr.id == face_reference_id and not fr.deleted_at:
            face_ref = fr
            break
    
    if not face_ref:
        raise HTTPException(status_code=404, detail="Face reference not found")
    
    file_path = Path(face_ref.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Face reference file not found")
    
    return FileResponse(
        path=str(file_path),
        filename=face_ref.file_name,
        media_type=face_ref.mime_type or "image/jpeg"
    )

# ============================================================================
# Character Management System - Additional Endpoints
# ============================================================================

@app.get("/api/characters/templates")
async def get_character_templates(db = Depends(get_db)):
    """Get all available character templates"""
    character_service = CharacterService(db, CHARACTERS_ROOT)
    templates = character_service.get_templates()
    return success_response(templates)

@app.get("/api/characters/templates/{template_name}")
async def get_character_template(template_name: str, db = Depends(get_db)):
    """Get a specific character template"""
    character_service = CharacterService(db, CHARACTERS_ROOT)
    template = character_service.get_template(template_name)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return success_response(template)

@app.post("/api/characters/{character_id}/export")
async def export_character(
    character_id: str,
    db = Depends(get_db)
):
    """Export character to JSON file"""
    character_service = CharacterService(db, CHARACTERS_ROOT)
    character = character_service.get_character(character_id)
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Create export directory
    export_dir = CHARACTERS_ROOT / "exports"
    export_dir.mkdir(exist_ok=True)
    
    # Generate export filename
    export_filename = f"{character.name.replace(' ', '_')}_{character.id}.json"
    export_path = export_dir / export_filename
    
    success = character_service.export_character(character_id, export_path)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to export character")
    
    # Return file for download
    return FileResponse(
        path=str(export_path),
        filename=export_filename,
        media_type="application/json"
    )

@app.post("/api/characters/import")
async def import_character(
    file: UploadFile = File(...),
    db = Depends(get_db)
):
    """Import character from JSON file"""
    try:
        character_service = CharacterService(db, CHARACTERS_ROOT)
        
        # Save uploaded file temporarily
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = Path(tmp_file.name)
        
        try:
            character = character_service.import_character(tmp_path)
            
            if not character:
                raise HTTPException(status_code=400, detail="Failed to import character")
            
            return success_response({
                "character_id": character.id,
                "name": character.name,
                "created_at": character.created_at.isoformat() if character.created_at else None
            })
        finally:
            # Clean up temp file
            if tmp_path.exists():
                os.unlink(tmp_path)
    except Exception as e:
        logger.error(f"Character import error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/characters/{character_id}/statistics")
async def get_character_statistics(character_id: str, db = Depends(get_db)):
    """Get detailed character statistics"""
    character_service = CharacterService(db, CHARACTERS_ROOT)
    stats = character_service.get_character_statistics(character_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return success_response(stats)

@app.post("/api/characters/batch-generate")
async def batch_generate_characters(
    request: Dict[str, Any],
    db = Depends(get_db)
):
    """
    Batch generate content for multiple characters
    
    Request body:
    {
        "character_ids": [str] (required),
        "count_per_character": int (optional, default: 10),
        "prompt_template": str (optional),
        "settings": dict (optional)
    }
    """
    character_service = CharacterService(db, CHARACTERS_ROOT)
    character_ids = request.get("character_ids", [])
    count_per_character = request.get("count_per_character", 10)
    
    if not character_ids:
        raise HTTPException(status_code=400, detail="character_ids is required")
    
    results = character_service.batch_generate(
        character_ids=character_ids,
        count_per_character=count_per_character
    )
    
    return success_response(results)

# ============================================================================
# Face Consistency Management
# ============================================================================

@app.get("/api/face-consistency/methods")
async def get_face_consistency_methods(db = Depends(get_db)):
    """Get available face consistency methods and their information"""
    face_service = FaceConsistencyService(db)
    methods = face_service.get_available_methods()
    return success_response(methods)

@app.post("/api/face-consistency/validate")
async def validate_face_reference(
    file: UploadFile = File(...),
    db = Depends(get_db)
):
    """Validate face reference image quality"""
    try:
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            face_service = FaceConsistencyService(db)
            result = face_service.validate_face_quality(tmp_path)
            return success_response(result)
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        logger.error(f"Face validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/face-consistency/similarity")
async def calculate_face_similarity(
    reference_file: UploadFile = File(...),
    generated_file: UploadFile = File(...),
    db = Depends(get_db)
):
    """Calculate face similarity between reference and generated image"""
    try:
        import tempfile
        import os
        
        # Save files temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(reference_file.filename)[1]) as ref_tmp:
            ref_content = await reference_file.read()
            ref_tmp.write(ref_content)
            ref_path = ref_tmp.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(generated_file.filename)[1]) as gen_tmp:
            gen_content = await generated_file.read()
            gen_tmp.write(gen_content)
            gen_path = gen_tmp.name
        
        try:
            face_service = FaceConsistencyService(db)
            similarity = face_service.calculate_face_similarity(ref_path, gen_path)
            
            return success_response({
                "similarity": similarity,
                "target_met": similarity > 0.85,
                "target": 0.85
            })
        finally:
            # Clean up temp files
            for path in [ref_path, gen_path]:
                if os.path.exists(path):
                    os.unlink(path)
                    
    except Exception as e:
        logger.error(f"Face similarity calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/face-consistency/test")
async def test_face_consistency(
    reference_file: UploadFile = File(...),
    generated_files: List[UploadFile] = File(...),
    db = Depends(get_db)
):
    """Test face consistency across multiple generated images"""
    try:
        import tempfile
        import os
        
        # Save reference file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(reference_file.filename)[1]) as ref_tmp:
            ref_content = await reference_file.read()
            ref_tmp.write(ref_content)
            ref_path = ref_tmp.name
        
        # Save generated files
        gen_paths = []
        for gen_file in generated_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(gen_file.filename)[1]) as gen_tmp:
                gen_content = await gen_file.read()
                gen_tmp.write(gen_content)
                gen_paths.append(gen_tmp.name)
        
        try:
            face_service = FaceConsistencyService(db)
            result = face_service.test_consistency(ref_path, gen_paths)
            return success_response(result)
        finally:
            # Clean up temp files
            for path in [ref_path] + gen_paths:
                if os.path.exists(path):
                    os.unlink(path)
                    
    except Exception as e:
        logger.error(f"Face consistency test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Generation History
# ============================================================================

@app.get("/api/generate/history")
async def get_generation_history(
    type: Optional[str] = Query(None),
    character_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db = Depends(get_db)
):
    """Get generation history"""
    # TODO: Implement generation history
    return success_response({
        "jobs": [],
        "total": 0,
        "page": page,
        "limit": limit
    })

# ============================================================================
# Post-Processing (docs/23-POST-PROCESSING-MASTER-WORKFLOW.md)
# ============================================================================

@app.post("/api/post-process/image")
async def post_process_image(
    media_id: str,
    config: Optional[Dict[str, Any]] = None,
    pipeline: Optional[str] = None,
    db = Depends(get_db)
):
    """Post-process an image with specified configuration or pipeline"""
    try:
        media_service = MediaService(db, MEDIA_ROOT)
        media = media_service.get_media(media_id)
        
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")
        
        if media.type != "image":
            raise HTTPException(status_code=400, detail="Media is not an image")
        
        input_path = Path(media.file_path)
        if not input_path.exists():
            raise HTTPException(status_code=404, detail="Media file not found")
        
        # Create output path
        output_dir = MEDIA_ROOT / "processed" / media_id
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"processed_{input_path.name}"
        
        # Get config
        if pipeline:
            processing_config = post_processing_service.get_preset_config(pipeline)
        else:
            processing_config = config or {}
        
        # Process image
        success = post_processing_service.process_image(
            input_path,
            output_path,
            processing_config
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Post-processing failed")
        
        # Create new media item for processed image
        processed_media = media_service.create_media_item(
            file_path=output_path,
            media_type="image",
            source="ai_generated",
            character_id=media.character_id,
            tags=media.tags
        )
        
        return success_response({
            "media_id": processed_media.id,
            "original_media_id": media_id,
            "file_path": str(output_path),
            "file_name": processed_media.file_name,
            "width": processed_media.width,
            "height": processed_media.height,
            "file_size": processed_media.file_size
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Post-processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/post-process/batch")
async def post_process_batch(
    input_folder: str,
    output_folder: str,
    config: Optional[Dict[str, Any]] = None,
    pipeline: Optional[str] = None
):
    """Batch process images in a folder"""
    try:
        input_path = Path(input_folder)
        output_path = Path(output_folder)
        
        if not input_path.exists():
            raise HTTPException(status_code=404, detail="Input folder not found")
        
        # Get config
        if pipeline:
            processing_config = post_processing_service.get_preset_config(pipeline)
        else:
            processing_config = config or {}
        
        # Process batch
        result = post_processing_service.batch_process(
            input_path,
            output_path,
            processing_config,
            pipeline
        )
        
        return success_response(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch post-processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/post-process/presets")
async def get_post_process_presets():
    """Get available post-processing presets"""
    presets = {
        "instagram": {
            "name": "Instagram",
            "description": "Optimized for Instagram feed (1080x1080, warm tones, vibrant colors)",
            "config": post_processing_service.get_preset_config("instagram")
        },
        "onlyfans": {
            "name": "OnlyFans",
            "description": "High-quality preset for OnlyFans content (warm, romantic tones)",
            "config": post_processing_service.get_preset_config("onlyfans")
        },
        "professional": {
            "name": "Professional",
            "description": "Professional photography preset (natural colors, high quality)",
            "config": post_processing_service.get_preset_config("professional")
        }
    }
    
    return success_response(presets)

@app.post("/api/post-process/video")
async def post_process_video(
    media_id: str,
    config: Optional[Dict[str, Any]] = None,
    db = Depends(get_db)
):
    """Post-process a video"""
    try:
        media_service = MediaService(db, MEDIA_ROOT)
        media = media_service.get_media(media_id)
        
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")
        
        if media.type != "video":
            raise HTTPException(status_code=400, detail="Media is not a video")
        
        input_path = Path(media.file_path)
        if not input_path.exists():
            raise HTTPException(status_code=404, detail="Media file not found")
        
        # Create output path
        output_dir = MEDIA_ROOT / "processed" / media_id
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"processed_{input_path.name}"
        
        # Process video
        processing_config = config or {}
        success = post_processing_service.process_video(
            input_path,
            output_path,
            processing_config
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Video post-processing failed")
        
        # Create new media item for processed video
        processed_media = media_service.create_media_item(
            file_path=output_path,
            media_type="video",
            source="ai_generated",
            character_id=media.character_id,
            tags=media.tags
        )
        
        return success_response({
            "media_id": processed_media.id,
            "original_media_id": media_id,
            "file_path": str(output_path),
            "file_name": processed_media.file_name,
            "file_size": processed_media.file_size
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video post-processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# System Setup & Verification (docs/18-AI-TOOLS-NVIDIA-SETUP.md)
# ============================================================================

@app.get("/api/setup/verify")
async def verify_system_setup():
    """Verify complete system setup according to NVIDIA setup guide"""
    try:
        verification = system_setup_service.verify_complete_setup()
        return success_response(verification)
    except Exception as e:
        logger.error(f"Setup verification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/setup/hardware")
async def get_hardware_info():
    """Get hardware information and requirements"""
    try:
        hardware = system_setup_service.verify_hardware()
        driver = system_setup_service.verify_nvidia_driver()
        cuda = system_setup_service.verify_cuda()
        cudnn = system_setup_service.verify_cudnn()
        
        return success_response({
            "hardware": hardware,
            "nvidia_driver": driver,
            "cuda": cuda,
            "cudnn": cudnn,
            "meets_minimum": hardware.get("meets_minimum", False),
            "meets_recommended": hardware.get("meets_recommended", False)
        })
    except Exception as e:
        logger.error(f"Hardware info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/setup/comfyui")
async def get_comfyui_status():
    """Get ComfyUI installation status"""
    try:
        comfyui_status = system_setup_service.verify_comfyui_installation()
        return success_response(comfyui_status)
    except Exception as e:
        logger.error(f"ComfyUI status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =========================================
# COMPREHENSIVE MODEL MANAGEMENT API
# Based on docs/33-MODELS-AND-CHECKPOINTS-COMPLETE-GUIDE.md
# =========================================

@app.get("/api/models")
async def list_all_models(category: Optional[str] = Query(None, description="Filter by category: image, video, face, post_processing, controlnet")):
    """List all models organized by category"""
    try:
        all_models = model_management_service.list_all_models(category)
        storage_info = model_management_service.get_storage_info()
        download_status = model_management_service.get_download_status()
        
        return success_response({
            "models": all_models,
            "storage": storage_info,
            "download_status": download_status
        })
    except Exception as e:
        logger.error(f"List models error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models/installed")
async def list_installed_models(category: Optional[str] = Query(None)):
    """List only installed models"""
    try:
        installed = model_management_service.list_installed_models(category)
        return success_response({
            "models": installed,
            "count": len(installed)
        })
    except Exception as e:
        logger.error(f"List installed models error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models/recommended")
async def get_recommended_models():
    """Get recommended models from the complete guide"""
    try:
        all_models = model_management_service.list_all_models()
        # Filter to show only recommended/high priority models
        recommended = {}
        for category, models in all_models.items():
            recommended[category] = [m for m in models if m.get("priority") in ["high", "medium"]]
        
        return success_response(recommended)
    except Exception as e:
        logger.error(f"Recommended models error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models/setups")
async def get_recommended_setups():
    """Get recommended model setups (best quality, best speed, balanced, etc.)"""
    try:
        setups = model_management_service.get_recommended_setups()
        return success_response(setups)
    except Exception as e:
        logger.error(f"Recommended setups error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models/setups/{use_case}")
async def get_setup_recommendation(use_case: str):
    """Get model setup recommendation for a specific use case"""
    try:
        setup = model_management_service.get_setup_recommendation(use_case)
        if not setup:
            raise HTTPException(status_code=404, detail=f"Use case not found: {use_case}")
        return success_response(setup)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Setup recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models/{model_key}")
async def get_model_info(model_key: str):
    """Get detailed information about a specific model"""
    try:
        model_info = model_management_service.get_model_info(model_key)
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model not found: {model_key}")
        return success_response(model_info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Model info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models/{model_key}/verify")
async def verify_model(model_key: str):
    """Verify model installation and integrity"""
    try:
        verification = model_management_service.verify_model(model_key)
        return success_response(verification)
    except Exception as e:
        logger.error(f"Model verification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models/storage/info")
async def get_storage_info():
    """Get comprehensive storage information"""
    try:
        storage_info = model_management_service.get_storage_info()
        return success_response(storage_info)
    except Exception as e:
        logger.error(f"Storage info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models/download/status")
async def get_download_status():
    """Get download status for all models"""
    try:
        status = model_management_service.get_download_status()
        return success_response(status)
    except Exception as e:
        logger.error(f"Download status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/models/{model_key}/download")
async def download_model(model_key: str):
    """Download a model (returns instructions - actual download via script)"""
    try:
        model_info = model_management_service.get_model_info(model_key)
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model not found: {model_key}")
        
        if model_info.get("installed"):
            return success_response({
                "success": True,
                "message": "Model already installed",
                "path": model_info.get("installed_path")
            })
        
        # Return download instructions
        return success_response({
            "success": False,
            "message": "Use download script for automatic download",
            "instructions": {
                "script": ".\\download-all-models-complete.ps1",
                "model_key": model_key,
                "url": model_info.get("url"),
                "source": model_info.get("source"),
                "target": model_info.get("target"),
                "size_gb": model_info.get("size_gb")
            }
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Model download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/models/{model_key}")
async def delete_model(model_key: str):
    """Delete a model"""
    try:
        result = model_management_service.delete_model(model_key)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to delete model"))
        return success_response(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Model deletion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/setup/face-consistency")
async def get_face_consistency_status():
    """Get face consistency tools status (IP-Adapter, InstantID)"""
    try:
        status = system_setup_service.verify_face_consistency_setup()
        return success_response(status)
    except Exception as e:
        logger.error(f"Face consistency status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/setup/video-generation")
async def get_video_generation_status():
    """Get video generation tools status (AnimateDiff, SVD)"""
    try:
        status = system_setup_service.verify_video_generation_setup()
        return success_response(status)
    except Exception as e:
        logger.error(f"Video generation status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/setup/post-processing")
async def get_post_processing_status():
    """Get post-processing tools status"""
    try:
        status = system_setup_service.verify_post_processing_setup()
        return success_response(status)
    except Exception as e:
        logger.error(f"Post-processing status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/quality/checklist")
async def get_quality_checklist():
    """Get the realism checklist"""
    try:
        checklist = quality_assurance_service.get_checklist()
        return success_response(checklist)
    except Exception as e:
        logger.error(f"Quality checklist error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/quality/check")
async def check_image_quality(
    image_path: str,
    manual_review: Optional[Dict[str, Any]] = None
):
    """Run quality check on an image"""
    try:
        image_file = Path(image_path)
        if not image_file.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        
        result = quality_assurance_service.quality_score_image(image_file, manual_review)
        return success_response(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quality check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/quality/checklist")
async def run_realism_checklist(
    image_path: str,
    manual_scores: Optional[Dict[str, float]] = None
):
    """Run realism checklist on an image"""
    try:
        image_file = Path(image_path)
        if not image_file.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        
        result = quality_assurance_service.run_realism_checklist(image_file, manual_scores)
        return success_response(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Realism checklist error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/quality/ai-detection")
async def test_ai_detection(image_path: str):
    """Test image against AI detection"""
    try:
        image_file = Path(image_path)
        if not image_file.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        
        result = quality_assurance_service.test_ai_detection(image_file)
        return success_response(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI detection test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/quality/batch-check")
async def batch_quality_check(
    image_paths: List[str],
    manual_reviews: Optional[Dict[str, Dict[str, Any]]] = None
):
    """Run quality checks on multiple images"""
    try:
        image_files = [Path(p) for p in image_paths]
        for img_file in image_files:
            if not img_file.exists():
                raise HTTPException(status_code=404, detail=f"Image not found: {img_file}")
        
        result = quality_assurance_service.batch_quality_check(image_files, manual_reviews)
        return success_response(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch quality check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# System Information
# ============================================================================

@app.get("/api/system/stats")
async def get_system_stats():
    """Get system statistics"""
    stats = comfyui_client.get_system_stats()
    
    # Get hardware info from setup service
    hardware = system_setup_service.verify_hardware()
    
    # Get performance metrics
    perf_report = performance_monitor.get_performance_report()
    
    return success_response({
        "comfyui": {
            "connected": comfyui_client.check_connection(),
            "version": "1.0.0"  # TODO: Get from ComfyUI
        },
        "gpu": {
            "available": hardware["gpu_available"],
            "name": hardware["gpu_name"] or "NVIDIA GPU",
            "memory_total": hardware["gpu_memory_total"],
            "memory_used": hardware["gpu_memory_used"],
            "memory_free": hardware["gpu_memory_free"]
        },
        "storage": {
            "total": 0,  # TODO: Get storage stats
            "used": 0,
            "free": hardware.get("storage_free", 0)
        },
        "queue": {
            "pending": 0,  # TODO: Get queue stats
            "processing": 0,
            "completed_today": 0
        },
        "performance": perf_report
    })

@app.get("/api/performance/monitor")
async def get_performance_monitor():
    """Get performance monitoring data"""
    try:
        report = performance_monitor.get_performance_report()
        return success_response(report)
    except Exception as e:
        logger.error(f"Performance monitoring error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/performance/optimize-gpu")
async def optimize_gpu_memory():
    """Optimize GPU memory usage"""
    try:
        success = performance_monitor.optimize_gpu_memory()
        return success_response({
            "optimized": success,
            "message": "GPU memory optimized" if success else "GPU optimization not available"
        })
    except Exception as e:
        logger.error(f"GPU optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Troubleshooting (docs/30-TROUBLESHOOTING-COMPLETE.md)
# ============================================================================

@app.get("/api/troubleshooting/diagnostics")
async def run_diagnostics():
    """Run comprehensive system diagnostics"""
    try:
        diagnostics = troubleshooting_service.run_full_diagnostics()
        return success_response(diagnostics)
    except Exception as e:
        logger.error(f"Diagnostics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/troubleshooting/diagnose-error")
async def diagnose_error(
    error_code: str,
    error_message: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
):
    """Diagnose an error and provide resolution"""
    try:
        diagnosis = troubleshooting_service.diagnose_error(
            error_code=error_code,
            error_message=error_message or "",
            context=context or {}
        )
        return success_response(diagnosis)
    except Exception as e:
        logger.error(f"Error diagnosis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/troubleshooting/error-codes")
async def list_error_codes():
    """List all available error codes"""
    try:
        error_codes = troubleshooting_service.list_all_error_codes()
        return success_response({
            "error_codes": error_codes,
            "count": len(error_codes)
        })
    except Exception as e:
        logger.error(f"List error codes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/troubleshooting/error-codes/{error_code}")
async def get_error_resolution(error_code: str):
    """Get resolution for a specific error code"""
    try:
        resolution = troubleshooting_service.get_error_resolution(error_code)
        if not resolution:
            raise HTTPException(status_code=404, detail="Error code not found")
        return success_response(resolution)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get error resolution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/troubleshooting/check-quality-issues")
async def check_quality_issues(settings: Optional[Dict[str, Any]] = None):
    """Check for common generation quality issues"""
    try:
        issues = troubleshooting_service.check_generation_quality_issues(settings=settings)
        return success_response(issues)
    except Exception as e:
        logger.error(f"Quality check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/troubleshooting/check-face-consistency-issues")
async def check_face_consistency_issues(
    reference_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
):
    """Check for face consistency issues"""
    try:
        from pathlib import Path
        ref_path = Path(reference_path) if reference_path else None
        issues = troubleshooting_service.check_face_consistency_issues(
            reference_path=ref_path,
            config=config
        )
        return success_response(issues)
    except Exception as e:
        logger.error(f"Face consistency check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/troubleshooting/check-performance")
async def check_performance_issues():
    """Check for performance issues"""
    try:
        issues = troubleshooting_service.check_performance_issues()
        return success_response(issues)
    except Exception as e:
        logger.error(f"Performance check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/troubleshooting/gpu-diagnostics")
async def get_gpu_diagnostics():
    """Get GPU diagnostic information"""
    try:
        gpu_info = troubleshooting_service._diagnose_gpu()
        return success_response(gpu_info)
    except Exception as e:
        logger.error(f"GPU diagnostics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/troubleshooting/comfyui-diagnostics")
async def get_comfyui_diagnostics():
    """Get ComfyUI diagnostic information"""
    try:
        comfyui_info = troubleshooting_service._diagnose_comfyui()
        return success_response(comfyui_info)
    except Exception as e:
        logger.error(f"ComfyUI diagnostics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/troubleshooting/disk-diagnostics")
async def get_disk_diagnostics():
    """Get disk space diagnostic information"""
    try:
        disk_info = troubleshooting_service._diagnose_disk_space()
        return success_response(disk_info)
    except Exception as e:
        logger.error(f"Disk diagnostics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/troubleshooting/python-diagnostics")
async def get_python_diagnostics():
    """Get Python version diagnostic information"""
    try:
        python_info = troubleshooting_service._diagnose_python()
        return success_response(python_info)
    except Exception as e:
        logger.error(f"Python diagnostics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Prompt Engineering
# ============================================================================

@app.post("/api/prompts/build")
async def build_prompt(
    request: Request,
    db = Depends(get_db)
):
    """Build a prompt using advanced prompt engineering"""
    try:
        # Get request body
        body = await request.json()
        
        # Extract parameters from body
        character_id = body.get("character_id")
        variation = body.get("variation", "default")
        platform = body.get("platform")
        base_prompt = body.get("base_prompt")
        
        # Check if using simple format (flat strings) - for frontend compatibility
        character_description = body.get("character_description")
        pose_value = body.get("pose")
        setting_value = body.get("setting")
        style_value = body.get("style")
        quality_modifiers = body.get("quality_modifiers")
        
        # Advanced format (nested objects)
        subject = body.get("subject")
        appearance = body.get("appearance")
        quality = body.get("quality")
        technical = body.get("technical")
        custom_modifiers = body.get("custom_modifiers")
        
        # Determine if using simple format (strings) or advanced format (dicts)
        is_simple_format = (
            (character_description and isinstance(character_description, str)) or
            (pose_value and isinstance(pose_value, str)) or
            (setting_value and isinstance(setting_value, str)) or
            (style_value and isinstance(style_value, str))
        ) and not (isinstance(pose_value, dict) or isinstance(setting_value, dict) or isinstance(style_value, dict))
        
        # If character_id is provided, use character config
        if character_id:
            character_service = CharacterService(db, CHARACTERS_ROOT)
            character = character_service.get_character(character_id)
            if character:
                character_config = character.settings or {}
                platform_enum = None
                if platform:
                    try:
                        platform_enum = Platform(platform.lower())
                    except ValueError:
                        pass
                
                prompt, negative_prompt = prompt_engineering_service.build_prompt_from_character_config(
                    character_config,
                    variation=variation,
                    platform=platform_enum
                )
                
                return success_response({
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "source": "character_config"
                })
        
        # Handle simple format (flat strings) - for frontend compatibility
        if is_simple_format:
            from services.prompt_service import PromptService
            prompt_service = PromptService()
            prompt = prompt_service.build_prompt(
                character_description=character_description,
                pose=pose_value if isinstance(pose_value, str) else None,
                setting=setting_value if isinstance(setting_value, str) else None,
                style=style_value if isinstance(style_value, str) else None,
                platform=platform,
                quality_modifiers=quality_modifiers
            )
            negative_prompt = prompt_service.build_negative_prompt(platform=platform)
            
            return success_response({
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "source": "components"
            })
        
        # Build from advanced components (nested objects)
        subject_obj = None
        if subject:
            subject_obj = SubjectDescription(**subject)
        
        appearance_obj = None
        if appearance:
            appearance_obj = AppearanceDetails(**appearance)
        
        pose_obj = None
        if pose_value and isinstance(pose_value, dict):
            pose_obj = PoseAction(**pose_value)
        
        setting_obj = None
        if setting_value and isinstance(setting_value, dict):
            setting_obj = SettingEnvironment(**setting_value)
        
        style_obj = None
        if style_value and isinstance(style_value, dict):
            # Handle photography style enum
            if "photography_style" in style_value and isinstance(style_value["photography_style"], str):
                try:
                    style_value["photography_style"] = PhotographyStyle(style_value["photography_style"])
                except ValueError:
                    style_value["photography_style"] = None
            style_obj = StyleModifiers(**style_value)
        
        quality_obj = None
        if quality:
            quality_obj = QualityModifiers(**quality)
        
        technical_obj = None
        if technical:
            technical_obj = TechnicalSpecs(**technical)
        
        platform_enum = None
        if platform:
            try:
                platform_enum = Platform(platform.lower())
            except ValueError:
                pass
        
        prompt = prompt_engineering_service.build_complete_prompt(
            subject=subject_obj,
            appearance=appearance_obj,
            pose=pose_obj,
            setting=setting_obj,
            style=style_obj,
            quality=quality_obj,
            technical=technical_obj,
            platform=platform_enum,
            base_prompt=base_prompt,
            custom_modifiers=custom_modifiers
        )
        
        negative_prompt = prompt_engineering_service.get_negative_prompt(platform=platform_enum)
        
        return success_response({
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "source": "components"
        })
    
    except Exception as e:
        logger.error(f"Prompt building error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/prompts/optimize")
async def optimize_prompt_endpoint(
    prompt: str,
    optimization_level: str = "standard"
):
    """Optimize a prompt"""
    try:
        optimized = prompt_engineering_service.optimize_prompt(prompt, optimization_level)
        return success_response({
            "original": prompt,
            "optimized": optimized
        })
    except Exception as e:
        logger.error(f"Prompt optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/prompts/weight")
async def apply_prompt_weighting(
    prompt: str,
    weights: Dict[str, float]
):
    """Apply weighting to prompt terms"""
    try:
        weighted = prompt_engineering_service.apply_prompt_weighting(prompt, weights)
        return success_response({
            "original": prompt,
            "weighted": weighted
        })
    except Exception as e:
        logger.error(f"Prompt weighting error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/prompts/variations")
async def generate_prompt_variations(
    base_prompt: str,
    variation_type: str = "pose",
    variation_options: Optional[List[str]] = None,
    count: int = 5
):
    """Generate prompt variations"""
    try:
        variations = []
        if variation_options:
            for option in variation_options[:count]:
                variation = prompt_engineering_service.generate_prompt_variation(
                    base_prompt,
                    variation_type=variation_type,
                    variation_options=[option]
                )
                variations.append({
                    "variation": option,
                    "prompt": variation
                })
        else:
            # Generate random variations
            for i in range(count):
                variation = prompt_engineering_service.generate_prompt_variation(
                    base_prompt,
                    variation_type=variation_type
                )
                variations.append({
                    "variation": f"variation_{i+1}",
                    "prompt": variation
                })
        
        return success_response({
            "base_prompt": base_prompt,
            "variations": variations
        })
    except Exception as e:
        logger.error(f"Prompt variation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/prompts/ab-test")
async def create_ab_test_prompts(
    base_prompt: str,
    test_variables: Dict[str, List[str]]
):
    """Create A/B test prompt variations"""
    try:
        variations = prompt_engineering_service.create_ab_test_prompts(
            base_prompt,
            test_variables
        )
        return success_response({
            "base_prompt": base_prompt,
            "variations": variations
        })
    except Exception as e:
        logger.error(f"A/B test prompt creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prompts/negative")
async def get_negative_prompt(
    platform: Optional[str] = None,
    include_standard: bool = True,
    custom_negatives: Optional[List[str]] = None
):
    """Get negative prompt for platform"""
    try:
        platform_enum = None
        if platform:
            try:
                platform_enum = Platform(platform.lower())
            except ValueError:
                pass
        
        negative_prompt = prompt_engineering_service.get_negative_prompt(
            platform=platform_enum,
            include_standard=include_standard,
            custom_negatives=custom_negatives
        )
        
        return success_response({
            "negative_prompt": negative_prompt,
            "platform": platform
        })
    except Exception as e:
        logger.error(f"Negative prompt generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prompts/platforms")
async def get_platform_styles():
    """Get available platforms and their styles"""
    platforms = {}
    for platform in Platform:
        style = prompt_engineering_service.get_platform_style(platform)
        negative = prompt_engineering_service.get_negative_prompt(platform=platform, include_standard=False)
        platforms[platform.value] = {
            "name": platform.value.title(),
            "style_modifiers": style,
            "negative_additions": negative
        }
    
    return success_response({
        "platforms": platforms
    })


@app.get("/api/prompts/templates")
async def get_prompt_templates():
    """Get prompt templates and modifiers"""
    return success_response({
        "quality_modifiers": PromptEngineeringService.ESSENTIAL_QUALITY_MODIFIERS,
        "realism_boosters": PromptEngineeringService.REALISM_BOOSTERS,
        "camera_modifiers": PromptEngineeringService.CAMERA_MODIFIERS,
        "lighting_modifiers": PromptEngineeringService.LIGHTING_MODIFIERS,
        "color_modifiers": PromptEngineeringService.COLOR_MODIFIERS,
        "standard_negative": PromptEngineeringService.STANDARD_NEGATIVE_PROMPT
    })

# ============================================================================
# WebSocket
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    job_id = None
    batch_job_id = None
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "subscribe":
                job_id = message.get("job_id")
                if job_id:
                    await websocket_service.connect(websocket, job_id)
                    # Start monitoring if not already
                    db = next(get_db())
                    generation_service = GenerationService(db, comfyui_client)
                    websocket_service.start_monitoring(
                        job_id,
                        comfyui_client,
                        generation_service,
                        db
                    )
            
            elif message.get("type") == "subscribe_batch":
                batch_job_id = message.get("batch_job_id")
                if batch_job_id:
                    await websocket_service.connect(websocket, batch_job_id)
            
            elif message.get("type") == "unsubscribe":
                if job_id:
                    websocket_service.disconnect(websocket, job_id)
                    job_id = None
                if batch_job_id:
                    websocket_service.disconnect(websocket, batch_job_id)
                    batch_job_id = None
            
    except WebSocketDisconnect:
        if job_id:
            websocket_service.disconnect(websocket, job_id)
        if batch_job_id:
            websocket_service.disconnect(websocket, batch_job_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

# ============================================================================
# Prompt Engineering
# ============================================================================

# Duplicate endpoint removed - functionality merged into the main /api/prompts/build endpoint above

@app.post("/api/prompts/optimize")
async def optimize_prompt(
    prompt: str,
    target_quality: str = "high"
):
    """Optimize existing prompt"""
    prompt_service = PromptService()
    optimized = prompt_service.optimize_prompt(prompt, target_quality)
    
    return success_response({
        "original": prompt,
        "optimized": optimized
    })

@app.post("/api/prompts/variations")
async def generate_prompt_variations(
    base_prompt: str,
    count: int = 5
):
    """Generate prompt variations"""
    prompt_service = PromptService()
    variations = prompt_service.generate_variations(base_prompt, count)
    
    return success_response({
        "base": base_prompt,
        "variations": variations
    })

# ============================================================================
# Quality Assurance
# ============================================================================

@app.post("/api/quality/score")
async def score_content(
    content_path: str,
    content_type: str = "image"
):
    """Score content quality"""
    quality_service = QualityService()
    scores = quality_service.score_content(Path(content_path), content_type)
    
    return success_response(scores)

@app.post("/api/quality/validate")
async def validate_content(
    content_path: str,
    content_type: str = "image",
    min_score: float = 8.0
):
    """Validate content meets quality standards"""
    quality_service = QualityService()
    result = quality_service.validate_content(
        Path(content_path),
        content_type,
        min_score
    )
    
    return success_response(result)

# ============================================================================
# Quality Assurance System (docs/28-QUALITY-ASSURANCE-SYSTEM.md)
# ============================================================================

@app.post("/api/qa/score")
async def score_quality(
    media_id: str,
    db = Depends(get_db)
):
    """Score content quality using comprehensive QA system"""
    try:
        from services.media_service import MediaService
        media_service = MediaService(db, MEDIA_ROOT)
        media = media_service.get_media(media_id)
        
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")
        
        media_path = Path(media.file_path)
        if not media_path.exists():
            raise HTTPException(status_code=404, detail="Media file not found")
        
        # Score quality
        scorer = QualityScorer()
        scores = scorer.score(media_path, media.type)
        
        # Save to database
        from models import QualityScore
        quality_score = QualityScore(
            media_id=media_id,
            overall_score=scores.get('overall', 0.0) / 10.0,  # Convert to 0-1 scale
            face_quality_score=scores.get('face', 0.0) / 10.0,
            technical_score=scores.get('technical', 0.0) / 10.0,
            realism_score=scores.get('realism', 0.0) / 10.0,
            passed=scores.get('passed', False),
            auto_approved=scores.get('auto_approved', False),
            metadata=scores
        )
        db.add(quality_score)
        db.commit()
        db.refresh(quality_score)
        
        return success_response({
            "quality_score_id": quality_score.id,
            "media_id": media_id,
            "scores": scores,
            "passed": scores.get('passed', False),
            "auto_approved": scores.get('auto_approved', False)
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quality scoring error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/qa/detection-test")
async def test_detection(
    media_id: str,
    db = Depends(get_db)
):
    """Test content against AI detection tools"""
    try:
        from services.media_service import MediaService
        media_service = MediaService(db, MEDIA_ROOT)
        media = media_service.get_media(media_id)
        
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")
        
        media_path = Path(media.file_path)
        if not media_path.exists():
            raise HTTPException(status_code=404, detail="Media file not found")
        
        # Test detection
        tester = DetectionTester()
        results = tester.test(media_path)
        
        # Save to database
        from models import DetectionTest
        test_record = DetectionTest(
            media_id=media_id,
            test_type="automated",
            threshold=results['threshold'],
            average_score=results['average'],
            passed=results['passed'],
            results=results['scores']
        )
        db.add(test_record)
        db.commit()
        db.refresh(test_record)
        
        return success_response({
            "test_id": test_record.id,
            "media_id": media_id,
            "results": results
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detection testing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/qa/metrics")
async def get_quality_metrics(
    days: int = Query(7, ge=1, le=90),
    db = Depends(get_db)
):
    """Get quality metrics and KPIs"""
    try:
        metrics = QualityMetrics(db)
        all_metrics = metrics.get_all_metrics(days=days)
        return success_response(all_metrics)
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/qa/dashboard")
async def get_quality_dashboard(
    days: int = Query(7, ge=1, le=90),
    db = Depends(get_db)
):
    """Get quality dashboard data"""
    try:
        dashboard = QualityDashboard(db)
        summary = dashboard.get_summary()
        trends = dashboard.get_trends(days=days)
        alerts = dashboard.get_alerts()
        
        return success_response({
            "summary": summary,
            "trends": trends,
            "alerts": alerts
        })
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/qa/improvements")
async def get_improvement_analysis(
    days: int = Query(7, ge=1, le=90),
    db = Depends(get_db)
):
    """Get quality improvement analysis"""
    try:
        improver = QualityImprover(db)
        analysis = improver.analyze_rejections(period_days=days)
        return success_response(analysis)
    except Exception as e:
        logger.error(f"Improvement analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/qa/review")
async def create_quality_review(
    media_id: str,
    reviewer_id: str,
    decision: str,
    quality_score: Optional[float] = None,
    face_score: Optional[float] = None,
    technical_score: Optional[float] = None,
    realism_score: Optional[float] = None,
    notes: Optional[str] = None,
    checklist_scores: Optional[Dict[str, float]] = None,
    db = Depends(get_db)
):
    """Create a manual quality review"""
    try:
        from services.media_service import MediaService
        media_service = MediaService(db, MEDIA_ROOT)
        media = media_service.get_media(media_id)
        
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")
        
        if decision not in ['approve', 'reject', 'improve']:
            raise HTTPException(status_code=400, detail="Invalid decision")
        
        from models import QualityReview
        review = QualityReview(
            media_id=media_id,
            reviewer_id=reviewer_id,
            review_type="manual",
            quality_score=quality_score / 10.0 if quality_score else None,
            face_score=face_score / 10.0 if face_score else None,
            technical_score=technical_score / 10.0 if technical_score else None,
            realism_score=realism_score / 10.0 if realism_score else None,
            decision=decision,
            notes=notes,
            checklist_scores=checklist_scores or {},
            completed_at=datetime.utcnow()
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        
        return success_response({
            "review_id": review.id,
            "media_id": media_id,
            "decision": decision
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Review creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/qa/reject")
async def reject_content(
    media_id: str,
    rejection_reason: str,
    rejection_category: Optional[str] = None,
    quality_score: Optional[float] = None,
    detection_score: Optional[float] = None,
    details: Optional[Dict[str, Any]] = None,
    action_taken: Optional[str] = None,
    db = Depends(get_db)
):
    """Log content rejection"""
    try:
        from services.media_service import MediaService
        media_service = MediaService(db, MEDIA_ROOT)
        media = media_service.get_media(media_id)
        
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")
        
        if rejection_reason not in ['quality', 'detection', 'technical']:
            raise HTTPException(status_code=400, detail="Invalid rejection reason")
        
        from models import RejectionLog
        rejection = RejectionLog(
            media_id=media_id,
            rejection_reason=rejection_reason,
            rejection_category=rejection_category,
            quality_score=quality_score / 10.0 if quality_score else None,
            detection_score=detection_score,
            details=details or {},
            action_taken=action_taken
        )
        db.add(rejection)
        db.commit()
        db.refresh(rejection)
        
        return success_response({
            "rejection_id": rejection.id,
            "media_id": media_id,
            "reason": rejection_reason
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rejection logging error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/qa/batch-test")
async def batch_test_quality(
    media_ids: List[str],
    db = Depends(get_db)
):
    """Batch test quality for multiple media items"""
    try:
        from services.media_service import MediaService
        media_service = MediaService(db, MEDIA_ROOT)
        scorer = QualityScorer()
        tester = DetectionTester()
        
        results = []
        for media_id in media_ids:
            media = media_service.get_media(media_id)
            if not media:
                continue
            
            media_path = Path(media.file_path)
            if not media_path.exists():
                continue
            
            # Score quality
            quality_scores = scorer.score(media_path, media.type)
            
            # Test detection
            detection_results = tester.test(media_path)
            
            # Overall assessment
            passed = (
                quality_scores.get('overall', 0) >= 8.0 and
                detection_results.get('passed', False)
            )
            
            results.append({
                "media_id": media_id,
                "quality": quality_scores,
                "detection": detection_results,
                "passed": passed
            })
        
        # Summary
        passed_count = sum(1 for r in results if r['passed'])
        total = len(results)
        
        return success_response({
            "results": results,
            "summary": {
                "total": total,
                "passed": passed_count,
                "pass_rate": (passed_count / total * 100) if total > 0 else 0
            }
        })
    except Exception as e:
        logger.error(f"Batch testing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Anti-Detection
# ============================================================================

@app.post("/api/anti-detection/process")
async def apply_anti_detection(
    image_path: str,
    config: Optional[Dict[str, Any]] = None
):
    """Apply anti-detection techniques to image"""
    anti_detection_service = AntiDetectionService()
    config = config or {
        "remove_metadata": True,
        "add_imperfections": True,
        "vary_quality": True,
        "remove_ai_signatures": True,
        "add_realistic_noise": True,
        "normalize_colors": True
    }
    
    success = anti_detection_service.process_image(Path(image_path), config)
    
    if success:
        return success_response({
            "processed": True,
            "output_path": str(Path(image_path).parent / f"processed_{Path(image_path).name}")
        })
    else:
        raise HTTPException(status_code=500, detail="Anti-detection processing failed")

@app.post("/api/anti-detection/test")
async def test_detection(
    image_path: str,
    detection_tools: Optional[List[str]] = None
):
    """Test image against detection tools"""
    anti_detection_service = AntiDetectionService()
    results = anti_detection_service.test_detection(
        Path(image_path),
        detection_tools
    )
    
    return success_response(results)

# ============================================================================
# Anti-Detection Endpoints (Comprehensive Implementation)
# ============================================================================

@app.post("/api/anti-detection/test")
async def test_detection(
    media_id: str,
    tools: Optional[List[str]] = None,
    threshold: Optional[float] = Query(0.3, ge=0.0, le=1.0),
    db = Depends(get_db)
):
    """Test media against detection tools"""
    try:
        media_service = MediaService(db, MEDIA_ROOT)
        media = media_service.get_media(media_id)
        
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")
        
        media_path = Path(media.file_path)
        if not media_path.exists():
            raise HTTPException(status_code=404, detail="Media file not found")
        
        # Run detection test
        results = anti_detection_service.test_detection(
            media_path,
            tools=tools,
            threshold=threshold
        )
        
        # Save test results to database
        from models import DetectionTest
        test_record = DetectionTest(
            media_id=media_id,
            test_type="manual",
            threshold=threshold,
            average_score=results["average_score"],
            passed=results["passed"],
            results=results["results"],
            recommendations=results["recommendations"]
        )
        db.add(test_record)
        db.commit()
        
        return success_response({
            "test_id": test_record.id,
            "media_id": media_id,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detection test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/anti-detection/pre-publication-check")
async def pre_publication_check(
    media_id: str,
    threshold: Optional[float] = Query(0.3, ge=0.0, le=1.0),
    db = Depends(get_db)
):
    """Comprehensive pre-publication anti-detection check"""
    try:
        media_service = MediaService(db, MEDIA_ROOT)
        media = media_service.get_media(media_id)
        
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")
        
        media_path = Path(media.file_path)
        if not media_path.exists():
            raise HTTPException(status_code=404, detail="Media file not found")
        
        # Run comprehensive check
        check_results = anti_detection_service.pre_publication_test(
            media_path,
            threshold=threshold
        )
        
        # Save test results
        from models import DetectionTest
        test_record = DetectionTest(
            media_id=media_id,
            test_type="pre_publication",
            threshold=threshold,
            average_score=check_results["detection"]["average_score"],
            passed=check_results["passed"],
            results=check_results["detection"]["results"],
            recommendations=check_results["detection"]["recommendations"],
            metadata_check=check_results["metadata"],
            quality_check=check_results["quality"]
        )
        db.add(test_record)
        db.commit()
        
        return success_response({
            "test_id": test_record.id,
            "media_id": media_id,
            "ready_for_publication": check_results["ready_for_publication"],
            "passed": check_results["passed"],
            "detection": check_results["detection"],
            "metadata": check_results["metadata"],
            "quality": check_results["quality"],
            "timestamp": check_results["timestamp"]
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pre-publication check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/anti-detection/clean-metadata")
async def clean_metadata(
    media_id: str,
    db = Depends(get_db)
):
    """Clean all metadata from media"""
    try:
        media_service = MediaService(db, MEDIA_ROOT)
        media = media_service.get_media(media_id)
        
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")
        
        media_path = Path(media.file_path)
        if not media_path.exists():
            raise HTTPException(status_code=404, detail="Media file not found")
        
        # Create cleaned version
        cleaned_path = media_path.parent / f"{media_path.stem}_cleaned{media_path.suffix}"
        
        # Clean metadata
        success = metadata_cleaner.clean_all_metadata(media_path, cleaned_path)
        
        if success:
            # Replace original with cleaned version
            media_path.unlink()
            cleaned_path.rename(media_path)
            
            return success_response({
                "media_id": media_id,
                "cleaned": True,
                "message": "Metadata removed successfully"
            })
        else:
            return error_response(
                "CLEAN_FAILED",
                "Failed to clean metadata",
                {"media_id": media_id}
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metadata cleaning error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/anti-detection/tests/{test_id}")
async def get_detection_test(test_id: str, db = Depends(get_db)):
    """Get detection test results"""
    from models import DetectionTest
    test = db.query(DetectionTest).filter(DetectionTest.id == test_id).first()
    
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    return success_response({
        "test_id": test.id,
        "media_id": test.media_id,
        "test_type": test.test_type,
        "threshold": test.threshold,
        "average_score": test.average_score,
        "passed": test.passed,
        "results": test.results,
        "recommendations": test.recommendations,
        "metadata_check": test.metadata_check,
        "quality_check": test.quality_check,
        "created_at": test.created_at.isoformat() if test.created_at else None
    })

@app.get("/api/anti-detection/media/{media_id}/tests")
async def get_media_detection_tests(
    media_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db = Depends(get_db)
):
    """Get all detection tests for a media item"""
    from models import DetectionTest
    from sqlalchemy import desc
    
    tests = db.query(DetectionTest).filter(
        DetectionTest.media_id == media_id
    ).order_by(desc(DetectionTest.created_at)).offset((page - 1) * limit).limit(limit).all()
    
    total = db.query(DetectionTest).filter(DetectionTest.media_id == media_id).count()
    
    test_list = []
    for test in tests:
        test_list.append({
            "test_id": test.id,
            "test_type": test.test_type,
            "threshold": test.threshold,
            "average_score": test.average_score,
            "passed": test.passed,
            "created_at": test.created_at.isoformat() if test.created_at else None
        })
    
    return success_response({
        "tests": test_list,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    })

@app.get("/api/anti-detection/stats")
async def get_detection_stats(db = Depends(get_db)):
    """Get detection statistics"""
    from models import DetectionTest
    from sqlalchemy import func
    
    total_tests = db.query(DetectionTest).count()
    passed_tests = db.query(DetectionTest).filter(DetectionTest.passed == True).count()
    failed_tests = total_tests - passed_tests
    
    avg_score = db.query(func.avg(DetectionTest.average_score)).scalar() or 0.0
    
    # Recent tests (last 24 hours)
    from datetime import timedelta
    recent_cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_tests = db.query(DetectionTest).filter(
        DetectionTest.created_at >= recent_cutoff
    ).count()
    
    return success_response({
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "pass_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0.0,
        "average_score": float(avg_score),
        "recent_tests_24h": recent_tests
    })

# ============================================================================
# Post-Processing
# ============================================================================

# Initialize post-processing service
post_processing_service = PostProcessingService()

@app.post("/api/post-process/image")
async def post_process_image(
    media_id: str,
    config: Optional[Dict[str, Any]] = None,
    pipeline: Optional[str] = None,
    db = Depends(get_db)
):
    """Post-process an image with specified configuration or pipeline"""
    try:
        media_service = MediaService(db, MEDIA_ROOT)
        media = media_service.get_media(media_id)
        
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")
        
        if media.type != "image":
            raise HTTPException(status_code=400, detail="Media is not an image")
        
        input_path = Path(media.file_path)
        if not input_path.exists():
            raise HTTPException(status_code=404, detail="Media file not found")
        
        # Create output path
        output_dir = MEDIA_ROOT / "processed" / media_id
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"processed_{input_path.name}"
        
        # Get config
        if pipeline:
            processing_config = post_processing_service.get_preset_config(pipeline)
        else:
            processing_config = config or {}
        
        # Process image
        success = post_processing_service.process_image(
            input_path,
            output_path,
            processing_config
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Post-processing failed")
        
        # Create new media item for processed image
        processed_media = media_service.create_media_item(
            file_path=output_path,
            media_type="image",
            source="ai_generated",
            character_id=media.character_id,
            tags=media.tags
        )
        
        return success_response({
            "media_id": processed_media.id,
            "original_media_id": media_id,
            "file_path": str(output_path),
            "file_name": processed_media.file_name,
            "width": processed_media.width,
            "height": processed_media.height,
            "file_size": processed_media.file_size
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Post-processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/post-process/batch")
async def post_process_batch(
    input_folder: str,
    output_folder: str,
    config: Optional[Dict[str, Any]] = None,
    pipeline: Optional[str] = None
):
    """Batch process images in a folder"""
    try:
        input_path = Path(input_folder)
        output_path = Path(output_folder)
        
        if not input_path.exists():
            raise HTTPException(status_code=404, detail="Input folder not found")
        
        # Get config
        if pipeline:
            processing_config = post_processing_service.get_preset_config(pipeline)
        else:
            processing_config = config or {}
        
        # Process batch
        result = post_processing_service.batch_process(
            input_path,
            output_path,
            processing_config,
            pipeline
        )
        
        return success_response(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch post-processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/post-process/presets")
async def get_post_process_presets():
    """Get available post-processing presets"""
    presets = {
        "instagram": {
            "name": "Instagram",
            "description": "Optimized for Instagram feed (1080x1080, warm tones, vibrant colors)",
            "config": post_processing_service.get_preset_config("instagram")
        },
        "onlyfans": {
            "name": "OnlyFans",
            "description": "High-quality preset for OnlyFans content (warm, romantic tones)",
            "config": post_processing_service.get_preset_config("onlyfans")
        },
        "professional": {
            "name": "Professional",
            "description": "Professional photography preset (natural colors, high quality)",
            "config": post_processing_service.get_preset_config("professional")
        }
    }
    
    return success_response(presets)

@app.post("/api/post-process/video")
async def post_process_video(
    media_id: str,
    config: Optional[Dict[str, Any]] = None,
    db = Depends(get_db)
):
    """Post-process a video"""
    try:
        media_service = MediaService(db, MEDIA_ROOT)
        media = media_service.get_media(media_id)
        
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")
        
        if media.type != "video":
            raise HTTPException(status_code=400, detail="Media is not a video")
        
        input_path = Path(media.file_path)
        if not input_path.exists():
            raise HTTPException(status_code=404, detail="Media file not found")
        
        # Create output path
        output_dir = MEDIA_ROOT / "processed" / media_id
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"processed_{input_path.name}"
        
        # Process video
        processing_config = config or {}
        success = post_processing_service.process_video(
            input_path,
            output_path,
            processing_config
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Video post-processing failed")
        
        # Create new media item for processed video
        processed_media = media_service.create_media_item(
            file_path=output_path,
            media_type="video",
            source="ai_generated",
            character_id=media.character_id,
            tags=media.tags
        )
        
        return success_response({
            "media_id": processed_media.id,
            "original_media_id": media_id,
            "file_path": str(output_path),
            "file_name": processed_media.file_name,
            "file_size": processed_media.file_size
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video post-processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Platform Integration (docs/27-PLATFORM-INTEGRATION-DETAILED.md)
# ============================================================================

@app.post("/api/platforms/accounts")
async def create_platform_account(
    request: Dict[str, Any],
    db = Depends(get_db)
):
    """Create a platform account"""
    try:
        platform_service = PlatformIntegrationService(db)
        
        account = platform_service.create_account(
            platform=request.get("platform"),
            username=request.get("username"),
            auth_type=request.get("auth_type", "browser"),
            credentials=request.get("credentials", {}),
            display_name=request.get("display_name")
        )
        
        return success_response({
            "account_id": account.id,
            "platform": account.platform,
            "username": account.username,
            "created_at": account.created_at.isoformat() if account.created_at else None
        })
    except Exception as e:
        logger.error(f"Create platform account error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/platforms/accounts")
async def list_platform_accounts(
    platform: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db = Depends(get_db)
):
    """List platform accounts"""
    try:
        platform_service = PlatformIntegrationService(db)
        accounts = platform_service.list_accounts(platform=platform, is_active=is_active)
        
        account_list = []
        for account in accounts:
            account_list.append({
                "id": account.id,
                "platform": account.platform,
                "username": account.username,
                "display_name": account.display_name,
                "is_active": account.is_active,
                "last_used_at": account.last_used_at.isoformat() if account.last_used_at else None,
                "created_at": account.created_at.isoformat() if account.created_at else None
            })
        
        return success_response({
            "accounts": account_list,
            "total": len(account_list)
        })
    except Exception as e:
        logger.error(f"List platform accounts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/platforms/accounts/{account_id}")
async def get_platform_account(account_id: str, db = Depends(get_db)):
    """Get platform account"""
    try:
        platform_service = PlatformIntegrationService(db)
        account = platform_service.get_account(account_id)
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Don't return credentials in response
        credentials = account.credentials.copy()
        credentials.pop("password", None)
        credentials.pop("access_token", None)
        credentials.pop("api_secret", None)
        
        return success_response({
            "id": account.id,
            "platform": account.platform,
            "username": account.username,
            "display_name": account.display_name,
            "auth_type": account.auth_type,
            "is_active": account.is_active,
            "credentials": credentials,  # Sanitized
            "last_used_at": account.last_used_at.isoformat() if account.last_used_at else None,
            "created_at": account.created_at.isoformat() if account.created_at else None
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get platform account error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/platforms/accounts/{account_id}")
async def update_platform_account(
    account_id: str,
    request: Dict[str, Any],
    db = Depends(get_db)
):
    """Update platform account"""
    try:
        platform_service = PlatformIntegrationService(db)
        account = platform_service.update_account(
            account_id=account_id,
            credentials=request.get("credentials"),
            is_active=request.get("is_active")
        )
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        return success_response({
            "account_id": account.id,
            "updated_at": account.updated_at.isoformat() if account.updated_at else None
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update platform account error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/platforms/accounts/{account_id}")
async def delete_platform_account(account_id: str, db = Depends(get_db)):
    """Delete platform account"""
    try:
        platform_service = PlatformIntegrationService(db)
        success = platform_service.delete_account(account_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Account not found")
        
        return success_response({"account_id": account_id, "deleted": True})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete platform account error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/platforms/posts")
async def create_platform_post(
    request: Dict[str, Any],
    db = Depends(get_db)
):
    """Create a platform post"""
    try:
        platform_service = PlatformIntegrationService(db)
        
        scheduled_at = None
        if request.get("scheduled_at"):
            from datetime import datetime
            scheduled_at = datetime.fromisoformat(request["scheduled_at"])
        
        post = platform_service.create_post(
            account_id=request.get("account_id"),
            media_id=request.get("media_id"),
            caption=request.get("caption", ""),
            post_type=request.get("post_type", "photo"),
            scheduled_at=scheduled_at
        )
        
        return success_response({
            "post_id": post.id,
            "platform": post.platform,
            "status": post.status,
            "scheduled_at": post.scheduled_at.isoformat() if post.scheduled_at else None,
            "created_at": post.created_at.isoformat() if post.created_at else None
        })
    except Exception as e:
        logger.error(f"Create platform post error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/platforms/posts/{post_id}/publish")
async def publish_platform_post(post_id: str, db = Depends(get_db)):
    """Publish a platform post"""
    try:
        platform_service = PlatformIntegrationService(db)
        result = platform_service.publish_post(post_id)
        
        return success_response({
            "post_id": post_id,
            "success": result.get("success", True),
            "platform_post_id": result.get("platform_post_id"),
            "platform": result.get("platform")
        })
    except Exception as e:
        logger.error(f"Publish platform post error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/platforms/posts")
async def list_platform_posts(
    account_id: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db = Depends(get_db)
):
    """List platform posts"""
    try:
        platform_service = PlatformIntegrationService(db)
        result = platform_service.list_posts(
            account_id=account_id,
            platform=platform,
            status=status,
            page=page,
            limit=limit
        )
        
        posts = []
        for post in result["posts"]:
            posts.append({
                "id": post.id,
                "platform": post.platform,
                "post_type": post.post_type,
                "caption": post.caption,
                "status": post.status,
                "platform_post_id": post.platform_post_id,
                "scheduled_at": post.scheduled_at.isoformat() if post.scheduled_at else None,
                "published_at": post.published_at.isoformat() if post.published_at else None,
                "failed_at": post.failed_at.isoformat() if post.failed_at else None,
                "error_message": post.error_message,
                "created_at": post.created_at.isoformat() if post.created_at else None
            })
        
        return success_response({
            "posts": posts,
            "total": result["total"],
            "page": result["page"],
            "limit": result["limit"],
            "total_pages": result["total_pages"]
        })
    except Exception as e:
        logger.error(f"List platform posts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/platforms/posts/{post_id}")
async def get_platform_post(post_id: str, db = Depends(get_db)):
    """Get platform post"""
    try:
        platform_service = PlatformIntegrationService(db)
        post = platform_service.get_post(post_id)
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        return success_response({
            "id": post.id,
            "account_id": post.account_id,
            "platform": post.platform,
            "media_id": post.media_id,
            "post_type": post.post_type,
            "caption": post.caption,
            "status": post.status,
            "platform_post_id": post.platform_post_id,
            "scheduled_at": post.scheduled_at.isoformat() if post.scheduled_at else None,
            "published_at": post.published_at.isoformat() if post.published_at else None,
            "failed_at": post.failed_at.isoformat() if post.failed_at else None,
            "error_message": post.error_message,
            "retry_count": post.retry_count,
            "metadata": post.meta_data,
            "created_at": post.created_at.isoformat() if post.created_at else None
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get platform post error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/platforms/rate-limits")
async def get_platform_rate_limits(
    platform: Optional[str] = Query(None),
    action: Optional[str] = Query(None)
):
    """Get platform rate limit information"""
    from services.rate_limiter import PlatformRateLimiter
    
    rate_limiter = PlatformRateLimiter()
    
    if platform and action:
        wait_time = rate_limiter.get_wait_time(platform, action)
        can_request = rate_limiter.can_make_request(platform, action)
        limits = rate_limiter.PLATFORM_LIMITS.get(platform, {}).get(action, {})
        
        return success_response({
            "platform": platform,
            "action": action,
            "can_make_request": can_request,
            "wait_time": wait_time,
            "limits": limits
        })
    else:
        # Return all platform limits
        all_limits = {}
        for platform_name, actions in rate_limiter.PLATFORM_LIMITS.items():
            if not platform or platform_name == platform:
                all_limits[platform_name] = actions
        
        return success_response({
            "platforms": all_limits
        })

# ============================================================================
# Settings Management
# ============================================================================

SETTINGS_FILE = SETTINGS_DIR / "settings.json"

def load_settings():
    """Load settings from file"""
    default_settings = {
        "generation": {
            "default_model": "realisticVisionV60_v60B1.safetensors",
            "default_quality": "balanced",
            "default_steps": 30,
            "default_cfg_scale": 7,
            "auto_upscale": False,
            "auto_face_restore": False,
        },
        "storage": {
            "media_location": str(MEDIA_ROOT),
            "auto_organize": True,
            "cleanup_enabled": False,
            "backup_enabled": False,
        },
        "performance": {
            "batch_size": 1,
            "queue_priority": "normal",
            "gpu_memory_optimization": True,
            "cache_enabled": True,
        },
        "ui": {
            "theme": "dark",
            "language": "en",
            "notifications": True,
            "keyboard_shortcuts": True,
        }
    }
    
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
                user_settings = json.load(f)
                # Merge with defaults
                for key in default_settings:
                    if key in user_settings:
                        default_settings[key].update(user_settings[key])
                return default_settings
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
    
    return default_settings

def save_settings(settings: Dict[str, Any]):
    """Save settings to file"""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
        return False

@app.get("/api/settings")
async def get_settings():
    """Get application settings"""
    try:
        settings = load_settings()
        return success_response(settings)
    except Exception as e:
        logger.error(f"Get settings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/settings")
async def update_settings(request: Dict[str, Any]):
    """Update application settings"""
    try:
        current_settings = load_settings()
        
        # Update only provided sections
        for section in ["generation", "storage", "performance", "ui"]:
            if section in request:
                current_settings[section].update(request[section])
        
        if save_settings(current_settings):
            return success_response(current_settings)
        else:
            raise HTTPException(status_code=500, detail="Failed to save settings")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update settings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_dashboard_stats(db = Depends(get_db)):
    """Get dashboard statistics"""
    try:
        from sqlalchemy import func, and_
        from models import MediaItem, Character
        
        # Count total images
        total_images = db.query(func.count(MediaItem.id)).filter(
            and_(
                MediaItem.type == "image",
                MediaItem.deleted_at.is_(None)
            )
        ).scalar() or 0
        
        # Count total videos
        total_videos = db.query(func.count(MediaItem.id)).filter(
            and_(
                MediaItem.type == "video",
                MediaItem.deleted_at.is_(None)
            )
        ).scalar() or 0
        
        # Count active characters
        total_characters = db.query(func.count(Character.id)).filter(
            Character.deleted_at.is_(None)
        ).scalar() or 0
        
        return success_response({
            "total_images": total_images,
            "total_videos": total_videos,
            "total_characters": total_characters,
        })
    except Exception as e:
        logger.error(f"Get dashboard stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Phase 1: Advanced Post-Processing Endpoints
# ============================================================================

@app.post("/api/post-process/multi-stage-upscale")
async def multi_stage_upscale(request: Dict[str, Any]):
    """Multi-stage upscaling (2x → 4x → 8x)"""
    try:
        image_path = request.get("image_path")
        target_factor = request.get("target_factor", 8)
        
        post_processing_service = PostProcessingService()
        result_path = post_processing_service.multi_stage_upscale(image_path, target_factor)
        
        return success_response({"output_path": result_path})
    except Exception as e:
        logger.error(f"Multi-stage upscale error: {e}")
        return error_response("PROCESSING_FAILED", str(e))

@app.post("/api/post-process/hybrid-face-restoration")
async def hybrid_face_restoration(request: Dict[str, Any]):
    """Hybrid face restoration (GFPGAN + CodeFormer)"""
    try:
        image_path = request.get("image_path")
        gfpgan_weight = request.get("gfpgan_weight", 0.5)
        
        post_processing_service = PostProcessingService()
        result_path = post_processing_service.hybrid_face_restoration(image_path, gfpgan_weight)
        
        return success_response({"output_path": result_path})
    except Exception as e:
        logger.error(f"Hybrid face restoration error: {e}")
        return error_response("PROCESSING_FAILED", str(e))

@app.post("/api/post-process/color-grading")
async def color_grading(request: Dict[str, Any]):
    """Apply color grading presets"""
    try:
        image_path = request.get("image_path")
        preset = request.get("preset", "instagram")
        
        post_processing_service = PostProcessingService()
        result_path = post_processing_service.color_grading_presets(image_path, preset)
        
        return success_response({"output_path": result_path})
    except Exception as e:
        logger.error(f"Color grading error: {e}")
        return error_response("PROCESSING_FAILED", str(e))

# ============================================================================
# Phase 1: Quality Assurance Endpoints
# ============================================================================

@app.post("/api/qa/automated-scoring")
async def automated_quality_scoring(request: Dict[str, Any]):
    """Automated quality scoring (0-10 scale)"""
    try:
        image_path = request.get("image_path")
        
        qa_service = QualityAssuranceService()
        scores = qa_service.automated_quality_scoring(image_path)
        
        return success_response(scores)
    except Exception as e:
        logger.error(f"Quality scoring error: {e}")
        return error_response("QA_FAILED", str(e))

@app.post("/api/qa/artifact-detection")
async def artifact_detection(request: Dict[str, Any]):
    """Automatic artifact detection"""
    try:
        image_path = request.get("image_path")
        
        qa_service = QualityAssuranceService()
        artifacts = qa_service.artifact_detection(image_path)
        
        return success_response(artifacts)
    except Exception as e:
        logger.error(f"Artifact detection error: {e}")
        return error_response("QA_FAILED", str(e))

@app.post("/api/qa/realism-scoring")
async def realism_scoring(request: Dict[str, Any]):
    """AI detection bypass scoring"""
    try:
        image_path = request.get("image_path")
        
        qa_service = QualityAssuranceService()
        realism = qa_service.realism_scoring(image_path)
        
        return success_response(realism)
    except Exception as e:
        logger.error(f"Realism scoring error: {e}")
        return error_response("QA_FAILED", str(e))

@app.post("/api/qa/batch-filter")
async def batch_quality_filter(request: Dict[str, Any]):
    """Batch quality filtering"""
    try:
        image_paths = request.get("image_paths", [])
        min_score = request.get("min_score", 7.0)
        
        qa_service = QualityAssuranceService()
        results = qa_service.batch_quality_filtering(image_paths, min_score)
        
        return success_response(results)
    except Exception as e:
        logger.error(f"Batch filtering error: {e}")
        return error_response("QA_FAILED", str(e))

# ============================================================================
# Enhanced Features API Endpoints
# ============================================================================

# Advanced Generation Features
@app.post("/api/generation/inpainting")
async def inpainting(
    image_path: str,
    mask_path: Optional[str] = None,
    prompt: str = "",
    negative_prompt: str = "",
    settings: Optional[Dict[str, Any]] = None,
    db = Depends(get_db)
):
    """Perform inpainting on an image"""
    try:
        from services.advanced_generation_service import AdvancedGenerationService
        service = AdvancedGenerationService(comfyui_client)
        result = service.inpainting(
            image_path=image_path,
            mask_path=mask_path,
            prompt=prompt,
            negative_prompt=negative_prompt,
            settings=settings
        )
        return success_response(result)
    except Exception as e:
        logger.error(f"Inpainting error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generation/outpainting")
async def outpainting(
    image_path: str,
    direction: str = "all",
    extension_size: int = 512,
    prompt: str = "",
    negative_prompt: str = "",
    settings: Optional[Dict[str, Any]] = None,
    db = Depends(get_db)
):
    """Extend image boundaries (outpainting)"""
    try:
        from services.advanced_generation_service import AdvancedGenerationService
        service = AdvancedGenerationService(comfyui_client)
        result = service.outpainting(
            image_path=image_path,
            direction=direction,
            extension_size=extension_size,
            prompt=prompt,
            negative_prompt=negative_prompt,
            settings=settings
        )
        return success_response(result)
    except Exception as e:
        logger.error(f"Outpainting error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generation/image-to-image")
async def image_to_image(
    image_path: str,
    prompt: str = "",
    negative_prompt: str = "",
    strength: float = 0.75,
    settings: Optional[Dict[str, Any]] = None,
    db = Depends(get_db)
):
    """Transform image using img2img"""
    try:
        from services.advanced_generation_service import AdvancedGenerationService
        service = AdvancedGenerationService(comfyui_client)
        result = service.image_to_image(
            image_path=image_path,
            prompt=prompt,
            negative_prompt=negative_prompt,
            strength=strength,
            settings=settings
        )
        return success_response(result)
    except Exception as e:
        logger.error(f"Image-to-image error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generation/controlnet")
async def controlnet_generation(
    control_image_path: str,
    control_type: str = "pose",
    prompt: str = "",
    negative_prompt: str = "",
    control_strength: float = 1.0,
    settings: Optional[Dict[str, Any]] = None,
    db = Depends(get_db)
):
    """Generate using ControlNet"""
    try:
        from services.advanced_generation_service import AdvancedGenerationService
        service = AdvancedGenerationService(comfyui_client)
        result = service.controlnet_generation(
            control_image_path=control_image_path,
            control_type=control_type,
            prompt=prompt,
            negative_prompt=negative_prompt,
            control_strength=control_strength,
            settings=settings
        )
        return success_response(result)
    except Exception as e:
        logger.error(f"ControlNet error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generation/style-transfer")
async def style_transfer(
    content_image_path: str,
    style_image_path: str,
    strength: float = 0.5,
    settings: Optional[Dict[str, Any]] = None,
    db = Depends(get_db)
):
    """Apply style transfer"""
    try:
        from services.advanced_generation_service import AdvancedGenerationService
        service = AdvancedGenerationService(comfyui_client)
        result = service.style_transfer(
            content_image_path=content_image_path,
            style_image_path=style_image_path,
            strength=strength,
            settings=settings
        )
        return success_response(result)
    except Exception as e:
        logger.error(f"Style transfer error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generation/background-replacement")
async def background_replacement(
    image_path: str,
    new_background_prompt: str = "",
    remove_background: bool = True,
    settings: Optional[Dict[str, Any]] = None,
    db = Depends(get_db)
):
    """Replace background using AI"""
    try:
        from services.advanced_generation_service import AdvancedGenerationService
        service = AdvancedGenerationService(comfyui_client)
        result = service.background_replacement(
            image_path=image_path,
            new_background_prompt=new_background_prompt,
            remove_background=remove_background,
            settings=settings
        )
        return success_response(result)
    except Exception as e:
        logger.error(f"Background replacement error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generation/object-removal")
async def object_removal(
    image_path: str,
    object_mask_path: Optional[str] = None,
    prompt: str = "",
    settings: Optional[Dict[str, Any]] = None,
    db = Depends(get_db)
):
    """Remove objects from image"""
    try:
        from services.advanced_generation_service import AdvancedGenerationService
        service = AdvancedGenerationService(comfyui_client)
        result = service.object_removal(
            image_path=image_path,
            object_mask_path=object_mask_path,
            prompt=prompt,
            settings=settings
        )
        return success_response(result)
    except Exception as e:
        logger.error(f"Object removal error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generation/object-addition")
async def object_addition(
    image_path: str,
    object_prompt: str,
    position: Optional[List[int]] = None,
    mask_path: Optional[str] = None,
    settings: Optional[Dict[str, Any]] = None,
    db = Depends(get_db)
):
    """Add objects to image"""
    try:
        from services.advanced_generation_service import AdvancedGenerationService
        service = AdvancedGenerationService(comfyui_client)
        result = service.object_addition(
            image_path=image_path,
            object_prompt=object_prompt,
            position=tuple(position) if position else None,
            mask_path=mask_path,
            settings=settings
        )
        return success_response(result)
    except Exception as e:
        logger.error(f"Object addition error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generation/face-swap")
async def face_swap(
    source_image_path: str,
    target_image_path: str,
    face_index: int = 0,
    settings: Optional[Dict[str, Any]] = None,
    db = Depends(get_db)
):
    """Swap faces between images"""
    try:
        from services.advanced_generation_service import AdvancedGenerationService
        service = AdvancedGenerationService(comfyui_client)
        result = service.face_swap(
            source_image_path=source_image_path,
            target_image_path=target_image_path,
            face_index=face_index,
            settings=settings
        )
        return success_response(result)
    except Exception as e:
        logger.error(f"Face swap error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generation/age-transformation")
async def age_transformation(
    image_path: str,
    target_age: str = "younger",
    strength: float = 0.5,
    settings: Optional[Dict[str, Any]] = None,
    db = Depends(get_db)
):
    """Transform age appearance"""
    try:
        from services.advanced_generation_service import AdvancedGenerationService
        service = AdvancedGenerationService(comfyui_client)
        result = service.age_transformation(
            image_path=image_path,
            target_age=target_age,
            strength=strength,
            settings=settings
        )
        return success_response(result)
    except Exception as e:
        logger.error(f"Age transformation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Character Features
@app.post("/api/characters/{character_id}/style-presets")
async def create_style_preset(
    character_id: str,
    preset_name: str,
    style_config: Dict[str, Any],
    db = Depends(get_db)
):
    """Create style preset for character"""
    try:
        from services.enhanced_character_service import EnhancedCharacterService
        service = EnhancedCharacterService(db, CHARACTERS_ROOT)
        result = service.create_style_preset(character_id, preset_name, style_config)
        return success_response(result)
    except Exception as e:
        logger.error(f"Create style preset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/characters/{character_id}/style-presets")
async def get_style_presets(character_id: str, db = Depends(get_db)):
    """Get all style presets for character"""
    try:
        from services.enhanced_character_service import EnhancedCharacterService
        service = EnhancedCharacterService(db, CHARACTERS_ROOT)
        result = service.get_style_presets(character_id)
        return success_response(result)
    except Exception as e:
        logger.error(f"Get style presets error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/characters/{character_id}/style-presets/{preset_name}/apply")
async def apply_style_preset(
    character_id: str,
    preset_name: str,
    db = Depends(get_db)
):
    """Apply style preset to character"""
    try:
        from services.enhanced_character_service import EnhancedCharacterService
        service = EnhancedCharacterService(db, CHARACTERS_ROOT)
        result = service.apply_style_preset(character_id, preset_name)
        return success_response({
            "character_id": result.id,
            "name": result.name,
            "style": result.style
        })
    except Exception as e:
        logger.error(f"Apply style preset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/characters/{character_id}/statistics")
async def get_character_statistics(character_id: str, db = Depends(get_db)):
    """Get character statistics"""
    try:
        from services.enhanced_character_service import EnhancedCharacterService
        service = EnhancedCharacterService(db, CHARACTERS_ROOT)
        result = service.get_character_statistics(character_id)
        return success_response(result)
    except Exception as e:
        logger.error(f"Get character statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/characters/compare")
async def compare_characters(
    character_ids: List[str],
    db = Depends(get_db)
):
    """Compare multiple characters"""
    try:
        from services.enhanced_character_service import EnhancedCharacterService
        service = EnhancedCharacterService(db, CHARACTERS_ROOT)
        result = service.compare_characters(character_ids)
        return success_response(result)
    except Exception as e:
        logger.error(f"Compare characters error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/characters/{character_id}/clone")
async def clone_character(
    character_id: str,
    new_name: str,
    variations: Optional[Dict[str, Any]] = None,
    db = Depends(get_db)
):
    """Clone character with variations"""
    try:
        from services.enhanced_character_service import EnhancedCharacterService
        service = EnhancedCharacterService(db, CHARACTERS_ROOT)
        result = service.clone_character(character_id, new_name, variations)
        return success_response({
            "character_id": result.id,
            "name": result.name
        })
    except Exception as e:
        logger.error(f"Clone character error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/characters/{character_id}/export")
async def export_character(
    character_id: str,
    output_path: Optional[str] = None,
    db = Depends(get_db)
):
    """Export character configuration"""
    try:
        from services.enhanced_character_service import EnhancedCharacterService
        from pathlib import Path
        service = EnhancedCharacterService(db, CHARACTERS_ROOT)
        result = service.export_character(
            character_id,
            Path(output_path) if output_path else None
        )
        return success_response(result)
    except Exception as e:
        logger.error(f"Export character error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/characters/import")
async def import_character(
    import_path: str,
    new_name: Optional[str] = None,
    db = Depends(get_db)
):
    """Import character from export file"""
    try:
        from services.enhanced_character_service import EnhancedCharacterService
        from pathlib import Path
        service = EnhancedCharacterService(db, CHARACTERS_ROOT)
        result = service.import_character(Path(import_path), new_name)
        return success_response({
            "character_id": result.id,
            "name": result.name
        })
    except Exception as e:
        logger.error(f"Import character error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/characters/{character_id}/versions")
async def create_character_version(
    character_id: str,
    version_name: str,
    notes: Optional[str] = None,
    db = Depends(get_db)
):
    """Create character version snapshot"""
    try:
        from services.enhanced_character_service import EnhancedCharacterService
        service = EnhancedCharacterService(db, CHARACTERS_ROOT)
        result = service.create_character_version(character_id, version_name, notes)
        return success_response(result)
    except Exception as e:
        logger.error(f"Create character version error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/characters/{character_id}/versions")
async def get_character_versions(character_id: str, db = Depends(get_db)):
    """Get all character versions"""
    try:
        from services.enhanced_character_service import EnhancedCharacterService
        service = EnhancedCharacterService(db, CHARACTERS_ROOT)
        result = service.get_character_versions(character_id)
        return success_response(result)
    except Exception as e:
        logger.error(f"Get character versions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/characters/{character_id}/versions/{version_name}/restore")
async def restore_character_version(
    character_id: str,
    version_name: str,
    db = Depends(get_db)
):
    """Restore character to version"""
    try:
        from services.enhanced_character_service import EnhancedCharacterService
        service = EnhancedCharacterService(db, CHARACTERS_ROOT)
        result = service.restore_character_version(character_id, version_name)
        return success_response({
            "character_id": result.id,
            "name": result.name,
            "version": version_name
        })
    except Exception as e:
        logger.error(f"Restore character version error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Media Library Enhancements
@app.post("/api/media/{media_id}/auto-tag")
async def auto_tag_media(
    media_id: str,
    tags: Optional[List[str]] = None,
    db = Depends(get_db)
):
    """Auto-generate tags for media"""
    try:
        from services.media_library_service import MediaLibraryService
        from pathlib import Path
        service = MediaLibraryService(db, Path("media"))
        result = service.auto_tag_media(media_id, tags)
        return success_response({
            "media_id": result.id,
            "tags": result.tags
        })
    except Exception as e:
        logger.error(f"Auto-tag media error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/media/{media_id}/recognize-faces")
async def recognize_faces(media_id: str, db = Depends(get_db)):
    """Recognize faces in media"""
    try:
        from services.media_library_service import MediaLibraryService
        from pathlib import Path
        service = MediaLibraryService(db, Path("media"))
        result = service.recognize_faces(media_id)
        return success_response(result)
    except Exception as e:
        logger.error(f"Recognize faces error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/media/duplicates")
async def find_duplicates(
    media_id: Optional[str] = None,
    threshold: float = 0.95,
    db = Depends(get_db)
):
    """Find duplicate media"""
    try:
        from services.media_library_service import MediaLibraryService
        from pathlib import Path
        service = MediaLibraryService(db, Path("media"))
        result = service.find_duplicates(media_id, threshold)
        return success_response(result)
    except Exception as e:
        logger.error(f"Find duplicates error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/media/search-by-image")
async def search_by_image(
    image_path: str,
    limit: int = 10,
    db = Depends(get_db)
):
    """Search for similar images"""
    try:
        from services.media_library_service import MediaLibraryService
        from pathlib import Path
        service = MediaLibraryService(db, Path("media"))
        result = service.search_by_image(image_path, limit)
        return success_response(result)
    except Exception as e:
        logger.error(f"Search by image error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/collections")
async def create_collection(
    name: str,
    description: Optional[str] = None,
    media_ids: Optional[List[str]] = None,
    db = Depends(get_db)
):
    """Create media collection"""
    try:
        from services.media_library_service import MediaLibraryService
        from pathlib import Path
        service = MediaLibraryService(db, Path("media"))
        result = service.create_collection(name, description, media_ids)
        return success_response(result)
    except Exception as e:
        logger.error(f"Create collection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/collections")
async def list_collections(db = Depends(get_db)):
    """List all collections"""
    try:
        from services.media_library_service import MediaLibraryService
        from pathlib import Path
        service = MediaLibraryService(db, Path("media"))
        result = service.list_collections()
        return success_response(result)
    except Exception as e:
        logger.error(f"List collections error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/collections/{collection_id}/media/{media_id}")
async def add_to_collection(
    collection_id: str,
    media_id: str,
    db = Depends(get_db)
):
    """Add media to collection"""
    try:
        from services.media_library_service import MediaLibraryService
        from pathlib import Path
        service = MediaLibraryService(db, Path("media"))
        result = service.add_to_collection(collection_id, media_id)
        return success_response(result)
    except Exception as e:
        logger.error(f"Add to collection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/media/{media_id}/favorite")
async def add_favorite(media_id: str, db = Depends(get_db)):
    """Mark media as favorite"""
    try:
        from services.media_library_service import MediaLibraryService
        from pathlib import Path
        service = MediaLibraryService(db, Path("media"))
        result = service.add_favorite(media_id)
        return success_response({
            "media_id": result.id,
            "favorite": True
        })
    except Exception as e:
        logger.error(f"Add favorite error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/media/{media_id}/favorite")
async def remove_favorite(media_id: str, db = Depends(get_db)):
    """Remove favorite status"""
    try:
        from services.media_library_service import MediaLibraryService
        from pathlib import Path
        service = MediaLibraryService(db, Path("media"))
        result = service.remove_favorite(media_id)
        return success_response({
            "media_id": result.id,
            "favorite": False
        })
    except Exception as e:
        logger.error(f"Remove favorite error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/media/{media_id}/rate")
async def rate_media(
    media_id: str,
    rating: int,
    db = Depends(get_db)
):
    """Rate media (1-5 stars)"""
    try:
        from services.media_library_service import MediaLibraryService
        from pathlib import Path
        service = MediaLibraryService(db, Path("media"))
        result = service.rate_media(media_id, rating)
        return success_response({
            "media_id": result.id,
            "rating": rating
        })
    except Exception as e:
        logger.error(f"Rate media error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/media/{media_id}/comments")
async def add_comment(
    media_id: str,
    comment: str,
    db = Depends(get_db)
):
    """Add comment to media"""
    try:
        from services.media_library_service import MediaLibraryService
        from pathlib import Path
        service = MediaLibraryService(db, Path("media"))
        result = service.add_comment(media_id, comment)
        return success_response({
            "media_id": result.id,
            "comments": result.meta_data.get("comments", [])
        })
    except Exception as e:
        logger.error(f"Add comment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/media/{media_id}/metadata")
async def edit_metadata(
    media_id: str,
    metadata_updates: Dict[str, Any],
    db = Depends(get_db)
):
    """Edit media metadata"""
    try:
        from services.media_library_service import MediaLibraryService
        from pathlib import Path
        service = MediaLibraryService(db, Path("media"))
        result = service.edit_metadata(media_id, metadata_updates)
        return success_response({
            "media_id": result.id,
            "metadata": result.meta_data
        })
    except Exception as e:
        logger.error(f"Edit metadata error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Automation Features
@app.post("/api/automation/smart-batch")
async def smart_batch_generate(
    character_id: Optional[str] = None,
    count: int = 10,
    prompt_template: str = "",
    settings_template: Optional[Dict[str, Any]] = None,
    quality_threshold: float = 0.7,
    auto_filter: bool = True,
    db = Depends(get_db)
):
    """Smart batch generation with quality filtering"""
    try:
        from services.automation_service import AutomationService
        from services.generation_service import GenerationService
        gen_service = GenerationService(db, comfyui_client)
        service = AutomationService(db, gen_service)
        result = service.smart_batch_generate(
            character_id, count, prompt_template, settings_template,
            quality_threshold, auto_filter
        )
        return success_response({
            "batch_job_id": result.id,
            "total_count": result.total_count,
            "status": result.status
        })
    except Exception as e:
        logger.error(f"Smart batch generate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/automation/templates")
async def create_generation_template(
    name: str,
    prompt: str,
    negative_prompt: str = "",
    settings: Optional[Dict[str, Any]] = None,
    character_id: Optional[str] = None,
    db = Depends(get_db)
):
    """Create generation template"""
    try:
        from services.automation_service import AutomationService
        from services.generation_service import GenerationService
        gen_service = GenerationService(db, comfyui_client)
        service = AutomationService(db, gen_service)
        result = service.create_generation_template(
            name, prompt, negative_prompt, settings, character_id
        )
        return success_response(result)
    except Exception as e:
        logger.error(f"Create template error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/automation/templates")
async def list_generation_templates(db = Depends(get_db)):
    """List generation templates"""
    try:
        from services.automation_service import AutomationService
        from services.generation_service import GenerationService
        gen_service = GenerationService(db, comfyui_client)
        service = AutomationService(db, gen_service)
        result = service.list_generation_templates()
        return success_response(result)
    except Exception as e:
        logger.error(f"List templates error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/automation/schedule")
async def schedule_generation(
    prompt: str,
    scheduled_time: str,  # ISO format
    character_id: Optional[str] = None,
    settings: Optional[Dict[str, Any]] = None,
    db = Depends(get_db)
):
    """Schedule generation"""
    try:
        from services.automation_service import AutomationService
        from services.generation_service import GenerationService
        from datetime import datetime
        gen_service = GenerationService(db, comfyui_client)
        service = AutomationService(db, gen_service)
        scheduled_dt = datetime.fromisoformat(scheduled_time)
        result = service.schedule_generation(prompt, scheduled_dt, character_id, settings)
        return success_response({
            "job_id": result.id,
            "scheduled_at": scheduled_time,
            "status": result.status
        })
    except Exception as e:
        logger.error(f"Schedule generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/generation/jobs/{job_id}/priority")
async def set_job_priority(
    job_id: str,
    priority: str,
    db = Depends(get_db)
):
    """Set job priority"""
    try:
        from services.automation_service import AutomationService
        from services.generation_service import GenerationService
        gen_service = GenerationService(db, comfyui_client)
        service = AutomationService(db, gen_service)
        result = service.set_job_priority(job_id, priority)
        return success_response({
            "job_id": result.id,
            "priority": priority
        })
    except Exception as e:
        logger.error(f"Set job priority error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/generation/queue")
async def get_queue_with_priorities(db = Depends(get_db)):
    """Get generation queue with priorities"""
    try:
        from services.automation_service import AutomationService
        from services.generation_service import GenerationService
        gen_service = GenerationService(db, comfyui_client)
        service = AutomationService(db, gen_service)
        result = service.get_queue_with_priorities()
        return success_response(result)
    except Exception as e:
        logger.error(f"Get queue error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/automation/parallel-generate")
async def parallel_generate(
    jobs: List[Dict[str, Any]],
    max_parallel: int = 3,
    db = Depends(get_db)
):
    """Generate multiple jobs in parallel"""
    try:
        from services.automation_service import AutomationService
        from services.generation_service import GenerationService
        gen_service = GenerationService(db, comfyui_client)
        service = AutomationService(db, gen_service)
        result = service.parallel_generate(jobs, max_parallel)
        return success_response([{"job_id": j.id, "status": j.status} for j in result])
    except Exception as e:
        logger.error(f"Parallel generate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# AI-Powered Features
@app.post("/api/ai/generate-prompt")
async def generate_prompt(
    description: str,
    style: Optional[str] = None,
    platform: Optional[str] = None
):
    """Auto-generate optimized prompt"""
    try:
        from services.ai_features_service import AIFeaturesService
        service = AIFeaturesService()
        result = service.generate_prompt(description, style, platform)
        return success_response(result)
    except Exception as e:
        logger.error(f"Generate prompt error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/match-style")
async def match_style(
    reference_image_path: str,
    target_style_description: Optional[str] = None
):
    """Match existing style"""
    try:
        from services.ai_features_service import AIFeaturesService
        service = AIFeaturesService()
        result = service.match_style(reference_image_path, target_style_description)
        return success_response(result)
    except Exception as e:
        logger.error(f"Match style error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/improve-quality")
async def improve_quality(
    image_path: str,
    improvements: Optional[List[str]] = None
):
    """Auto-enhance quality"""
    try:
        from services.ai_features_service import AIFeaturesService
        service = AIFeaturesService()
        result = service.improve_quality(image_path, improvements)
        return success_response(result)
    except Exception as e:
        logger.error(f"Improve quality error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/suggest-content")
async def suggest_content(
    character_id: Optional[str] = None,
    platform: Optional[str] = None,
    count: int = 5
):
    """Suggest content ideas"""
    try:
        from services.ai_features_service import AIFeaturesService
        service = AIFeaturesService()
        result = service.suggest_content(character_id, platform, count)
        return success_response(result)
    except Exception as e:
        logger.error(f"Suggest content error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/generate-caption")
async def generate_caption(
    image_description: str,
    platform: Optional[str] = None,
    tone: Optional[str] = None
):
    """Auto-generate social media captions"""
    try:
        from services.ai_features_service import AIFeaturesService
        service = AIFeaturesService()
        result = service.generate_caption(image_description, platform, tone)
        return success_response(result)
    except Exception as e:
        logger.error(f"Generate caption error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/generate-hashtags")
async def generate_hashtags(
    content_description: str,
    platform: Optional[str] = None,
    count: int = 10
):
    """Auto-generate hashtags"""
    try:
        from services.ai_features_service import AIFeaturesService
        service = AIFeaturesService()
        result = service.generate_hashtags(content_description, platform, count)
        return success_response({"hashtags": result})
    except Exception as e:
        logger.error(f"Generate hashtags error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/trends")
async def analyze_trends(
    platform: Optional[str] = None,
    timeframe: str = "week"
):
    """Analyze content trends"""
    try:
        from services.ai_features_service import AIFeaturesService
        service = AIFeaturesService()
        result = service.analyze_trends(platform, timeframe)
        return success_response(result)
    except Exception as e:
        logger.error(f"Analyze trends error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Phase 1: Advanced Post-Processing Endpoints
# ============================================================================

@app.post("/api/post-process/multi-stage-upscale")
async def multi_stage_upscale(request: Dict[str, Any]):
    """Multi-stage upscaling (2x → 4x → 8x)"""
    try:
        image_path = request.get("image_path")
        target_factor = request.get("target_factor", 8)
        
        post_processing_service = PostProcessingService()
        result_path = post_processing_service.multi_stage_upscale(image_path, target_factor)
        
        return success_response({"output_path": result_path})
    except Exception as e:
        logger.error(f"Multi-stage upscale error: {e}")
        return error_response("PROCESSING_FAILED", str(e))

@app.post("/api/post-process/hybrid-face-restoration")
async def hybrid_face_restoration(request: Dict[str, Any]):
    """Hybrid face restoration (GFPGAN + CodeFormer)"""
    try:
        image_path = request.get("image_path")
        gfpgan_weight = request.get("gfpgan_weight", 0.5)
        
        post_processing_service = PostProcessingService()
        result_path = post_processing_service.hybrid_face_restoration(image_path, gfpgan_weight)
        
        return success_response({"output_path": result_path})
    except Exception as e:
        logger.error(f"Hybrid face restoration error: {e}")
        return error_response("PROCESSING_FAILED", str(e))

@app.post("/api/post-process/color-grading")
async def color_grading(request: Dict[str, Any]):
    """Apply color grading presets"""
    try:
        image_path = request.get("image_path")
        preset = request.get("preset", "instagram")
        
        post_processing_service = PostProcessingService()
        result_path = post_processing_service.color_grading_presets(image_path, preset)
        
        return success_response({"output_path": result_path})
    except Exception as e:
        logger.error(f"Color grading error: {e}")
        return error_response("PROCESSING_FAILED", str(e))

# ============================================================================
# Phase 1: Quality Assurance Endpoints
# ============================================================================

@app.post("/api/qa/automated-scoring")
async def automated_quality_scoring(request: Dict[str, Any]):
    """Automated quality scoring (0-10 scale)"""
    try:
        image_path = request.get("image_path")
        
        qa_service = QualityAssuranceService()
        scores = qa_service.automated_quality_scoring(image_path)
        
        return success_response(scores)
    except Exception as e:
        logger.error(f"Quality scoring error: {e}")
        return error_response("QA_FAILED", str(e))

@app.post("/api/qa/artifact-detection")
async def artifact_detection(request: Dict[str, Any]):
    """Automatic artifact detection"""
    try:
        image_path = request.get("image_path")
        
        qa_service = QualityAssuranceService()
        artifacts = qa_service.artifact_detection(image_path)
        
        return success_response(artifacts)
    except Exception as e:
        logger.error(f"Artifact detection error: {e}")
        return error_response("QA_FAILED", str(e))

@app.post("/api/qa/realism-scoring")
async def realism_scoring(request: Dict[str, Any]):
    """AI detection bypass scoring"""
    try:
        image_path = request.get("image_path")
        
        qa_service = QualityAssuranceService()
        realism = qa_service.realism_scoring(image_path)
        
        return success_response(realism)
    except Exception as e:
        logger.error(f"Realism scoring error: {e}")
        return error_response("QA_FAILED", str(e))

@app.post("/api/qa/batch-filter")
async def batch_quality_filter(request: Dict[str, Any]):
    """Batch quality filtering"""
    try:
        image_paths = request.get("image_paths", [])
        min_score = request.get("min_score", 7.0)
        
        qa_service = QualityAssuranceService()
        results = qa_service.batch_quality_filtering(image_paths, min_score)
        
        return success_response(results)
    except Exception as e:
        logger.error(f"Batch filtering error: {e}")
        return error_response("QA_FAILED", str(e))

@app.post("/api/qa/compare")
async def compare_quality(request: Dict[str, Any]):
    """Compare quality of multiple images side-by-side"""
    try:
        image_paths = request.get("image_paths", [])
        
        qa_service = QualityAssuranceService()
        comparison = qa_service.compare_quality(image_paths)
        
        return success_response(comparison)
    except Exception as e:
        logger.error(f"Quality comparison error: {e}")
        return error_response("QA_FAILED", str(e))

@app.post("/api/qa/improvement-suggestions")
async def quality_improvement_suggestions(request: Dict[str, Any]):
    """Get AI-powered suggestions for improving image quality"""
    try:
        image_path = request.get("image_path")
        
        qa_service = QualityAssuranceService()
        suggestions = qa_service.get_quality_improvement_suggestions(image_path)
        
        return success_response(suggestions)
    except Exception as e:
        logger.error(f"Quality improvement suggestions error: {e}")
        return error_response("QA_FAILED", str(e))

# ============================================================================
# Phase 2: Advanced Generation Endpoints
# ============================================================================

@app.post("/api/generate/inpaint")
async def inpaint_image(request: Dict[str, Any]):
    """Inpaint specific parts of images"""
    try:
        from services.inpainting_service import InpaintingService
        
        image_path = request.get("image_path")
        mask_path = request.get("mask_path")
        prompt = request.get("prompt")
        
        inpainting_service = InpaintingService(comfyui_client)
        result_path = inpainting_service.inpaint(image_path, mask_path, prompt, **request.get("settings", {}))
        
        return success_response({"output_path": result_path})
    except Exception as e:
        logger.error(f"Inpainting error: {e}")
        return error_response("GENERATION_FAILED", str(e))

@app.post("/api/generate/outpaint")
async def outpaint_image(request: Dict[str, Any]):
    """Extend image boundaries"""
    try:
        from services.outpainting_service import OutpaintingService
        
        image_path = request.get("image_path")
        direction = request.get("direction", "all")
        pixels = request.get("pixels", 512)
        prompt = request.get("prompt")
        
        outpainting_service = OutpaintingService(comfyui_client)
        result_path = outpainting_service.outpaint(image_path, direction, pixels, prompt, **request.get("settings", {}))
        
        return success_response({"output_path": result_path})
    except Exception as e:
        logger.error(f"Outpainting error: {e}")
        return error_response("GENERATION_FAILED", str(e))

@app.post("/api/generate/controlnet/pose")
async def generate_with_pose(request: Dict[str, Any]):
    """Generate with pose control"""
    try:
        from services.controlnet_service import ControlNetService
        
        prompt = request.get("prompt")
        pose_image_path = request.get("pose_image_path")
        
        controlnet_service = ControlNetService(comfyui_client)
        result_path = controlnet_service.generate_with_pose(prompt, pose_image_path, **request.get("settings", {}))
        
        return success_response({"output_path": result_path})
    except Exception as e:
        logger.error(f"ControlNet pose error: {e}")
        return error_response("GENERATION_FAILED", str(e))

@app.post("/api/generate/controlnet/depth")
async def generate_with_depth(request: Dict[str, Any]):
    """Generate with depth control"""
    try:
        from services.controlnet_service import ControlNetService
        
        prompt = request.get("prompt")
        depth_image_path = request.get("depth_image_path")
        
        controlnet_service = ControlNetService(comfyui_client)
        result_path = controlnet_service.generate_with_depth(prompt, depth_image_path, **request.get("settings", {}))
        
        return success_response({"output_path": result_path})
    except Exception as e:
        logger.error(f"ControlNet depth error: {e}")
        return error_response("GENERATION_FAILED", str(e))

@app.post("/api/generate/controlnet/edges")
async def generate_with_edges(request: Dict[str, Any]):
    """Generate with edge control"""
    try:
        from services.controlnet_service import ControlNetService
        
        prompt = request.get("prompt")
        edge_image_path = request.get("edge_image_path")
        
        controlnet_service = ControlNetService(comfyui_client)
        result_path = controlnet_service.generate_with_edges(prompt, edge_image_path, **request.get("settings", {}))
        
        return success_response({"output_path": result_path})
    except Exception as e:
        logger.error(f"ControlNet edge error: {e}")
        return error_response("GENERATION_FAILED", str(e))

@app.post("/api/generate/image-to-image")
async def image_to_image(request: Dict[str, Any]):
    """Transform existing images using img2img"""
    try:
        from services.advanced_generation_service import AdvancedGenerationService
        
        image_path = request.get("image_path")
        prompt = request.get("prompt")
        negative_prompt = request.get("negative_prompt", "")
        strength = request.get("strength", 0.75)
        
        service = AdvancedGenerationService(comfyui_client)
        result = service.image_to_image(
            image_path=image_path,
            prompt=prompt,
            negative_prompt=negative_prompt,
            strength=strength,
            settings=request.get("settings", {})
        )
        
        # Queue the workflow
        prompt_id = comfyui_client.queue_prompt(result["workflow"])
        
        return success_response({
            "prompt_id": prompt_id,
            "type": "image_to_image",
            "strength": strength
        })
    except Exception as e:
        logger.error(f"Image-to-image error: {e}")
        return error_response("GENERATION_FAILED", str(e))

@app.post("/api/generate/style-transfer")
async def style_transfer(request: Dict[str, Any]):
    """Apply artistic styles to images"""
    try:
        from services.advanced_generation_service import AdvancedGenerationService
        
        image_path = request.get("image_path")
        style_reference_path = request.get("style_reference_path")
        strength = request.get("strength", 0.5)
        
        service = AdvancedGenerationService(comfyui_client)
        result = service.style_transfer(
            image_path=image_path,
            style_reference_path=style_reference_path,
            strength=strength,
            settings=request.get("settings", {})
        )
        
        prompt_id = comfyui_client.queue_prompt(result["workflow"])
        
        return success_response({
            "prompt_id": prompt_id,
            "type": "style_transfer"
        })
    except Exception as e:
        logger.error(f"Style transfer error: {e}")
        return error_response("GENERATION_FAILED", str(e))

@app.post("/api/generate/background-replacement")
async def background_replacement(request: Dict[str, Any]):
    """Replace background using AI"""
    try:
        from services.advanced_generation_service import AdvancedGenerationService
        
        image_path = request.get("image_path")
        new_background_prompt = request.get("background_prompt", "")
        
        service = AdvancedGenerationService(comfyui_client)
        result = service.background_replacement(
            image_path=image_path,
            new_background_prompt=new_background_prompt,
            settings=request.get("settings", {})
        )
        
        prompt_id = comfyui_client.queue_prompt(result["workflow"])
        
        return success_response({
            "prompt_id": prompt_id,
            "type": "background_replacement"
        })
    except Exception as e:
        logger.error(f"Background replacement error: {e}")
        return error_response("GENERATION_FAILED", str(e))

@app.post("/api/generate/object-removal")
async def object_removal(request: Dict[str, Any]):
    """Remove unwanted objects from images"""
    try:
        from services.advanced_generation_service import AdvancedGenerationService
        
        image_path = request.get("image_path")
        mask_path = request.get("mask_path")
        
        service = AdvancedGenerationService(comfyui_client)
        result = service.object_removal(
            image_path=image_path,
            mask_path=mask_path,
            settings=request.get("settings", {})
        )
        
        prompt_id = comfyui_client.queue_prompt(result["workflow"])
        
        return success_response({
            "prompt_id": prompt_id,
            "type": "object_removal"
        })
    except Exception as e:
        logger.error(f"Object removal error: {e}")
        return error_response("GENERATION_FAILED", str(e))

@app.post("/api/generate/face-swap")
async def face_swap(request: Dict[str, Any]):
    """Swap faces in images/videos"""
    try:
        from services.advanced_generation_service import AdvancedGenerationService
        
        source_image_path = request.get("source_image_path")
        target_image_path = request.get("target_image_path")
        strength = request.get("strength", 0.8)
        
        service = AdvancedGenerationService(comfyui_client)
        result = service.face_swap(
            source_image_path=source_image_path,
            target_image_path=target_image_path,
            strength=strength,
            settings=request.get("settings", {})
        )
        
        prompt_id = comfyui_client.queue_prompt(result["workflow"])
        
        return success_response({
            "prompt_id": prompt_id,
            "type": "face_swap"
        })
    except Exception as e:
        logger.error(f"Face swap error: {e}")
        return error_response("GENERATION_FAILED", str(e))

@app.post("/api/generate/age-transformation")
async def age_transformation(request: Dict[str, Any]):
    """Change age appearance"""
    try:
        from services.advanced_generation_service import AdvancedGenerationService
        
        image_path = request.get("image_path")
        target_age = request.get("target_age", "younger")
        strength = request.get("strength", 0.5)
        
        service = AdvancedGenerationService(comfyui_client)
        result = service.age_transformation(
            image_path=image_path,
            target_age=target_age,
            strength=strength,
            settings=request.get("settings", {})
        )
        
        prompt_id = comfyui_client.queue_prompt(result["workflow"])
        
        return success_response({
            "prompt_id": prompt_id,
            "type": "age_transformation",
            "target_age": target_age
        })
    except Exception as e:
        logger.error(f"Age transformation error: {e}")
        return error_response("GENERATION_FAILED", str(e))

@app.post("/api/generate/gender-transformation")
async def gender_transformation(request: Dict[str, Any]):
    """Change gender appearance"""
    try:
        from services.advanced_generation_service import AdvancedGenerationService
        
        image_path = request.get("image_path")
        target_gender = request.get("target_gender", "opposite")
        strength = request.get("strength", 0.5)
        
        service = AdvancedGenerationService(comfyui_client)
        result = service.gender_transformation(
            image_path=image_path,
            target_gender=target_gender,
            strength=strength,
            settings=request.get("settings", {})
        )
        
        prompt_id = comfyui_client.queue_prompt(result["workflow"])
        
        return success_response({
            "prompt_id": prompt_id,
            "type": "gender_transformation",
            "target_gender": target_gender
        })
    except Exception as e:
        logger.error(f"Gender transformation error: {e}")
        return error_response("GENERATION_FAILED", str(e))

@app.post("/api/generate/body-type-modification")
async def body_type_modification(request: Dict[str, Any]):
    """Modify body type proportions"""
    try:
        from services.advanced_generation_service import AdvancedGenerationService
        
        image_path = request.get("image_path")
        modification = request.get("modification", "slimmer")
        strength = request.get("strength", 0.5)
        
        service = AdvancedGenerationService(comfyui_client)
        result = service.body_type_modification(
            image_path=image_path,
            modification=modification,
            strength=strength,
            settings=request.get("settings", {})
        )
        
        prompt_id = comfyui_client.queue_prompt(result["workflow"])
        
        return success_response({
            "prompt_id": prompt_id,
            "type": "body_type_modification",
            "modification": modification
        })
    except Exception as e:
        logger.error(f"Body type modification error: {e}")
        return error_response("GENERATION_FAILED", str(e))

@app.post("/api/generate/object-addition")
async def object_addition(request: Dict[str, Any]):
    """Add objects to images"""
    try:
        from services.advanced_generation_service import AdvancedGenerationService
        
        image_path = request.get("image_path")
        object_prompt = request.get("object_prompt")
        position = request.get("position")  # [x, y]
        size = request.get("size")  # [width, height]
        
        service = AdvancedGenerationService(comfyui_client)
        result = service.object_addition(
            image_path=image_path,
            object_prompt=object_prompt,
            position=tuple(position) if position else None,
            size=tuple(size) if size else None,
            settings=request.get("settings", {})
        )
        
        prompt_id = comfyui_client.queue_prompt(result["workflow"])
        
        return success_response({
            "prompt_id": prompt_id,
            "type": "object_addition"
        })
    except Exception as e:
        logger.error(f"Object addition error: {e}")
        return error_response("GENERATION_FAILED", str(e))

# ============================================================================
# Phase 1: Video Enhancement Endpoints
# ============================================================================

@app.post("/api/video/enhance")
async def enhance_video(request: Dict[str, Any]):
    """Enhance video with frame interpolation, upscaling, etc."""
    try:
        from services.video_generation_service import VideoGenerationService
        
        video_path = request.get("video_path")
        enhancements = request.get("enhancements", {})
        
        video_service = VideoGenerationService(db, comfyui_client)
        result_path = video_service.enhance_video(video_path, enhancements)
        
        return success_response({"output_path": result_path})
    except Exception as e:
        logger.error(f"Video enhancement error: {e}")
        return error_response("PROCESSING_FAILED", str(e))

@app.post("/api/video/frame-interpolation")
async def frame_interpolation(request: Dict[str, Any]):
    """Interpolate frames to increase video frame rate"""
    try:
        from services.frame_interpolation_service import FrameInterpolationService, FrameInterpolationMethod
        
        input_path = request.get("input_path")
        output_path = request.get("output_path")
        method = request.get("method", "rife")
        scale = request.get("scale", 2)
        fps = request.get("fps")
        
        interpolation_service = FrameInterpolationService()
        method_enum = FrameInterpolationMethod(method)
        success = interpolation_service.interpolate_frames(
            Path(input_path),
            Path(output_path),
            method_enum,
            scale,
            fps
        )
        
        return success_response({"success": success, "output_path": output_path})
    except Exception as e:
        logger.error(f"Frame interpolation error: {e}")
        return error_response("PROCESSING_FAILED", str(e))

# ============================================================================
# Phase 1: Face Consistency Enhancement Endpoints
# ============================================================================

@app.post("/api/face-consistency/ip-adapter-plus")
async def use_ip_adapter_plus(request: Dict[str, Any]):
    """Use IP-Adapter Plus for enhanced face consistency"""
    try:
        from services.face_consistency_service import FaceConsistencyService
        
        workflow = request.get("workflow", {})
        face_reference_path = request.get("face_reference_path")
        strength = request.get("strength", 0.8)
        multiple_references = request.get("multiple_references")
        
        face_service = FaceConsistencyService(db)
        enhanced_workflow = face_service.add_ip_adapter_plus_to_workflow(
            workflow,
            face_reference_path,
            strength,
            multiple_references
        )
        
        return success_response({"workflow": enhanced_workflow})
    except Exception as e:
        logger.error(f"IP-Adapter Plus error: {e}")
        return error_response("PROCESSING_FAILED", str(e))

@app.post("/api/face-consistency/multi-reference")
async def multi_reference_blending(request: Dict[str, Any]):
    """Blend multiple face references for better consistency"""
    try:
        from services.face_consistency_service import FaceConsistencyService
        
        workflow = request.get("workflow", {})
        face_references = request.get("face_references", [])
        weights = request.get("weights")
        method = request.get("method", "instantid")
        
        face_service = FaceConsistencyService(db)
        enhanced_workflow = face_service.multi_reference_blending(
            workflow,
            face_references,
            weights,
            method
        )
        
        return success_response({"workflow": enhanced_workflow})
    except Exception as e:
        logger.error(f"Multi-reference blending error: {e}")
        return error_response("PROCESSING_FAILED", str(e))

# ============================================================================
# Analytics Endpoints
# ============================================================================

@app.get("/api/analytics/generation")
async def get_generation_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    character_id: Optional[str] = None,
    db = Depends(get_db)
):
    """Get generation analytics"""
    try:
        from services.analytics_service import AnalyticsService
        from datetime import datetime
        service = AnalyticsService(db)
        
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        result = service.get_generation_analytics(start_dt, end_dt, character_id)
        return success_response(result)
    except Exception as e:
        logger.error(f"Get generation analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/quality-trends")
async def get_quality_trends(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    character_id: Optional[str] = None,
    db = Depends(get_db)
):
    """Get quality trends"""
    try:
        from services.analytics_service import AnalyticsService
        from datetime import datetime
        service = AnalyticsService(db)
        
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        result = service.get_quality_trends(start_dt, end_dt, character_id)
        return success_response(result)
    except Exception as e:
        logger.error(f"Get quality trends error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/performance")
async def get_performance_metrics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db = Depends(get_db)
):
    """Get performance metrics"""
    try:
        from services.analytics_service import AnalyticsService
        from datetime import datetime
        service = AnalyticsService(db)
        
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        result = service.get_performance_metrics(start_dt, end_dt)
        return success_response(result)
    except Exception as e:
        logger.error(f"Get performance metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/content-performance")
async def get_content_performance(
    platform: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db = Depends(get_db)
):
    """Get content performance metrics"""
    try:
        from services.analytics_service import AnalyticsService
        from datetime import datetime
        service = AnalyticsService(db)
        
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        result = service.get_content_performance(platform, start_dt, end_dt)
        return success_response(result)
    except Exception as e:
        logger.error(f"Get content performance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/user")
async def get_user_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db = Depends(get_db)
):
    """Get user analytics"""
    try:
        from services.analytics_service import AnalyticsService
        from datetime import datetime
        service = AnalyticsService(db)
        
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        result = service.get_user_analytics(start_dt, end_dt)
        return success_response(result)
    except Exception as e:
        logger.error(f"Get user analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analytics/export")
async def export_analytics_report(
    report_type: str,
    format: str = "json",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db = Depends(get_db)
):
    """Export analytics report"""
    try:
        from services.analytics_service import AnalyticsService
        from datetime import datetime
        service = AnalyticsService(db)
        
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        result = service.export_report(report_type, format, start_dt, end_dt)
        return success_response(result)
    except Exception as e:
        logger.error(f"Export report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Phase 5: Performance & Optimization Endpoints
# ============================================================================

@app.get("/api/performance/metrics")
async def get_performance_metrics():
    """Get system performance metrics"""
    try:
        from services.performance_service import PerformanceService
        service = PerformanceService()
        result = service.get_performance_metrics()
        return success_response(result)
    except Exception as e:
        logger.error(f"Get performance metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/performance/bottlenecks")
async def detect_bottlenecks():
    """Detect performance bottlenecks"""
    try:
        from services.performance_service import PerformanceService
        service = PerformanceService()
        result = service.detect_bottlenecks()
        return success_response(result)
    except Exception as e:
        logger.error(f"Detect bottlenecks error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/performance/memory")
async def get_memory_usage():
    """Get current memory usage"""
    try:
        from services.performance_service import PerformanceService
        service = PerformanceService()
        result = service.get_memory_usage()
        return success_response(result)
    except Exception as e:
        logger.error(f"Get memory usage error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/performance/optimize-batch")
async def optimize_batch_generation(
    batch_size: int,
    parallel_count: int
):
    """Optimize batch generation parameters"""
    try:
        from services.performance_service import PerformanceService
        service = PerformanceService()
        result = service.optimize_batch_generation(batch_size, parallel_count)
        return success_response(result)
    except Exception as e:
        logger.error(f"Optimize batch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/performance/clear-cache")
async def clear_cache(cache_type: Optional[str] = None):
    """Clear cache to free memory"""
    try:
        from services.performance_service import PerformanceService
        service = PerformanceService()
        result = service.clear_cache(cache_type)
        return success_response(result)
    except Exception as e:
        logger.error(f"Clear cache error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/performance/optimize-queue")
async def optimize_queue(queue_items: List[Dict[str, Any]]):
    """Optimize generation queue order"""
    try:
        from services.performance_service import PerformanceService
        service = PerformanceService()
        result = service.optimize_queue(queue_items)
        return success_response(result)
    except Exception as e:
        logger.error(f"Optimize queue error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Phase 2: Platform Integration Endpoints
# ============================================================================

@app.post("/api/platforms/{platform}/post")
async def post_to_platform(
    platform: str,
    media_path: str,
    caption: Optional[str] = None,
    hashtags: Optional[List[str]] = None,
    schedule_time: Optional[str] = None,
    account_id: Optional[str] = None
):
    """Post media to platform"""
    try:
        from services.platform_integration_service import PlatformIntegrationService
        from datetime import datetime
        
        service = PlatformIntegrationService()
        scheduled_dt = datetime.fromisoformat(schedule_time) if schedule_time else None
        
        result = service.post_to_platform(
            platform=platform,
            media_path=media_path,
            caption=caption,
            hashtags=hashtags,
            schedule_time=scheduled_dt,
            account_id=account_id
        )
        return success_response(result)
    except Exception as e:
        logger.error(f"Platform post error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/platforms/{platform}/status")
async def get_platform_status(
    platform: str,
    account_id: Optional[str] = None
):
    """Get platform connection status"""
    try:
        from services.platform_integration_service import PlatformIntegrationService
        
        service = PlatformIntegrationService()
        result = service.get_platform_status(platform, account_id)
        return success_response(result)
    except Exception as e:
        logger.error(f"Get platform status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/platforms/{platform}/schedule")
async def schedule_platform_post(
    platform: str,
    media_path: str,
    schedule_time: str,
    caption: Optional[str] = None,
    hashtags: Optional[List[str]] = None,
    account_id: Optional[str] = None
):
    """Schedule a post for later"""
    try:
        from services.platform_integration_service import PlatformIntegrationService
        from datetime import datetime
        
        service = PlatformIntegrationService()
        scheduled_dt = datetime.fromisoformat(schedule_time)
        
        result = service.schedule_post(
            platform=platform,
            media_path=media_path,
            schedule_time=scheduled_dt,
            caption=caption,
            hashtags=hashtags,
            account_id=account_id
        )
        return success_response(result)
    except Exception as e:
        logger.error(f"Schedule post error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/platforms/{platform}/analytics")
async def get_platform_analytics(
    platform: str,
    post_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get platform analytics"""
    try:
        from services.platform_integration_service import PlatformIntegrationService
        from datetime import datetime
        
        service = PlatformIntegrationService()
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        result = service.get_analytics(platform, post_id, start_dt, end_dt)
        return success_response(result)
    except Exception as e:
        logger.error(f"Get platform analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
