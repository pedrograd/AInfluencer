"""
Job Monitor Service
Monitors ComfyUI generation jobs and saves results when complete
"""
import logging
import asyncio
import time
from pathlib import Path
from typing import Dict, Optional, Set
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

from models import GenerationJob, MediaItem
from services.comfyui_client import ComfyUIClient
from services.media_service import MediaService

logger = logging.getLogger(__name__)

class JobMonitorService:
    """Service for monitoring generation jobs and saving results"""
    
    def __init__(self, db: Session, comfyui_client: ComfyUIClient, media_root: Path):
        self.db = db
        self.comfyui = comfyui_client
        self.media_service = MediaService(db, media_root)
        self.monitoring_jobs: Set[str] = set()
        self.monitor_tasks: Dict[str, asyncio.Task] = {}
    
    async def monitor_job(self, job_id: str, timeout: int = 600):
        """Monitor a generation job until completion"""
        if job_id in self.monitoring_jobs:
            logger.warning(f"Job {job_id} is already being monitored")
            return
        
        self.monitoring_jobs.add(job_id)
        
        try:
            from models import GenerationJob
            
            start_time = time.time()
            last_progress = 0.0
            check_count = 0
            
            while time.time() - start_time < timeout:
                check_count += 1
                # Get job from database
                job = self.db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
                
                if not job:
                    logger.error(f"Job {job_id} not found in database")
                    break
                
                # Check if already completed
                if job.status == "completed":
                    logger.info(f"Job {job_id} already completed")
                    break
                
                if job.status == "failed":
                    logger.info(f"Job {job_id} failed: {job.error_message}")
                    break
                
                # Check ComfyUI status if processing
                if job.status == "processing" and job.comfyui_prompt_id:
                    try:
                        # Get all history (more reliable)
                        history = self.comfyui.get_history()
                        
                        if history:
                            # Handle different history formats
                            prompt_info = None
                            if isinstance(history, dict):
                                # Try direct lookup first
                                if job.comfyui_prompt_id in history:
                                    prompt_info = history[job.comfyui_prompt_id]
                                else:
                                    # Search through all entries for one with outputs
                                    for key, value in history.items():
                                        if isinstance(value, dict) and 'outputs' in value:
                                            # Check if this matches our prompt_id
                                            if 'prompt' in value:
                                                prompt_array = value.get('prompt', [])
                                                if isinstance(prompt_array, list):
                                                    for p in prompt_array:
                                                        if isinstance(p, list) and len(p) >= 2:
                                                            if p[1] == job.comfyui_prompt_id or p[0] == job.comfyui_prompt_id:
                                                                prompt_info = value
                                                                break
                                                    if prompt_info:
                                                        break
                                            # If no prompt array, assume it's our job if it has outputs
                                            if not prompt_info:
                                                prompt_info = value
                                                break
                            
                            if prompt_info:
                                # Check for completion
                                if 'outputs' in prompt_info:
                                    logger.info(f"Job {job_id} completed, saving results...")
                                    # Job completed - save results
                                    await self._save_job_results(job_id, job.comfyui_prompt_id)
                                    break
                                
                                # Check for errors
                                if 'errors' in prompt_info and prompt_info['errors']:
                                    error_msg = str(prompt_info['errors'])
                                    logger.error(f"Job {job_id} error: {error_msg}")
                                    self._fail_job(job_id, error_msg)
                                    break
                    except Exception as e:
                        # Log error but continue monitoring (don't spam logs)
                        if int(time.time() - start_time) % 20 == 0:  # Log every 20 seconds
                            logger.debug(f"Error checking ComfyUI status for job {job_id}: {e}")
                
                # Update progress (estimate based on time)
                elapsed = time.time() - start_time
                estimated_progress = min(0.95, elapsed / 120)  # Estimate 2 minutes per image
                
                if estimated_progress > last_progress + 0.05:  # Update every 5%
                    self._update_job_progress(job_id, estimated_progress)
                    last_progress = estimated_progress
                
                # Wait before next check
                await asyncio.sleep(2)
            
            # Timeout check
            if time.time() - start_time >= timeout:
                logger.warning(f"Job {job_id} monitoring timeout after {timeout}s")
                self._fail_job(job_id, "Generation timeout")
        
        except Exception as e:
            logger.error(f"Error monitoring job {job_id}: {e}", exc_info=True)
            self._fail_job(job_id, str(e))
        finally:
            self.monitoring_jobs.discard(job_id)
            if job_id in self.monitor_tasks:
                del self.monitor_tasks[job_id]
    
    async def _save_job_results(self, job_id: str, prompt_id: str):
        """Save generation results to media library"""
        try:
            from models import GenerationJob
            import tempfile
            import os
            
            # Get job
            job = self.db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found when saving results")
                return
            
            # Wait a bit for files to be written
            await asyncio.sleep(1)
            
            # Get output images from ComfyUI
            # Try multiple times as files may not be written immediately
            output_images = []
            for attempt in range(5):
                output_images = self.comfyui.get_output_images(prompt_id)
                if output_images:
                    break
                logger.debug(f"Attempt {attempt + 1}: No output images yet for job {job_id}, waiting...")
                await asyncio.sleep(2)
            
            if not output_images:
                logger.warning(f"No output images found for job {job_id}, prompt_id={prompt_id} after 5 attempts")
                # Try getting history directly to see what's available
                history = self.comfyui.get_history()
                logger.debug(f"History for prompt {prompt_id}: {type(history)}, keys: {list(history.keys()) if isinstance(history, dict) else 'N/A'}")
                self._fail_job(job_id, "No images generated")
                return
            
            # Process first image (or all if batch)
            saved_media_id = None
            for image_info in output_images:
                try:
                    # Download image from ComfyUI
                    image_data = self.comfyui.get_image(
                        image_info['filename'],
                        image_info.get('subfolder', ''),
                        image_info.get('type', 'output')
                    )
                    
                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                        tmp_file.write(image_data)
                        tmp_path = Path(tmp_file.name)
                    
                    try:
                        # Create media item (will move file to proper location)
                        media = self.media_service.create_media_item(
                            file_path=tmp_path,
                            media_type="image",
                            source="ai_generated",
                            character_id=job.character_id,
                            generation_job_id=job_id,
                            tags=["generated"]
                        )
                        
                        saved_media_id = media.id
                        logger.info(f"Job {job_id} completed, media saved: {media.id}")
                        break  # Only save first image for now
                        
                    except Exception as e:
                        logger.error(f"Error creating media item for job {job_id}: {e}", exc_info=True)
                        # Clean up temp file
                        if tmp_path.exists():
                            try:
                                os.unlink(tmp_path)
                            except:
                                pass
                        raise
                        
                except Exception as e:
                    logger.error(f"Error processing image for job {job_id}: {e}", exc_info=True)
                    continue
            
            # Complete job with media_id
            if saved_media_id:
                self._complete_job(job_id, saved_media_id, None)
            else:
                # Refresh job to check if media was set
                self.db.refresh(job)
                if not job.result_media:
                    self._fail_job(job_id, "Failed to save generated images")
        
        except Exception as e:
            logger.error(f"Error saving results for job {job_id}: {e}", exc_info=True)
            self._fail_job(job_id, f"Error saving results: {str(e)}")
    
    def _update_job_progress(self, job_id: str, progress: float):
        """Update job progress in database"""
        try:
            from models import GenerationJob
            job = self.db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if job:
                job.progress = progress
                self.db.commit()
        except Exception as e:
            logger.error(f"Error updating job progress: {e}")
    
    def _complete_job(self, job_id: str, media_id: str, output_path: Optional[Path]):
        """Mark job as completed"""
        try:
            from models import GenerationJob
            
            job = self.db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found when completing")
                return
            
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.progress = 1.0
            
            # Set media relationship (MediaItem.generation_job_id creates the relationship)
            media = self.db.query(MediaItem).filter(MediaItem.id == media_id).first()
            if media:
                media.generation_job_id = job_id
            else:
                logger.warning(f"Media {media_id} not found when completing job {job_id}")
            
            self.db.commit()
            logger.info(f"Job {job_id} marked as completed with media {media_id}")
        except Exception as e:
            logger.error(f"Error completing job {job_id}: {e}", exc_info=True)
            self.db.rollback()
    
    def _fail_job(self, job_id: str, error_message: str):
        """Mark job as failed"""
        try:
            from models import GenerationJob
            job = self.db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.failed_at = datetime.utcnow()
                job.error_message = error_message
                self.db.commit()
                logger.info(f"Job {job_id} marked as failed: {error_message}")
        except Exception as e:
            logger.error(f"Error failing job {job_id}: {e}")
    
    def start_monitoring(self, job_id: str):
        """Start monitoring a job in background"""
        if job_id in self.monitor_tasks:
            return  # Already monitoring
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop running, create new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        task = loop.create_task(self.monitor_job(job_id))
        self.monitor_tasks[job_id] = task
        
        # Clean up when done
        def cleanup(t):
            if job_id in self.monitor_tasks:
                del self.monitor_tasks[job_id]
        
        task.add_done_callback(cleanup)
        logger.info(f"Started monitoring job: {job_id}")
