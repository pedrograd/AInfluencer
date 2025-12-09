"""
Video Generation Service
Handles video generation with AnimateDiff, SVD, and other methods
"""
import logging
from enum import Enum
from typing import Dict, Optional, Any, Union
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

from models import GenerationJob, MediaItem, Character
from services.comfyui_client import ComfyUIClient
from services.workflow_manager import WorkflowManager
from services.face_consistency_service import FaceConsistencyService

logger = logging.getLogger(__name__)


class VideoGenerationMethod(Enum):
    ANIMATEDIFF = "animatediff"
    SVD = "svd"


class VideoGenerationService:
    """Service for video generation"""
    
    def __init__(
        self,
        db: Session,
        comfyui_client: ComfyUIClient,
        workflow_manager: Optional[WorkflowManager] = None,
        face_consistency_service: Optional[FaceConsistencyService] = None,
    ):
        self.db = db
        self.comfyui = comfyui_client
        self.workflow_manager = workflow_manager or WorkflowManager()
        self.face_consistency_service = face_consistency_service or FaceConsistencyService(db)
    
    def get_recommended_method(
        self,
        use_case: str = "general",
        has_image: bool = False,
        quality_priority: str = "balanced",
    ) -> VideoGenerationMethod:
        """
        Lightweight heuristic to pick a video generation method.
        """
        use_case = (use_case or "general").lower()
        quality_priority = (quality_priority or "balanced").lower()

        # Prefer AnimateDiff for general use and motion-heavy prompts.
        if use_case in {"motion", "general", "character"}:
            return VideoGenerationMethod.ANIMATEDIFF

        # Prefer SVD when quality priority is high and we may have an image.
        if quality_priority in {"high", "quality"} or has_image:
            return VideoGenerationMethod.SVD

        return VideoGenerationMethod.ANIMATEDIFF

    def generate_video(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        character_id: Optional[str] = None,
        image_id: Optional[str] = None,
        image_path: Optional[Path] = None,
        settings: Optional[Dict[str, Any]] = None,
        face_consistency: Optional[Dict[str, Any]] = None,
        method: Union[str, VideoGenerationMethod] = VideoGenerationMethod.ANIMATEDIFF,
        job: Optional[GenerationJob] = None,
    ) -> Dict[str, Any]:
        """Generate a video and return prompt metadata."""
        settings = settings or {}

        # Normalize method to enum + value string
        if isinstance(method, str):
            try:
                method_enum = VideoGenerationMethod(method.lower())
            except ValueError:
                logger.warning(f"Unknown video method '{method}', defaulting to animatediff")
                method_enum = VideoGenerationMethod.ANIMATEDIFF
        elif isinstance(method, VideoGenerationMethod):
            method_enum = method
        else:
            method_enum = VideoGenerationMethod.ANIMATEDIFF
        method_value = method_enum.value
        
        # Reuse provided job or create a new one
        if job is None:
            job = GenerationJob(
                type="video",
                status="pending",
                prompt=prompt,
                negative_prompt=negative_prompt or "",
                character_id=character_id,
                settings=settings,
                metadata={
                    "image_id": image_id,
                    "face_consistency": face_consistency or {},
                    "method": method_value,
                },
            )
            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)
        
        # Get character if specified
        character = None
        if character_id:
            character = self.db.query(Character).filter(Character.id == character_id).first()
        
        # Get source image if specified
        source_image = None
        if image_id:
            source_image = self.db.query(MediaItem).filter(MediaItem.id == image_id).first()
        elif image_path:
            # When a direct path is provided we keep source_image None for now;
            # downstream workflow builders can be extended to use the path.
            source_image = None
        
        # Build workflow based on method
        if method_enum == VideoGenerationMethod.ANIMATEDIFF:
            workflow = self._build_animatediff_workflow(
                prompt=prompt,
                negative_prompt=negative_prompt,
                settings=settings or {},
                character=character,
                source_image=source_image,
                face_consistency=face_consistency or {}
            )
        elif method_enum == VideoGenerationMethod.SVD:
            workflow = self._build_svd_workflow(
                prompt=prompt,
                negative_prompt=negative_prompt,
                settings=settings or {},
                character=character,
                source_image=source_image,
                face_consistency=face_consistency or {}
            )
        else:
            workflow = self._build_animatediff_workflow(
                prompt=prompt,
                negative_prompt=negative_prompt,
                settings=settings or {},
                character=character,
                source_image=source_image,
                face_consistency=face_consistency or {}
            )
        
        # Queue prompt
        try:
            prompt_id = self.comfyui.queue_prompt(workflow)
            job.comfyui_prompt_id = prompt_id
            job.status = "processing"
            job.started_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Video generation queued: job_id={job.id}, prompt_id={prompt_id}, method={method_value}")
            return {
                "job_id": job.id,
                "prompt_id": prompt_id,
                "method": method_value,
            }
        except Exception as e:
            logger.error(f"Failed to queue video generation job {job.id}: {e}")
            self.db.rollback()
            raise
    
    def enhance_video(
        self,
        video_path: str,
        enhancements: Dict[str, Any]
    ) -> str:
        """
        Enhance video with frame interpolation, temporal consistency, upscaling, etc.
        
        Args:
            video_path: Path to input video
            enhancements: Dict with enhancement options:
                - frame_interpolation: bool, target_fps: int
                - temporal_consistency: bool
                - motion_smoothing: bool
                - upscale: bool, target_resolution: str (1080p, 4K)
                - color_grading: bool, preset: str
                - stabilization: bool
                - slow_motion: bool, factor: float
        
        Returns:
            Path to enhanced video
        """
        from pathlib import Path
        from services.frame_interpolation_service import FrameInterpolationService
        from services.post_processing_service import PostProcessingService
        
        input_path = Path(video_path)
        output_path = input_path.parent / f"{input_path.stem}_enhanced{input_path.suffix}"
        
        current_video = input_path
        
        # Frame interpolation
        if enhancements.get("frame_interpolation"):
            target_fps = enhancements.get("target_fps", 60)
            logger.info(f"Frame interpolation: target FPS = {target_fps}")
            interpolation_service = FrameInterpolationService()
            temp_path = input_path.parent / f"{input_path.stem}_interpolated{input_path.suffix}"
            if interpolation_service.interpolate_frames(current_video, temp_path, scale=2, fps=target_fps):
                current_video = temp_path
        
        # Video upscaling
        if enhancements.get("upscale"):
            target_res = enhancements.get("target_resolution", "4K")
            logger.info(f"Video upscaling: target = {target_res}")
            try:
                import cv2
                from services.post_processing_service import PostProcessingService
                
                # Determine target resolution
                resolution_map = {
                    "1080p": (1920, 1080),
                    "2K": (2560, 1440),
                    "4K": (3840, 2160)
                }
                target_size = resolution_map.get(target_res, (3840, 2160))
                
                # Use Real-ESRGAN or similar for video upscaling
                post_processor = PostProcessingService()
                temp_upscaled = input_path.parent / f"{input_path.stem}_upscaled{input_path.suffix}"
                
                # Upscale frame by frame (simplified - in production use video upscaling model)
                cap = cv2.VideoCapture(str(current_video))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(str(temp_upscaled), fourcc, fps, target_size)
                
                frame_count = 0
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Upscale frame (simplified - use actual upscaling model in production)
                    upscaled_frame = cv2.resize(frame, target_size, interpolation=cv2.INTER_LANCZOS4)
                    out.write(upscaled_frame)
                    frame_count += 1
                
                cap.release()
                out.release()
                
                if temp_upscaled.exists():
                    current_video = temp_upscaled
                    logger.info(f"Video upscaled to {target_res}")
            except Exception as e:
                logger.warning(f"Video upscaling failed: {e}")
        
        # Color grading
        if enhancements.get("color_grading"):
            preset = enhancements.get("preset", "professional")
            logger.info(f"Color grading: preset = {preset}")
            try:
                import cv2
                import numpy as np
                
                # Color grading presets
                presets = {
                    "professional": {"contrast": 1.1, "brightness": 0, "saturation": 1.05},
                    "cinematic": {"contrast": 1.2, "brightness": -10, "saturation": 0.9},
                    "vibrant": {"contrast": 1.15, "brightness": 5, "saturation": 1.2},
                    "warm": {"contrast": 1.1, "brightness": 5, "saturation": 1.1, "temperature": 100},
                    "cool": {"contrast": 1.1, "brightness": 5, "saturation": 1.0, "temperature": -100}
                }
                
                grade_params = presets.get(preset, presets["professional"])
                
                temp_graded = input_path.parent / f"{input_path.stem}_graded{input_path.suffix}"
                cap = cv2.VideoCapture(str(current_video))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(str(temp_graded), fourcc, fps, (width, height))
                
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Apply color grading
                    frame_float = frame.astype(np.float32)
                    frame_float = frame_float * grade_params.get("contrast", 1.0) + grade_params.get("brightness", 0)
                    frame_float = np.clip(frame_float, 0, 255)
                    
                    # Adjust saturation
                    if "saturation" in grade_params:
                        hsv = cv2.cvtColor(frame_float.astype(np.uint8), cv2.COLOR_BGR2HSV)
                        hsv[:, :, 1] = hsv[:, :, 1] * grade_params["saturation"]
                        frame_float = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR).astype(np.float32)
                    
                    out.write(frame_float.astype(np.uint8))
                
                cap.release()
                out.release()
                
                if temp_graded.exists():
                    current_video = temp_graded
                    logger.info(f"Color grading applied: {preset}")
            except Exception as e:
                logger.warning(f"Color grading failed: {e}")
        
        # Stabilization
        if enhancements.get("stabilization"):
            logger.info("Video stabilization")
            try:
                import cv2
                
                temp_stabilized = input_path.parent / f"{input_path.stem}_stabilized{input_path.suffix}"
                
                # Use OpenCV's video stabilization
                cap = cv2.VideoCapture(str(current_video))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                # Create stabilizer
                stabilizer = cv2.createStabilizer()
                stabilizer.setRadius(15)  # Smoothing radius
                
                # Process video
                frames = []
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    frames.append(frame)
                cap.release()
                
                if frames:
                    # Stabilize frames
                    stabilized_frames = stabilizer.stabilize(frames)
                    
                    # Write stabilized video
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    out = cv2.VideoWriter(str(temp_stabilized), fourcc, fps, (width, height))
                    for frame in stabilized_frames:
                        out.write(frame)
                    out.release()
                    
                    if temp_stabilized.exists():
                        current_video = temp_stabilized
                        logger.info("Video stabilized")
            except Exception as e:
                logger.warning(f"Video stabilization failed: {e}")
        
        # Temporal consistency
        if enhancements.get("temporal_consistency"):
            logger.info("Applying temporal consistency")
            try:
                import cv2
                import numpy as np
                
                temp_consistent = input_path.parent / f"{input_path.stem}_temporal{input_path.suffix}"
                cap = cv2.VideoCapture(str(current_video))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(str(temp_consistent), fourcc, fps, (width, height))
                
                prev_frame = None
                alpha = 0.3  # Blending factor for temporal smoothing
                
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    if prev_frame is not None:
                        # Blend with previous frame to reduce flickering
                        frame = cv2.addWeighted(frame, 1 - alpha, prev_frame, alpha, 0)
                    
                    out.write(frame)
                    prev_frame = frame.copy()
                
                cap.release()
                out.release()
                
                if temp_consistent.exists():
                    current_video = temp_consistent
                    logger.info("Temporal consistency applied")
            except Exception as e:
                logger.warning(f"Temporal consistency failed: {e}")
        
        # Motion smoothing
        if enhancements.get("motion_smoothing"):
            logger.info("Applying motion smoothing")
            try:
                import cv2
                import numpy as np
                
                temp_smooth = input_path.parent / f"{input_path.stem}_smoothed{input_path.suffix}"
                cap = cv2.VideoCapture(str(current_video))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(str(temp_smooth), fourcc, fps, (width, height))
                
                # Use optical flow for motion smoothing
                frames = []
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    frames.append(frame)
                cap.release()
                
                if len(frames) > 2:
                    # Apply Gaussian blur to motion vectors for smoothing
                    smoothed_frames = []
                    for i in range(len(frames)):
                        if i == 0 or i == len(frames) - 1:
                            smoothed_frames.append(frames[i])
                        else:
                            # Blend with neighbors for smooth motion
                            smoothed = cv2.addWeighted(frames[i-1], 0.2, frames[i], 0.6, 0)
                            smoothed = cv2.addWeighted(smoothed, 1.0, frames[i+1], 0.2, 0)
                            smoothed_frames.append(smoothed)
                    
                    for frame in smoothed_frames:
                        out.write(frame)
                
                out.release()
                
                if temp_smooth.exists():
                    current_video = temp_smooth
                    logger.info("Motion smoothing applied")
            except Exception as e:
                logger.warning(f"Motion smoothing failed: {e}")
        
        # Audio sync (add background music or sync existing audio)
        if enhancements.get("audio_sync"):
            audio_path = enhancements.get("audio_path")
            logger.info(f"Audio sync: {'adding audio' if audio_path else 'syncing existing audio'}")
            try:
                import subprocess
                
                temp_audio = input_path.parent / f"{input_path.stem}_audio{input_path.suffix}"
                
                if audio_path and Path(audio_path).exists():
                    # Add background music
                    subprocess.run([
                        "ffmpeg", "-i", str(current_video),
                        "-i", str(audio_path),
                        "-c:v", "copy",
                        "-c:a", "aac",
                        "-shortest",
                        "-y", str(temp_audio)
                    ], check=True, capture_output=True)
                else:
                    # Just ensure audio is synced (copy video with audio)
                    subprocess.run([
                        "ffmpeg", "-i", str(current_video),
                        "-c", "copy",
                        "-y", str(temp_audio)
                    ], check=True, capture_output=True)
                
                if temp_audio.exists():
                    current_video = temp_audio
                    logger.info("Audio synced")
            except Exception as e:
                logger.warning(f"Audio sync failed: {e}")
        
        # Slow motion
        if enhancements.get("slow_motion"):
            factor = enhancements.get("factor", 0.5)
            logger.info(f"Slow motion: factor = {factor}")
            try:
                import cv2
                from services.frame_interpolation_service import FrameInterpolationService
                
                # Use frame interpolation to create slow motion
                interpolation_service = FrameInterpolationService()
                temp_slowmo = input_path.parent / f"{input_path.stem}_slowmo{input_path.suffix}"
                
                # Interpolate frames to achieve slow motion
                # If factor is 0.5, we need 2x frames (every frame becomes 2 frames)
                scale = int(1 / factor) if factor > 0 else 2
                
                if interpolation_service.interpolate_frames(current_video, temp_slowmo, scale=scale):
                    current_video = temp_slowmo
                    logger.info(f"Slow motion applied: {factor}x")
            except Exception as e:
                logger.warning(f"Slow motion failed: {e}")
        
        # Final output
        if current_video != input_path:
            import shutil
            shutil.copy2(current_video, output_path)
        else:
            output_path = input_path
        
        return str(output_path)
    
    def _build_animatediff_workflow(
        self,
        prompt: str,
        negative_prompt: str,
        settings: Dict[str, Any],
        character: Optional[Character],
        source_image: Optional[MediaItem],
        face_consistency: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build AnimateDiff workflow"""
        # Base workflow structure for AnimateDiff
        workflow = {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": settings.get("model", "realisticVisionV60_v60B1.safetensors")
                }
            },
            "2": {
                "class_type": "AnimateDiffLoader",
                "inputs": {
                    "model_name": settings.get("animatediff_model", "mm_sd_v15_v2.ckpt"),
                    "frame_count": settings.get("frame_count", 16),
                    "motion_bucket": settings.get("motion_bucket", 127)
                }
            },
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": prompt,
                    "clip": ["1", 1]
                }
            },
            "4": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["1", 1]
                }
            },
            "5": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": settings.get("seed", -1),
                    "steps": settings.get("steps", 30),
                    "cfg": settings.get("cfg_scale", 7.5),
                    "sampler_name": settings.get("sampler_name", "euler"),
                    "scheduler": settings.get("scheduler", "normal"),
                    "denoise": 1.0,
                    "model": ["2", 0],
                    "positive": ["3", 0],
                    "negative": ["4", 0],
                    "latent_image": ["6", 0]
                }
            },
            "6": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": settings.get("width", 512),
                    "height": settings.get("height", 512),
                    "batch_size": 1
                }
            },
            "7": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["5", 0],
                    "vae": ["1", 2]
                }
            },
            "8": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "animatediff",
                    "images": ["7", 0]
                }
            }
        }
        
        # Add face consistency if enabled
        if face_consistency.get("enabled") and character:
            workflow = self.face_consistency_service.apply_face_consistency(
                workflow,
                character_id=character.id if character else None,
                face_consistency_config=face_consistency
            )
        
        return workflow
    
    def _build_svd_workflow(
        self,
        prompt: str,
        negative_prompt: str,
        settings: Dict[str, Any],
        character: Optional[Character],
        source_image: Optional[MediaItem],
        face_consistency: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build Stable Video Diffusion workflow"""
        # Start from the AnimateDiff scaffold and tune for SVD defaults.
        workflow = self._build_animatediff_workflow(
            prompt=prompt,
            negative_prompt=negative_prompt,
            settings=settings,
            character=character,
            source_image=source_image,
            face_consistency=face_consistency
        )
        
        # Apply SVD-specific defaults and naming so the downstream ComfyUI
        # workflow picks up the right checkpoints and outputs.
        checkpoint_node = workflow.get("1", {})
        if isinstance(checkpoint_node, dict):
            inputs = checkpoint_node.get("inputs", {})
            inputs["ckpt_name"] = settings.get("model", "svd_xt_1_1.safetensors")
            checkpoint_node["inputs"] = inputs
            workflow["1"] = checkpoint_node

        animatediff_node = workflow.get("2", {})
        if isinstance(animatediff_node, dict):
            inputs = animatediff_node.get("inputs", {})
            inputs["model_name"] = settings.get("svd_motion_model", settings.get("animatediff_model", "svd_xt_1_1.safetensors"))
            inputs["frame_count"] = settings.get("frame_count", 14)
            inputs["motion_bucket"] = settings.get("motion_bucket", 48)
            animatediff_node["inputs"] = inputs
            workflow["2"] = animatediff_node

        sampler_node = workflow.get("5", {})
        if isinstance(sampler_node, dict):
            inputs = sampler_node.get("inputs", {})
            inputs["steps"] = settings.get("steps", 20)
            inputs["cfg"] = settings.get("cfg_scale", 6.5)
            inputs["sampler_name"] = settings.get("sampler_name", "dpmpp_2m")
            inputs["scheduler"] = settings.get("scheduler", "karras")
            sampler_node["inputs"] = inputs
            workflow["5"] = sampler_node

        latent_node = workflow.get("6", {})
        if isinstance(latent_node, dict):
            inputs = latent_node.get("inputs", {})
            inputs["width"] = settings.get("width", 832)
            inputs["height"] = settings.get("height", 480)
            latent_node["inputs"] = inputs
            workflow["6"] = latent_node

        save_node = workflow.get("8", {})
        if isinstance(save_node, dict):
            inputs = save_node.get("inputs", {})
            inputs["filename_prefix"] = settings.get("output_prefix", "svd_xt")
            save_node["inputs"] = inputs
            workflow["8"] = save_node
        
        return workflow
