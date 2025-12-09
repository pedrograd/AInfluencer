"""
Complete Automation
Orchestrates the entire automation workflow from generation to posting
"""
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.orm import Session

from models import Character
from services.generation_service import GenerationService
from services.automation.content_generation_pipeline import ContentGenerationPipeline
from services.automation.batch_processor import BatchProcessor
from services.automation.quality_controller import QualityController
from services.automation.approval_workflow import ApprovalWorkflow
from services.automation.content_scheduler import ContentScheduler
from services.automation.auto_poster import AutoPoster
from services.automation.monitoring_system import MonitoringSystem

logger = logging.getLogger(__name__)

class CompleteAutomation:
    """Complete automation orchestrator"""
    
    def __init__(
        self,
        db: Session,
        generation_service: GenerationService,
        config: Optional[Dict[str, Any]] = None
    ):
        self.db = db
        self.generation_service = generation_service
        self.config = config or {}
        
        # Initialize services
        self.pipeline = ContentGenerationPipeline(
            db,
            generation_service,
            config.get("character")
        )
        self.processor = BatchProcessor()
        self.quality_controller = QualityController()
        self.approval_workflow = ApprovalWorkflow(
            db,
            auto_approve_threshold=self.config.get("auto_approve_threshold", 9.0)
        )
        self.scheduler = ContentScheduler(db)
        self.poster = AutoPoster(db, self.scheduler)
        self.monitoring = MonitoringSystem(db)
    
    def run_daily(self) -> Dict[str, Any]:
        """
        Run daily automation workflow
        
        Returns:
            Automation results
        """
        logger.info("Starting daily automation...")
        
        results = {
            "generated": [],
            "processed": [],
            "approved": [],
            "scheduled": [],
            "posted": [],
            "errors": []
        }
        
        try:
            # 1. Generate content
            daily_count = self.config.get("daily_content_count", 10)
            character_id = self.config.get("character_id")
            
            generation_results = self.pipeline.generate_content(
                count=daily_count,
                content_type=self.config.get("content_type", "image"),
                settings=self.config.get("generation_settings", {}),
                auto_quality_check=True,
                min_quality_score=self.config.get("min_quality_score", 8.0),
                auto_retry=True,
                max_retries=self.config.get("max_retries", 3)
            )
            
            results["generated"] = generation_results
            
            # 2. Process generated content (if needed)
            if self.config.get("batch_process", False):
                processed = self._batch_process_generated(generation_results)
                results["processed"] = processed
            
            # 3. Quality check and approval
            approved_content = []
            for item in generation_results:
                if item.get("status") == "completed":
                    media_path = Path(item.get("media_path"))
                    if media_path.exists():
                        approval_result = self.approval_workflow.approve_content(
                            media_path,
                            self.config.get("content_type", "image")
                        )
                        if approval_result["approved"]:
                            approved_content.append({
                                **item,
                                "approval": approval_result
                            })
            
            results["approved"] = approved_content
            
            # 4. Schedule content
            platform = self.config.get("platform", "instagram")
            schedule_times = self._calculate_post_times(len(approved_content))
            
            for i, content in enumerate(approved_content):
                if i < len(schedule_times):
                    scheduled = self.scheduler.schedule_content(
                        content["media_id"],
                        platform,
                        schedule_times[i]
                    )
                    results["scheduled"].append({
                        "media_id": content["media_id"],
                        "platform": platform,
                        "scheduled_time": schedule_times[i].isoformat()
                    })
            
            # 5. Post scheduled items
            post_results = self.poster.process_scheduled_posts()
            results["posted"] = post_results
            
            # 6. Track metrics
            for item in generation_results:
                if item.get("status") == "completed":
                    quality_score = item.get("quality_score", 0.0)
                    self.monitoring.track_generation(
                        success=True,
                        quality_score=quality_score
                    )
                else:
                    self.monitoring.track_generation(success=False)
            
            for post in post_results.get("posted", []):
                self.monitoring.track_posting(success=True)
            
            logger.info(
                f"Daily automation complete. "
                f"Generated: {len(generation_results)}, "
                f"Approved: {len(approved_content)}, "
                f"Posted: {post_results.get('posted', 0)}"
            )
            
        except Exception as e:
            logger.error(f"Daily automation error: {e}", exc_info=True)
            results["errors"].append({
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return results
    
    def _batch_process_generated(
        self,
        generation_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Batch process generated content"""
        processed = []
        
        for item in generation_results:
            if item.get("status") == "completed":
                media_path = Path(item.get("media_path"))
                if media_path.exists():
                    # Process with batch processor
                    output_path = media_path.parent / f"processed_{media_path.name}"
                    config = self.config.get("post_processing", {})
                    
                    # Use post-processing service directly
                    from services.post_processing_service import PostProcessingService
                    post_service = PostProcessingService()
                    success = post_service.process_image(
                        media_path,
                        output_path,
                        config
                    )
                    
                    if success:
                        processed.append({
                            **item,
                            "processed_path": str(output_path)
                        })
        
        return processed
    
    def _calculate_post_times(self, count: int) -> List[datetime]:
        """Calculate optimal posting times"""
        now = datetime.utcnow()
        times = []
        
        # Default: post every 2 hours starting from now
        interval_hours = self.config.get("post_interval_hours", 2)
        
        for i in range(count):
            post_time = now + timedelta(hours=i * interval_hours)
            times.append(post_time)
        
        return times
    
    def run_batch_generation(
        self,
        count: int,
        character_id: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run batch generation workflow
        
        Args:
            count: Number of items to generate
            character_id: Character ID (optional)
            settings: Generation settings
        
        Returns:
            Batch generation results
        """
        logger.info(f"Starting batch generation: {count} items")
        
        # Get character if specified
        character_config = None
        if character_id:
            character = self.db.query(Character).filter(
                Character.id == character_id
            ).first()
            if character:
                character_config = {
                    "character_id": character_id,
                    "character": character
                }
        
        # Create pipeline with character
        pipeline = ContentGenerationPipeline(
            self.db,
            self.generation_service,
            character_config
        )
        
        # Generate content
        results = pipeline.generate_content(
            count=count,
            content_type=settings.get("content_type", "image") if settings else "image",
            settings=settings or {},
            auto_quality_check=True,
            min_quality_score=settings.get("min_quality_score", 8.0) if settings else 8.0,
            auto_retry=True,
            max_retries=settings.get("max_retries", 3) if settings else 3
        )
        
        # Filter by quality
        filtered = self.quality_controller.filter_content(
            [
                {
                    "path": r.get("media_path"),
                    "type": settings.get("content_type", "image") if settings else "image",
                    "job_id": r.get("job_id"),
                    "media_id": r.get("media_id")
                }
                for r in results
                if r.get("status") == "completed"
            ],
            min_score=settings.get("min_quality_score", 8.0) if settings else 8.0
        )
        
        return {
            "generated": results,
            "filtered": filtered,
            "total": len(results),
            "passed": len(filtered.get("passed", [])),
            "rejected": len(filtered.get("rejected", []))
        }
