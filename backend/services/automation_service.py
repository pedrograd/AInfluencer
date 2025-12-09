"""
Automation Service
Handles smart batch generation, templates, scheduled generation, workflow automation
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from pathlib import Path
import json

from models import GenerationJob, Character

logger = logging.getLogger(__name__)

class AutomationService:
    """Service for automation features"""
    
    def __init__(self, db: Session, generation_service):
        """Initialize automation service"""
        self.db = db
        self.generation_service = generation_service
        self.templates_dir = Path("templates")
        self.templates_dir.mkdir(exist_ok=True)
    
    def smart_batch_generate(
        self,
        character_id: Optional[str],
        count: int,
        prompt_template: str,
        settings_template: Optional[Dict[str, Any]],
        quality_threshold: float,
        auto_filter: bool
    ) -> GenerationJob:
        """
        Smart batch generation with quality filtering
        
        Args:
            character_id: Optional character ID
            count: Number of images to generate
            prompt_template: Prompt template with variables
            settings_template: Generation settings template
            quality_threshold: Minimum quality score
            auto_filter: Auto-reject low quality
        
        Returns:
            Batch generation job
        """
        from models import GenerationJob
        
        # Create batch job
        batch_job = GenerationJob(
            type="batch",
            status="pending",
            prompt=prompt_template,
            settings=settings_template or {},
            metadata={
                "character_id": character_id,
                "count": count,
                "quality_threshold": quality_threshold,
                "auto_filter": auto_filter
            }
        )
        self.db.add(batch_job)
        self.db.commit()
        self.db.refresh(batch_job)
        
        # Generate variations with quality filtering
        logger.info(f"Smart batch generation started: {count} images")
        
        # Start batch generation in background
        import threading
        def generate_batch():
            try:
                from services.quality_scorer_service import QualityScorer
                quality_scorer = QualityScorer()
                
                generated_count = 0
                approved_count = 0
                rejected_count = 0
                
                batch_job.status = "processing"
                self.db.commit()
                
                for i in range(count):
                    try:
                        # Generate variation of prompt
                        variation_prompt = self._generate_variation(prompt_template, i)
                        
                        # Generate image
                        job = self.generation_service.generate_image(
                            prompt=variation_prompt,
                            negative_prompt=settings_template.get("negative_prompt") if settings_template else None,
                            character_id=character_id,
                            settings=settings_template
                        )
                        
                        # Wait for generation to complete
                        max_wait = 300  # 5 minutes max
                        wait_time = 0
                        while job.status in ["pending", "processing"] and wait_time < max_wait:
                            import time
                            time.sleep(2)
                            wait_time += 2
                            self.db.refresh(job)
                        
                        if job.status == "completed" and job.result_path:
                            # Score quality
                            quality_result = quality_scorer.score_image(job.result_path)
                            overall_score = quality_result.get("overall", 0.0)
                            
                            generated_count += 1
                            
                            # Check quality threshold
                            if overall_score >= quality_threshold:
                                approved_count += 1
                                if auto_filter:
                                    # Auto-approve high quality
                                    logger.info(f"Batch item {i+1}/{count}: Approved (score: {overall_score:.2f})")
                            else:
                                rejected_count += 1
                                if auto_filter:
                                    # Mark as rejected
                                    job.meta_data = job.meta_data or {}
                                    job.meta_data["batch_rejected"] = True
                                    job.meta_data["quality_score"] = overall_score
                                    self.db.commit()
                                    logger.info(f"Batch item {i+1}/{count}: Rejected (score: {overall_score:.2f} < {quality_threshold})")
                        else:
                            logger.warning(f"Batch item {i+1}/{count}: Generation failed")
                            rejected_count += 1
                            
                    except Exception as e:
                        logger.error(f"Error in batch generation item {i+1}: {e}")
                        rejected_count += 1
                        continue
                
                # Update batch job status
                batch_job.status = "completed"
                batch_job.meta_data = batch_job.meta_data or {}
                batch_job.meta_data.update({
                    "generated_count": generated_count,
                    "approved_count": approved_count,
                    "rejected_count": rejected_count,
                    "approval_rate": approved_count / generated_count if generated_count > 0 else 0
                })
                self.db.commit()
                
                logger.info(f"Batch generation complete: {approved_count}/{generated_count} approved")
                
            except Exception as e:
                logger.error(f"Batch generation error: {e}")
                batch_job.status = "failed"
                batch_job.error_message = str(e)
                self.db.commit()
        
        # Start batch generation in background thread
        thread = threading.Thread(target=generate_batch, daemon=True)
        thread.start()
        
        return batch_job
    
    def _generate_variation(self, template: str, index: int) -> str:
        """Generate a variation of the prompt template"""
        import random
        import re
        
        # Simple variation: add index-based variations
        variations = [
            f"{template}, variation {index+1}",
            f"{template}, style {index+1}",
            f"{template}, pose {index+1}",
        ]
        
        # If template has variables, replace them
        if "{variation}" in template:
            return template.replace("{variation}", str(index+1))
        elif "{index}" in template:
            return template.replace("{index}", str(index+1))
        else:
            # Add variation suffix
            return f"{template}, variation {index+1}"
    
    def create_generation_template(
        self,
        name: str,
        prompt: str,
        negative_prompt: str,
        settings: Optional[Dict[str, Any]],
        character_id: Optional[str]
    ) -> Dict[str, Any]:
        """Create a generation template"""
        import uuid
        template = {
            "id": str(uuid.uuid4()),
            "name": name,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "settings": settings or {},
            "character_id": character_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Save template
        template_path = self.templates_dir / f"{template['id']}.json"
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2)
        
        return template
    
    def list_generation_templates(self) -> List[Dict[str, Any]]:
        """List all generation templates"""
        templates = []
        for template_file in self.templates_dir.glob("*.json"):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template = json.load(f)
                    templates.append(template)
            except Exception as e:
                logger.error(f"Error reading template {template_file}: {e}")
        
        return templates
    
    def schedule_generation(
        self,
        prompt: str,
        scheduled_time: datetime,
        character_id: Optional[str],
        settings: Optional[Dict[str, Any]]
    ) -> GenerationJob:
        """Schedule a generation for later"""
        from models import GenerationJob
        
        job = GenerationJob(
            type="image",
            status="scheduled",
            prompt=prompt,
            settings=settings or {},
            character_id=character_id,
            metadata={
                "scheduled_at": scheduled_time.isoformat()
            }
        )
        
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        # Schedule the job using a simple scheduler
        self._schedule_job(job, scheduled_time)
        logger.info(f"Generation scheduled for {scheduled_time}")
        
        return job
    
    def _schedule_job(self, job: GenerationJob, scheduled_time: datetime):
        """Schedule a job to run at a specific time"""
        import threading
        import time
        from datetime import datetime
        
        def run_scheduled_job():
            try:
                # Wait until scheduled time
                now = datetime.utcnow()
                if scheduled_time > now:
                    wait_seconds = (scheduled_time - now).total_seconds()
                    logger.info(f"Waiting {wait_seconds:.0f} seconds until scheduled time")
                    time.sleep(wait_seconds)
                
                # Check if job still exists and is scheduled
                self.db.refresh(job)
                if job.status == "scheduled":
                    # Update job status and trigger generation
                    job.status = "pending"
                    job.meta_data = job.meta_data or {}
                    job.meta_data["scheduled_at"] = scheduled_time.isoformat()
                    job.meta_data["started_at"] = datetime.utcnow().isoformat()
                    self.db.commit()
                    
                    # Trigger generation
                    try:
                        if job.type == "image":
                            self.generation_service.generate_image(
                                prompt=job.prompt,
                                negative_prompt=job.negative_prompt,
                                character_id=job.character_id,
                                settings=job.settings
                            )
                        elif job.type == "video":
                            # Video generation would go here
                            pass
                    except Exception as e:
                        logger.error(f"Error executing scheduled job {job.id}: {e}")
                        job.status = "failed"
                        job.error_message = str(e)
                        self.db.commit()
            except Exception as e:
                logger.error(f"Error in scheduled job execution: {e}")
                job.status = "failed"
                job.error_message = str(e)
                self.db.commit()
        
        # Start scheduler thread
        thread = threading.Thread(target=run_scheduled_job, daemon=True)
        thread.start()
    
    def set_job_priority(self, job_id: str, priority: str) -> GenerationJob:
        """Set job priority (low, normal, high, urgent)"""
        job = self.db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        if not job.meta_data:
            job.meta_data = {}
        
        job.meta_data["priority"] = priority
        self.db.commit()
        self.db.refresh(job)
        
        return job
    
    def get_queue_with_priorities(self) -> Dict[str, Any]:
        """Get generation queue with priorities"""
        jobs = self.db.query(GenerationJob).filter(
            GenerationJob.status.in_(["pending", "queued", "processing"])
        ).all()
        
        # Sort by priority
        priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
        
        sorted_jobs = sorted(
            jobs,
            key=lambda j: priority_order.get(j.meta_data.get("priority", "normal"), 2)
        )
        
        return {
            "total": len(sorted_jobs),
            "jobs": [
                {
                    "id": job.id,
                    "status": job.status,
                    "priority": job.meta_data.get("priority", "normal"),
                    "created_at": job.created_at.isoformat() if job.created_at else None
                }
                for job in sorted_jobs
            ]
        }
    
    def parallel_generate(
        self,
        jobs: List[Dict[str, Any]],
        max_parallel: int
    ) -> List[GenerationJob]:
        """Generate multiple jobs in parallel"""
        results = []
        
        # Process in batches
        for i in range(0, len(jobs), max_parallel):
            batch = jobs[i:i + max_parallel]
            
            for job_data in batch:
                try:
                    job = self.generation_service.generate_image(
                        prompt=job_data.get("prompt", ""),
                        negative_prompt=job_data.get("negative_prompt"),
                        character_id=job_data.get("character_id"),
                        settings=job_data.get("settings", {})
                    )
                    results.append(job)
                except Exception as e:
                    logger.error(f"Parallel generation error: {e}")
        
        return results
