"""
ControlNet Service
Pose, depth, edge control for generation using ComfyUI ControlNet workflows
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ControlNetService:
    """Service for ControlNet-based generation control"""
    
    def __init__(self, comfyui_client):
        """Initialize ControlNet service"""
        self.comfyui_client = comfyui_client
    
    def generate_with_pose(self, prompt: str, pose_image_path: str, **kwargs) -> str:
        """
        Generate image with pose control
        
        Args:
            prompt: Text prompt
            pose_image_path: Path to pose reference image
            **kwargs: Additional generation parameters
        
        Returns:
            Path to generated image
        """
        logger.info(f"Generating with pose control: {pose_image_path}")
        
        try:
            workflow = self._build_controlnet_workflow("openpose", pose_image_path, prompt, **kwargs)
            prompt_id = self.comfyui_client.queue_prompt(workflow)
            result = self.comfyui_client.wait_for_completion(prompt_id)
            
            if result and result.get("output_images"):
                return result["output_images"][0]
            raise Exception("ControlNet pose generation failed")
        except Exception as e:
            logger.error(f"ControlNet pose error: {e}")
            raise
    
    def generate_with_depth(self, prompt: str, depth_image_path: str, **kwargs) -> str:
        """
        Generate image with depth control
        
        Args:
            prompt: Text prompt
            depth_image_path: Path to depth map
            **kwargs: Additional generation parameters
        
        Returns:
            Path to generated image
        """
        logger.info(f"Generating with depth control: {depth_image_path}")
        
        try:
            workflow = self._build_controlnet_workflow("depth", depth_image_path, prompt, **kwargs)
            prompt_id = self.comfyui_client.queue_prompt(workflow)
            result = self.comfyui_client.wait_for_completion(prompt_id)
            
            if result and result.get("output_images"):
                return result["output_images"][0]
            raise Exception("ControlNet depth generation failed")
        except Exception as e:
            logger.error(f"ControlNet depth error: {e}")
            raise
    
    def generate_with_edges(self, prompt: str, edge_image_path: str, **kwargs) -> str:
        """
        Generate image with edge control
        
        Args:
            prompt: Text prompt
            edge_image_path: Path to edge image (Canny)
            **kwargs: Additional generation parameters
        
        Returns:
            Path to generated image
        """
        logger.info(f"Generating with edge control: {edge_image_path}")
        
        try:
            workflow = self._build_controlnet_workflow("canny", edge_image_path, prompt, **kwargs)
            prompt_id = self.comfyui_client.queue_prompt(workflow)
            result = self.comfyui_client.wait_for_completion(prompt_id)
            
            if result and result.get("output_images"):
                return result["output_images"][0]
            raise Exception("ControlNet edge generation failed")
        except Exception as e:
            logger.error(f"ControlNet edge error: {e}")
            raise
    
    def _build_controlnet_workflow(self, control_type: str, control_image_path: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Build ControlNet workflow"""
        # Model selection
        model_name = kwargs.get("model", "realisticVisionV60B1_v51HyperInpaintVAE.safetensors")
        strength = kwargs.get("controlnet_strength", 1.0)
        
        # ControlNet model mapping
        controlnet_models = {
            "openpose": "control_v11p_sd15_openpose.pth",
            "depth": "control_v11f1p_sd15_depth.pth",
            "canny": "control_v11p_sd15_canny.pth"
        }
        
        controlnet_model = controlnet_models.get(control_type, controlnet_models["openpose"])
        
        workflow = {
            "1": {
                "inputs": {
                    "ckpt_name": model_name
                },
                "class_type": "CheckpointLoaderSimple"
            },
            "2": {
                "inputs": {
                    "text": prompt,
                    "clip": ["1", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "3": {
                "inputs": {
                    "control_net_name": controlnet_model,
                    "image": control_image_path,
                    "strength": strength
                },
                "class_type": "ControlNetLoader"
            },
            "4": {
                "inputs": {
                    "positive": ["2", 0],
                    "negative": ["2", 0],
                    "control_net": ["3", 0],
                    "model": ["1", 0]
                },
                "class_type": "ControlNetApply"
            }
        }
        
        return workflow
