"""
WebSocket Service
Handles real-time updates for generation jobs
"""
import logging
import json
import asyncio
from typing import Dict, Set, Optional
from fastapi import WebSocket
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketService:
    """Service for managing WebSocket connections and broadcasting updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.job_monitors: Dict[str, asyncio.Task] = {}
    
    async def connect(self, websocket: WebSocket, job_id: str):
        """Connect a WebSocket to a job"""
        await websocket.accept()
        
        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()
        
        self.active_connections[job_id].add(websocket)
        logger.info(f"WebSocket connected: job_id={job_id}, total={len(self.active_connections[job_id])}")
    
    def disconnect(self, websocket: WebSocket, job_id: str):
        """Disconnect a WebSocket from a job"""
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
                # Stop monitoring if no connections
                if job_id in self.job_monitors:
                    self.job_monitors[job_id].cancel()
                    del self.job_monitors[job_id]
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to a specific WebSocket"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
    
    async def broadcast(self, job_id: str, message: dict):
        """Broadcast message to all connections for a job"""
        if job_id not in self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections[job_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                disconnected.add(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.active_connections[job_id].discard(connection)
    
    async def send_job_update(
        self,
        job_id: str,
        status: str,
        progress: float,
        message: Optional[str] = None,
        media_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Send job update to all connected clients"""
        update = {
            "type": "job_update",
            "job_id": job_id,
            "status": status,
            "progress": progress,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if message:
            update["message"] = message
        if media_id:
            update["media_id"] = media_id
        if error:
            update["error"] = error
        
        await self.broadcast(job_id, update)
    
    async def send_batch_update(
        self,
        batch_job_id: str,
        status: str,
        completed_count: int,
        total_count: int,
        failed_count: int = 0,
        message: Optional[str] = None
    ):
        """Send batch job update to all connected clients"""
        progress = completed_count / total_count if total_count > 0 else 0.0
        
        update = {
            "type": "batch_update",
            "batch_job_id": batch_job_id,
            "status": status,
            "completed_count": completed_count,
            "total_count": total_count,
            "failed_count": failed_count,
            "progress": progress,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if message:
            update["message"] = message
        
        await self.broadcast(batch_job_id, update)
    
    async def monitor_job(
        self,
        job_id: str,
        comfyui_client,
        generation_service,
        db
    ):
        """Monitor a generation job and send updates"""
        try:
            last_progress = 0.0
            last_status = "pending"
            
            while True:
                # Get job status
                job = generation_service.get_job_status(job_id)
                if not job:
                    await self.send_job_update(job_id, "error", 0.0, error="Job not found")
                    break
                
                # Check if status changed
                if job.status != last_status or job.progress != last_progress:
                    message = "Processing..." if job.status == "processing" else None
                    
                    if job.status == "completed":
                        media_id = None
                        if job.result_media:
                            media_id = job.result_media.id
                        await self.send_job_update(
                            job_id,
                            "completed",
                            1.0,
                            message="Generation completed",
                            media_id=media_id
                        )
                        break
                    elif job.status == "failed":
                        await self.send_job_update(
                            job_id,
                            "failed",
                            job.progress,
                            error=job.error_message or "Generation failed"
                        )
                        break
                    else:
                        await self.send_job_update(
                            job_id,
                            job.status,
                            job.progress,
                            message=message
                        )
                    
                    last_status = job.status
                    last_progress = job.progress
                
                # Check ComfyUI status if processing
                if job.status == "processing" and job.comfyui_prompt_id:
                    history = comfyui_client.get_history(job.comfyui_prompt_id)
                    if history and job.comfyui_prompt_id in history:
                        prompt_info = history[job.comfyui_prompt_id]
                        
                        # Check for completion
                        if 'outputs' in prompt_info:
                            # Job completed, fetch and save output images
                            try:
                                from services.media_service import MediaService
                                from pathlib import Path
                                import tempfile
                                import os
                                
                                # Get output images from ComfyUI
                                output_images = comfyui_client.get_output_images(job.comfyui_prompt_id)
                                
                                if output_images:
                                    # Get the first image (or handle multiple)
                                    image_info = output_images[0]
                                    
                                    # Download image from ComfyUI
                                    image_data = comfyui_client.get_image(
                                        image_info['filename'],
                                        image_info.get('subfolder', ''),
                                        image_info.get('type', 'output')
                                    )
                                    
                                    # Save to temporary file
                                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                                        tmp_file.write(image_data)
                                        tmp_path = Path(tmp_file.name)
                                    
                                    try:
                                        # Get media root - should match main.py MEDIA_ROOT
                                        # Using relative path from backend directory
                                        backend_dir = Path(__file__).parent.parent
                                        media_root = backend_dir / "media_library"
                                        
                                        # Save to media library
                                        media_service = MediaService(db, media_root)
                                        
                                        # Create media item (will move file to proper location)
                                        media = media_service.create_media_item(
                                            file_path=tmp_path,
                                            media_type="image",
                                            source="ai_generated",
                                            character_id=job.character_id,
                                            generation_job_id=job_id,
                                            tags=["generated"]
                                        )
                                        
                                        # Complete job with media_id
                                        final_path = Path(media.file_path)
                                        generation_service.complete_job(job_id, media_id=media.id, output_path=final_path)
                                        
                                        await self.send_job_update(
                                            job_id,
                                            "completed",
                                            1.0,
                                            message="Generation completed",
                                            media_id=media.id
                                        )
                                    except Exception as e:
                                        logger.error(f"Error saving media for job {job_id}: {e}", exc_info=True)
                                        # Clean up temp file
                                        if tmp_path.exists():
                                            try:
                                                os.unlink(tmp_path)
                                            except:
                                                pass
                                        # Complete job without media_id
                                        generation_service.complete_job(job_id)
                                        await self.send_job_update(
                                            job_id,
                                            "completed",
                                            1.0,
                                            message="Generation completed (media save failed)"
                                        )
                                else:
                                    # No images found, complete job anyway
                                    logger.warning(f"No output images found for job {job_id}")
                                    generation_service.complete_job(job_id)
                                    await self.send_job_update(
                                        job_id,
                                        "completed",
                                        1.0,
                                        message="Generation completed (no images found)"
                                    )
                            except Exception as e:
                                logger.error(f"Error processing completion for job {job_id}: {e}", exc_info=True)
                                # Complete job anyway
                                generation_service.complete_job(job_id)
                                await self.send_job_update(
                                    job_id,
                                    "completed",
                                    1.0,
                                    message="Generation completed"
                                )
                            break
                        
                        # Check for errors
                        if 'errors' in prompt_info and prompt_info['errors']:
                            error_msg = str(prompt_info['errors'])
                            generation_service.fail_job(job_id, error_msg)
                            await self.send_job_update(
                                job_id,
                                "failed",
                                job.progress,
                                error=error_msg
                            )
                            break
                
                # Wait before next check
                await asyncio.sleep(2)  # Check every 2 seconds
                
        except asyncio.CancelledError:
            logger.info(f"Job monitoring cancelled: {job_id}")
        except Exception as e:
            logger.error(f"Error monitoring job {job_id}: {e}")
            await self.send_job_update(job_id, "error", 0.0, error=str(e))
    
    def start_monitoring(
        self,
        job_id: str,
        comfyui_client,
        generation_service,
        db
    ):
        """Start monitoring a job"""
        if job_id in self.job_monitors:
            return  # Already monitoring
        
        loop = asyncio.get_event_loop()
        task = loop.create_task(
            self.monitor_job(job_id, comfyui_client, generation_service, db)
        )
        self.job_monitors[job_id] = task
        
        # Clean up when done
        def cleanup(t):
            if job_id in self.job_monitors:
                del self.job_monitors[job_id]
        
        task.add_done_callback(cleanup)
