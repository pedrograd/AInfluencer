"""
Batch Generation Service
Handles batch image and video generation with queue management
"""
import logging
import asyncio
from typing import Dict, Optional, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from pathlib import Path

from models import BatchJob, BatchJobItem, GenerationJob, MediaItem
from services.generation_service import GenerationService
from services.comfyui_client import ComfyUIClient

logger = logging.getLogger(__name__)

class BatchGenerationService:
    """Service for managing batch generation jobs"""
    
    def __init__(self, db: Session, generation_service: GenerationService):
        self.db = db
        self.generation_service = generation_service
        self.active_jobs: Dict[str, asyncio.Task] = {}
    
    def create_batch_job(
        self,
        batch_type: str,
        count: int,
        prompt_template: str,
        variations: Optional[List[str]] = None,
        character_id: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
        priority: str = "normal"
    ) -> BatchJob:
        """Create a new batch generation job"""
        batch_job = BatchJob(
            type=batch_type,
            status="pending",
            total_count=count,
            completed_count=0,
            failed_count=0,
            character_id=character_id,
            prompt_template=prompt_template,
            settings_template=settings or {},
            metadata={
                "variations": variations or [],
                "priority": priority
            }
        )
        
        self.db.add(batch_job)
        self.db.commit()
        self.db.refresh(batch_job)
        
        # Create batch job items
        variations_list = variations or [""]
        for i in range(count):
            # Select variation (cycle through if count > variations)
            variation = variations_list[i % len(variations_list)]
            prompt = prompt_template.format(variation=variation) if "{variation}" in prompt_template else prompt_template
            
            batch_item = BatchJobItem(
                batch_job_id=batch_job.id,
                index=i + 1,
                prompt=prompt,
                negative_prompt=settings.get("negative_prompt", "") if settings else "",
                settings=settings or {},
                status="pending"
            )
            self.db.add(batch_item)
        
        self.db.commit()
        
        logger.info(f"Batch job created: {batch_job.id}, count={count}")
        return batch_job
    
    def get_batch_job(self, batch_job_id: str) -> Optional[BatchJob]:
        """Get batch job by ID"""
        return self.db.query(BatchJob).filter(BatchJob.id == batch_job_id).first()
    
    def get_batch_job_status(self, batch_job_id: str) -> Dict[str, Any]:
        """Get detailed batch job status"""
        batch_job = self.get_batch_job(batch_job_id)
        if not batch_job:
            return {}
        
        # Get all items
        items = self.db.query(BatchJobItem).filter(
            BatchJobItem.batch_job_id == batch_job_id
        ).order_by(BatchJobItem.index).all()
        
        # Format items
        formatted_items = []
        for item in items:
            formatted_items.append({
                "id": item.id,
                "index": item.index,
                "status": item.status,
                "progress": 0.0,  # TODO: Get from generation job
                "media_id": item.result_media_id if hasattr(item, 'result_media_id') else None,
                "error_message": item.error_message
            })
        
        # Calculate progress
        progress = 0.0
        if batch_job.total_count > 0:
            progress = batch_job.completed_count / batch_job.total_count
        
        return {
            "batch_job_id": batch_job.id,
            "status": batch_job.status,
            "total_count": batch_job.total_count,
            "completed_count": batch_job.completed_count,
            "failed_count": batch_job.failed_count,
            "progress": progress,
            "items": formatted_items
        }
    
    async def process_batch_job(self, batch_job_id: str):
        """Process a batch job asynchronously"""
        batch_job = self.get_batch_job(batch_job_id)
        if not batch_job:
            logger.error(f"Batch job not found: {batch_job_id}")
            return
        
        # Update status
        batch_job.status = "processing"
        batch_job.started_at = datetime.utcnow()
        self.db.commit()
        
        # Get all pending items
        items = self.db.query(BatchJobItem).filter(
            BatchJobItem.batch_job_id == batch_job_id,
            BatchJobItem.status == "pending"
        ).order_by(BatchJobItem.index).all()
        
        logger.info(f"Processing batch job {batch_job_id}: {len(items)} items")
        
        # Process items sequentially (to avoid GPU memory issues)
        for item in items:
            try:
                # Update item status
                item.status = "processing"
                self.db.commit()
                
                # Generate image/video
                if batch_job.type == "image":
                    generation_job = self.generation_service.generate_image(
                        prompt=item.prompt,
                        negative_prompt=item.negative_prompt,
                        character_id=batch_job.character_id,
                        settings=item.settings or {},
                        face_consistency=batch_job.meta_data.get("face_consistency", {})
                    )
                else:  # video
                    generation_job = self.generation_service.generate_video(
                        prompt=item.prompt,
                        negative_prompt=item.negative_prompt,
                        character_id=batch_job.character_id,
                        settings=item.settings or {},
                        face_consistency=batch_job.meta_data.get("face_consistency", {})
                    )
                
                # Link generation job to batch item
                item.generation_job_id = generation_job.id
                self.db.commit()
                
                # Wait for completion
                completed = self.generation_service.comfyui.wait_for_completion(
                    generation_job.comfyui_prompt_id,
                    timeout=600  # 10 minutes per item
                )
                
                if completed:
                    # Get result media
                    self.db.refresh(generation_job)
                    if generation_job.result_media:
                        item.result_media_id = generation_job.result_media.id
                        item.status = "completed"
                        batch_job.completed_count += 1
                    else:
                        item.status = "failed"
                        item.error_message = "No media generated"
                        batch_job.failed_count += 1
                else:
                    item.status = "failed"
                    item.error_message = "Generation timeout"
                    batch_job.failed_count += 1
                
                self.db.commit()
                
            except Exception as e:
                logger.error(f"Error processing batch item {item.id}: {e}")
                item.status = "failed"
                item.error_message = str(e)
                batch_job.failed_count += 1
                self.db.commit()
        
        # Update batch job status
        if batch_job.completed_count + batch_job.failed_count >= batch_job.total_count:
            batch_job.status = "completed"
            batch_job.completed_at = datetime.utcnow()
        else:
            batch_job.status = "processing"  # Still processing
        
        self.db.commit()
        logger.info(f"Batch job {batch_job_id} completed: {batch_job.completed_count}/{batch_job.total_count}")
    
    def start_batch_job(self, batch_job_id: str):
        """Start processing a batch job in background"""
        import asyncio
        
        # Create task if not already running
        if batch_job_id not in self.active_jobs:
            loop = asyncio.get_event_loop()
            task = loop.create_task(self.process_batch_job(batch_job_id))
            self.active_jobs[batch_job_id] = task
            
            # Clean up task when done
            def cleanup(task):
                if batch_job_id in self.active_jobs:
                    del self.active_jobs[batch_job_id]
            
            task.add_done_callback(cleanup)
            logger.info(f"Started batch job processing: {batch_job_id}")
