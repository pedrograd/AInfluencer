"""
Generation Service
Handles image and video generation
"""
import logging
from typing import Dict, Optional, Any, List
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

from models import GenerationJob, MediaItem, Character
from services.comfyui_client import ComfyUIClient
from services.workflow_manager import WorkflowManager
from services.face_consistency_service import FaceConsistencyService
from services.post_processing_service import PostProcessingService
from services.video_generation_service import VideoGenerationService, VideoGenerationMethod
from services.frame_interpolation_service import FrameInterpolationService
from services.audio_sync_service import AudioSyncService
from services.anti_detection_service import AntiDetectionService
from services.quality_service import QualityService
from services.quality_scorer_service import QualityScorer
from services.detection_tester_service import DetectionTester
from models import QualityScore, DetectionTest
from services.prompt_engineering_service import PromptEngineeringService, Platform
from services.troubleshooting_service import ErrorCode
from services.best_practices_service import BestPracticesService

logger = logging.getLogger(__name__)

class GenerationService:
    """Service for managing image and video generation"""
    
    def __init__(self, db: Session, comfyui_client: ComfyUIClient):
        self.db = db
        self.comfyui = comfyui_client
        self.workflow_manager = WorkflowManager()
        self.face_consistency_service = FaceConsistencyService(db)
        self.post_processing_service = PostProcessingService()
        self.video_generation_service = VideoGenerationService(
            db,
            comfyui_client,
            self.workflow_manager,
            self.face_consistency_service
        )
        self.frame_interpolation_service = FrameInterpolationService()
        self.audio_sync_service = AudioSyncService()
        self.anti_detection_service = AntiDetectionService()
        self.quality_service = QualityService()
        self.quality_scorer = QualityScorer()
        self.detection_tester = DetectionTester()
        self.prompt_engineering = PromptEngineeringService()
        self.best_practices = BestPracticesService()
    
    def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        character_id: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
        face_consistency: Optional[Dict[str, Any]] = None,
        post_processing: Optional[Dict[str, Any]] = None,
        platform: Optional[str] = None,
        optimize_prompt: bool = True
    ) -> GenerationJob:
        """Generate an image"""
        
        # Get character if specified
        character = None
        character_config = None
        if character_id:
            character = self.db.query(Character).filter(Character.id == character_id).first()
            if character:
                character_config = character.settings or {}
        
        # Use advanced prompt engineering if character config exists
        final_prompt = prompt
        final_negative = negative_prompt or ""
        
        if character_config and character_config.get("base_prompt"):
            # Build prompt from character config
            platform_enum = None
            if platform:
                try:
                    platform_enum = Platform(platform.lower())
                except ValueError:
                    pass
            
            variation = settings.get("variation", "default") if settings else "default"
            final_prompt, final_negative = self.prompt_engineering.build_prompt_from_character_config(
                character_config,
                variation=variation,
                platform=platform_enum
            )
        elif optimize_prompt:
            # Optimize the provided prompt
            final_prompt = self.prompt_engineering.optimize_prompt(prompt)
            if not negative_prompt:
                platform_enum = None
                if platform:
                    try:
                        platform_enum = Platform(platform.lower())
                    except ValueError:
                        pass
                final_negative = self.prompt_engineering.get_negative_prompt(platform=platform_enum)
        
        # Validate best practices
        try:
            validation_request = {
                "prompt": final_prompt,
                "negative_prompt": final_negative,
                "face_consistency": face_consistency or {},
                "post_processing": post_processing or {},
                "quality_check": {"enabled": True}
            }
            bp_report = self.best_practices.validate_generation_request(validation_request)
            
            # Log violations if any
            if bp_report.violations:
                critical_violations = [v for v in bp_report.violations if v.severity.value == "critical"]
                if critical_violations:
                    logger.warning(f"Critical best practices violations detected: {len(critical_violations)}")
                    for violation in critical_violations[:3]:  # Log first 3
                        logger.warning(f"  - {violation.practice}: {violation.description}")
            
            # Store best practices report in metadata
            validation_metadata = {
                "best_practices_score": bp_report.overall_score,
                "best_practices_violations_count": len(bp_report.violations),
                "best_practices_critical_count": len([v for v in bp_report.violations if v.severity.value == "critical"])
            }
        except Exception as e:
            logger.warning(f"Best practices validation failed: {e}")
            validation_metadata = {}
        
        # Create generation job
        job = GenerationJob(
            type="image",
            status="pending",
            prompt=final_prompt,
            negative_prompt=final_negative,
            character_id=character_id,
            settings=settings or {},
            metadata={
                "face_consistency": face_consistency or {},
                "post_processing": post_processing or {},
                "original_prompt": prompt,
                "optimized": optimize_prompt,
                **validation_metadata
            }
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        # Build workflow
        workflow = self.workflow_manager.build_image_workflow(
            prompt=final_prompt,
            negative_prompt=final_negative,
            settings=settings or {},
            character=character,
            face_consistency=face_consistency or {}
        )
        
        # Apply face consistency if enabled
        if face_consistency and face_consistency.get("enabled"):
            workflow = self.face_consistency_service.apply_face_consistency(
                workflow,
                character_id=character_id,
                face_consistency_config=face_consistency
            )
        
        # Queue prompt
        try:
            prompt_id = self.comfyui.queue_prompt(workflow)
            job.comfyui_prompt_id = prompt_id
            job.status = "processing"
            job.started_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Image generation queued: job_id={job.id}, prompt_id={prompt_id}")
            
            # Start background monitoring (will be handled by job monitor service)
            # The monitor will check ComfyUI and save results when complete
            
        except Exception as e:
            job.status = "failed"
            job.failed_at = datetime.utcnow()
            
            # Determine error code
            error_code = ErrorCode.GENERATION_FAILED.value
            error_message = str(e)
            
            # Check for specific error types
            if "CUDA out of memory" in str(e) or "out of memory" in str(e).lower():
                error_code = ErrorCode.CUDA_OUT_OF_MEMORY.value
            elif "CUDA" in str(e) and "not found" in str(e).lower():
                error_code = ErrorCode.CUDA_DEVICE_NOT_FOUND.value
            elif "model" in str(e).lower() and "not found" in str(e).lower():
                error_code = ErrorCode.MODEL_FILE_NOT_FOUND.value
            elif "connection" in str(e).lower() or "refused" in str(e).lower():
                error_code = ErrorCode.COMFYUI_NOT_RUNNING.value
            
            job.error_message = error_message
            job.meta_data = job.meta_data or {}
            job.meta_data["error_code"] = error_code
            self.db.commit()
            logger.error(f"Failed to queue image generation: {error_code} - {error_message}")
        
        return job
    
    def generate_video(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        character_id: Optional[str] = None,
        image_id: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
        face_consistency: Optional[Dict[str, Any]] = None,
        post_processing: Optional[Dict[str, Any]] = None,
        method: Optional[str] = None
    ) -> GenerationJob:
        """
        Generate a video using specified method
        
        Supports: animatediff, svd, modelscope, veo, luma, kling
        """
        settings = settings or {}
        
        # Determine method
        if not method:
            # Auto-select based on settings
            has_image = image_id is not None
            quality_priority = settings.get("quality_priority", "balanced")
            method = self.video_generation_service.get_recommended_method(
                use_case=settings.get("use_case", "general"),
                has_image=has_image,
                quality_priority=quality_priority
            )
        else:
            try:
                method = VideoGenerationMethod(method.lower())
            except ValueError:
                logger.warning(f"Invalid method {method}, using animatediff")
                method = VideoGenerationMethod.ANIMATEDIFF
        
        # Create generation job
        job = GenerationJob(
            type="video",
            status="pending",
            prompt=prompt,
            negative_prompt=negative_prompt or "",
            character_id=character_id,
            settings={
                **settings,
                "method": method.value
            },
            metadata={
                "image_id": image_id,
                "face_consistency": face_consistency or {},
                "post_processing": post_processing or {}
            }
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        # Get source image path if specified
        image_path = None
        if image_id:
            source_image = self.db.query(MediaItem).filter(MediaItem.id == image_id).first()
            if source_image:
                image_path = Path(source_image.file_path)
        
        # Apply face consistency to settings if enabled
        if face_consistency and face_consistency.get("enabled"):
            # Face consistency will be applied in workflow building
            pass
        
        # Build workflow using video generation service
        try:
            # Convert method string to enum
            try:
                method_enum = VideoGenerationMethod(method.lower()) if method else VideoGenerationMethod.ANIMATEDIFF
            except ValueError:
                logger.warning(f"Invalid method {method}, using animatediff")
                method_enum = VideoGenerationMethod.ANIMATEDIFF
            
            # Generate video workflow
            result = self.video_generation_service.generate_video(
                method=method_enum,
                prompt=prompt,
                negative_prompt=negative_prompt,
                image_path=image_path,
                settings=settings,
                character_id=character_id,
                face_consistency=face_consistency,
                job=job
            )
            
            job.comfyui_prompt_id = result.get("prompt_id")
            job.status = "processing"
            job.started_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Video generation queued: job_id={job.id}, method={method_enum.value}, prompt_id={result.get('prompt_id')}")
            
        except Exception as e:
            job.status = "failed"
            job.failed_at = datetime.utcnow()
            
            # Determine error code
            error_code = ErrorCode.GENERATION_FAILED.value
            error_message = str(e)
            
            # Check for specific error types
            if "CUDA out of memory" in str(e) or "out of memory" in str(e).lower():
                error_code = ErrorCode.CUDA_OUT_OF_MEMORY.value
            elif "CUDA" in str(e) and "not found" in str(e).lower():
                error_code = ErrorCode.CUDA_DEVICE_NOT_FOUND.value
            elif "model" in str(e).lower() and "not found" in str(e).lower():
                error_code = ErrorCode.MODEL_FILE_NOT_FOUND.value
            elif "connection" in str(e).lower() or "refused" in str(e).lower():
                error_code = ErrorCode.COMFYUI_NOT_RUNNING.value
            
            job.error_message = error_message
            job.meta_data = job.meta_data or {}
            job.meta_data["error_code"] = error_code
            self.db.commit()
            logger.error(f"Failed to queue video generation: {error_code} - {error_message}", exc_info=True)
        
        return job
    
    def get_job_status(self, job_id: str) -> Optional[GenerationJob]:
        """Get generation job status"""
        return self.db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    
    def update_job_progress(self, job_id: str, progress: float, message: Optional[str] = None):
        """Update job progress"""
        job = self.db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if job:
            job.progress = progress
            if message:
                job.meta_data = job.meta_data or {}
                job.meta_data["status_message"] = message
            self.db.commit()
    
    def complete_job(
        self,
        job_id: str,
        media_id: Optional[str] = None,
        output_path: Optional[Path] = None
    ):
        """Mark job as completed and apply post-processing if needed"""
        job = self.db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if job:
            # Get post-processing config from job metadata
            post_processing_config = job.meta_data.get("post_processing", {}) if job.meta_data else {}
            
            # Apply post-processing if enabled and output path provided
            if output_path and post_processing_config.get("enabled", True):
                try:
                    processed_path = self._apply_post_processing(
                        output_path,
                        post_processing_config,
                        job.type
                    )
                    
                    # Apply anti-detection if enabled
                    anti_detection_config = job.meta_data.get("anti_detection", {}) if job.meta_data else {}
                    if anti_detection_config.get("enabled", True):
                        self._apply_anti_detection(processed_path, anti_detection_config)
                    
                    # Quality check if enabled (using comprehensive QA system)
                    quality_config = job.meta_data.get("quality_check", {}) if job.meta_data else {}
                    if quality_config.get("enabled", True):
                        # Score quality using comprehensive QA system
                        quality_scores = self.quality_scorer.score(
                            processed_path,
                            job.type
                        )
                        
                        # Test AI detection
                        detection_results = self.detection_tester.test(processed_path)
                        
                        # Store quality scores in metadata
                        job.meta_data = job.meta_data or {}
                        job.meta_data["quality_scores"] = quality_scores
                        job.meta_data["detection_results"] = detection_results
                        
                        # Save quality score to database if media_id exists
                        if media_id:
                            try:
                                quality_score_record = QualityScore(
                                    media_id=media_id,
                                    overall_score=quality_scores.get('overall', 0.0) / 10.0,  # Convert to 0-1
                                    face_quality_score=quality_scores.get('face', 0.0) / 10.0,
                                    technical_score=quality_scores.get('technical', 0.0) / 10.0,
                                    realism_score=quality_scores.get('realism', 0.0) / 10.0,
                                    passed=quality_scores.get('passed', False),
                                    auto_approved=quality_scores.get('auto_approved', False),
                                    metadata=quality_scores
                                )
                                self.db.add(quality_score_record)
                                
                                # Save detection test
                                detection_test_record = DetectionTest(
                                    media_id=media_id,
                                    test_type="automated",
                                    threshold=detection_results.get('threshold', 0.3),
                                    average_score=detection_results.get('average', 0.0),
                                    passed=detection_results.get('passed', False),
                                    results=detection_results.get('scores', {})
                                )
                                self.db.add(detection_test_record)
                                self.db.commit()
                            except Exception as e:
                                logger.error(f"Failed to save QA results to database: {e}")
                        
                        # Auto-reject if below threshold
                        min_score = quality_config.get("min_score", 8.0)
                        min_detection_score = quality_config.get("min_detection_score", 0.3)
                        
                        quality_failed = quality_scores.get("overall", 0.0) < min_score
                        detection_failed = not detection_results.get("passed", False) or detection_results.get("average", 1.0) > min_detection_score
                        
                        if quality_failed or detection_failed:
                            logger.warning(
                                f"Job {job_id} failed QA check: "
                                f"quality={quality_scores.get('overall', 0.0):.1f} (min={min_score}), "
                                f"detection={detection_results.get('average', 0.0):.2f} (max={min_detection_score})"
                            )
                            job.status = "failed"
                            job.error_message = f"Failed QA: quality={quality_scores.get('overall', 0.0):.1f}, detection={detection_results.get('average', 0.0):.2f}"
                            job.error_message = f"Quality score {quality_scores.get('overall')} below threshold {min_score}"
                            job.meta_data = job.meta_data or {}
                            job.meta_data["error_code"] = ErrorCode.GENERATION_QUALITY_LOW.value
                            self.db.commit()
                            return
                    
                except Exception as e:
                    logger.error(f"Post-processing error for job {job_id}: {e}")
                    # Continue anyway - don't fail the job due to post-processing errors
            
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.progress = 1.0
            if media_id:
                # Set result_media relationship by setting generation_job_id on media
                media = self.db.query(MediaItem).filter(MediaItem.id == media_id).first()
                if media:
                    media.generation_job_id = job.id
            self.db.commit()
    
    def _apply_post_processing(
        self,
        input_path: Path,
        config: Dict[str, Any],
        content_type: str
    ) -> Path:
        """Apply post-processing to generated content"""
        output_path = input_path.parent / f"processed_{input_path.name}"
        
        if content_type == "image":
            success = self.post_processing_service.process_image(
                input_path,
                output_path,
                config
            )
            if success:
                return output_path
        
        # Return original if processing failed
        return input_path
    
    def _apply_anti_detection(
        self,
        image_path: Path,
        config: Dict[str, Any]
    ):
        """Apply anti-detection techniques"""
        try:
            self.anti_detection_service.process_image(image_path, config)
        except Exception as e:
            logger.warning(f"Anti-detection error: {e}")
    
    def fail_job(self, job_id: str, error_message: str):
        """Mark job as failed"""
        job = self.db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.failed_at = datetime.utcnow()
            job.error_message = error_message
            self.db.commit()
