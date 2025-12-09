"""
Content Generation Pipeline
Complete automation pipeline for content generation with face consistency and post-processing
"""
import logging
from typing import Dict, Optional, Any, List
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

from models import Character, GenerationJob, MediaItem
from services.generation_service import GenerationService
from services.face_consistency_service import FaceConsistencyService
from services.post_processing_service import PostProcessingService
from services.quality_service import QualityService

logger = logging.getLogger(__name__)

class ContentGenerationPipeline:
    """Complete content generation pipeline with automation"""
    
    def __init__(
        self,
        db: Session,
        generation_service: GenerationService,
        character_config: Optional[Dict[str, Any]] = None
    ):
        self.db = db
        self.generation_service = generation_service
        self.face_consistency_service = FaceConsistencyService(db)
        self.post_processing_service = PostProcessingService()
        self.quality_service = QualityService()
        
        # Get character if character_id provided
        self.character = None
        if character_config and character_config.get("character_id"):
            self.character = db.query(Character).filter(
                Character.id == character_config["character_id"]
            ).first()
    
    def generate_content(
        self,
        count: int = 10,
        content_type: str = "image",
        settings: Optional[Dict[str, Any]] = None,
        auto_quality_check: bool = True,
        min_quality_score: float = 8.0,
        auto_retry: bool = True,
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate content with full automation pipeline
        
        Args:
            count: Number of content items to generate
            content_type: 'image' or 'video'
            settings: Generation settings
            auto_quality_check: Automatically check quality
            min_quality_score: Minimum quality score to accept
            auto_retry: Automatically retry failed generations
            max_retries: Maximum retry attempts
        
        Returns:
            List of generated content results
        """
        results = []
        settings = settings or {}
        
        for i in range(count):
            logger.info(f"Generating {content_type} {i+1}/{count}...")
            
            retry_count = 0
            success = False
            
            while retry_count <= max_retries and not success:
                try:
                    # Build prompt
                    prompt = self.build_prompt(settings.get("variation", f"variation_{i+1}"))
                    
                    # Generate content
                    if content_type == "image":
                        job = self.generate_image(prompt, settings)
                    elif content_type == "video":
                        job = self.generate_video(prompt, settings)
                    else:
                        raise ValueError(f"Unsupported content type: {content_type}")
                    
                    # Wait for completion
                    if not self.wait_for_completion(job.id, timeout=600):
                        raise TimeoutError(f"Generation timeout for job {job.id}")
                    
                    # Get result
                    self.db.refresh(job)
                    if not job.result_media:
                        raise ValueError("No media generated")
                    
                    media_path = Path(job.result_media.file_path)
                    
                    # Apply face consistency if enabled
                    face_consistency_config = settings.get("face_consistency", {})
                    if face_consistency_config.get("enabled", False) and self.character:
                        media_path = self.apply_face_consistency(media_path, face_consistency_config)
                    
                    # Post-process
                    post_processing_config = settings.get("post_processing", {})
                    if post_processing_config.get("enabled", True):
                        media_path = self.post_process(media_path, post_processing_config, content_type)
                    
                    # Quality check
                    if auto_quality_check:
                        quality_result = self.quality_service.score_content(media_path, content_type)
                        quality_score = quality_result.get("overall", 0.0)
                        
                        if quality_score < min_quality_score:
                            logger.warning(
                                f"Quality score {quality_score} below threshold {min_quality_score}"
                            )
                            if auto_retry and retry_count < max_retries:
                                retry_count += 1
                                logger.info(f"Retrying generation (attempt {retry_count}/{max_retries})...")
                                continue
                            else:
                                self.handle_failure(job, f"Quality score {quality_score} below threshold")
                                break
                        
                        # Store quality scores
                        job.meta_data = job.meta_data or {}
                        job.meta_data["quality_scores"] = quality_result
                        self.db.commit()
                    
                    # Success
                    results.append({
                        "job_id": job.id,
                        "media_id": job.result_media.id,
                        "media_path": str(media_path),
                        "quality_score": quality_result.get("overall", 0.0) if auto_quality_check else None,
                        "status": "completed"
                    })
                    success = True
                    logger.info(f"Successfully generated {content_type} {i+1}/{count}")
                    
                except Exception as e:
                    logger.error(f"Error generating content {i+1}/{count}: {e}")
                    if auto_retry and retry_count < max_retries:
                        retry_count += 1
                        logger.info(f"Retrying generation (attempt {retry_count}/{max_retries})...")
                    else:
                        self.handle_failure(job if 'job' in locals() else None, str(e))
                        results.append({
                            "status": "failed",
                            "error": str(e),
                            "retry_count": retry_count
                        })
                        break
        
        return results
    
    def generate_image(self, prompt: str, settings: Dict[str, Any]) -> GenerationJob:
        """Generate an image"""
        return self.generation_service.generate_image(
            prompt=prompt,
            negative_prompt=settings.get("negative_prompt"),
            character_id=self.character.id if self.character else None,
            settings=settings.get("generation_settings", {}),
            face_consistency=settings.get("face_consistency", {}),
            post_processing=settings.get("post_processing", {}),
            platform=settings.get("platform"),
            optimize_prompt=settings.get("optimize_prompt", True)
        )
    
    def generate_video(self, prompt: str, settings: Dict[str, Any]) -> GenerationJob:
        """Generate a video"""
        return self.generation_service.generate_video(
            prompt=prompt,
            negative_prompt=settings.get("negative_prompt"),
            character_id=self.character.id if self.character else None,
            image_id=settings.get("image_id"),
            settings=settings.get("generation_settings", {}),
            face_consistency=settings.get("face_consistency", {}),
            post_processing=settings.get("post_processing", {}),
            method=settings.get("method")
        )
    
    def build_prompt(self, variation: str = "default") -> str:
        """Build prompt from character config or template"""
        if self.character and self.character.settings:
            base = self.character.settings.get("base_prompt", "")
            variation_text = self.get_variation(variation)
            return f"{base}, {variation_text}" if base else variation_text
        else:
            # Default prompt template
            return f"ultra realistic photo, professional photography, {variation}"
    
    def get_variation(self, variation: str) -> str:
        """Get variation text"""
        variations = {
            "default": "natural pose, soft lighting",
            "variation_1": "elegant pose, warm lighting",
            "variation_2": "casual pose, natural lighting",
            "variation_3": "professional pose, studio lighting",
        }
        return variations.get(variation, variation)
    
    def apply_face_consistency(
        self,
        media_path: Path,
        config: Dict[str, Any]
    ) -> Path:
        """Apply face consistency to media"""
        # Face consistency is applied during generation
        # This is a placeholder for post-generation face consistency
        return media_path
    
    def post_process(
        self,
        media_path: Path,
        config: Dict[str, Any],
        content_type: str
    ) -> Path:
        """Post-process media"""
        if content_type == "image":
            output_path = media_path.parent / f"processed_{media_path.name}"
            success = self.post_processing_service.process_image(
                media_path,
                output_path,
                config
            )
            if success:
                return output_path
        
        return media_path
    
    def wait_for_completion(self, job_id: str, timeout: int = 600) -> bool:
        """Wait for job completion"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            job = self.generation_service.get_job_status(job_id)
            if not job:
                return False
            
            if job.status == "completed":
                return True
            elif job.status == "failed":
                return False
            
            time.sleep(2)
        
        return False
    
    def handle_failure(self, job: Optional[GenerationJob], error: str):
        """Handle generation failure"""
        if job:
            self.generation_service.fail_job(job.id, error)
        logger.error(f"Generation failed: {error}")
