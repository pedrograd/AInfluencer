"""
Outpainting Service
Extend image boundaries using ComfyUI outpainting workflows
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class OutpaintingService:
    """Service for image outpainting"""
    
    def __init__(self, comfyui_client):
        """Initialize outpainting service"""
        self.comfyui_client = comfyui_client
    
    def outpaint(self, image_path: str, direction: str, pixels: int, prompt: str, **kwargs) -> str:
        """
        Extend image boundaries
        
        Args:
            image_path: Path to input image
            direction: Direction to extend (left, right, top, bottom, all)
            pixels: Number of pixels to extend
            prompt: Text prompt for extension
            **kwargs: Additional generation parameters
        
        Returns:
            Path to outpainted image
        """
        logger.info(f"Outpainting image: {image_path}, direction: {direction}, pixels: {pixels}")
        
        try:
            # Build ComfyUI outpainting workflow
            workflow = self._build_outpainting_workflow(image_path, direction, pixels, prompt, **kwargs)
            
            # Queue the workflow
            prompt_id = self.comfyui_client.queue_prompt(workflow)
            
            # Wait for completion and get result
            result = self.comfyui_client.wait_for_completion(prompt_id)
            
            if result and result.get("output_images"):
                output_path = result["output_images"][0]
                logger.info(f"Outpainting completed: {output_path}")
                return output_path
            else:
                logger.error("Outpainting failed: No output images")
                return image_path
                
        except Exception as e:
            logger.error(f"Outpainting error: {e}")
            raise
    
    def _build_outpainting_workflow(self, image_path: str, direction: str, pixels: int, prompt: str, **kwargs) -> Dict[str, Any]:
        """Build ComfyUI outpainting workflow"""
        # Calculate new dimensions based on direction
        from PIL import Image
        img = Image.open(image_path)
        width, height = img.size
        
        if direction == "left":
            new_width = width + pixels
            new_height = height
        elif direction == "right":
            new_width = width + pixels
            new_height = height
        elif direction == "top":
            new_width = width
            new_height = height + pixels
        elif direction == "bottom":
            new_width = width
            new_height = height + pixels
        else:  # all
            new_width = width + pixels * 2
            new_height = height + pixels * 2
        
        workflow = {
            "1": {
                "inputs": {
                    "image": image_path,
                    "width": new_width,
                    "height": new_height,
                    "direction": direction
                },
                "class_type": "ImageOutpainting"
            },
            "2": {
                "inputs": {
                    "text": prompt,
                    "clip": ["1", 1]
                },
                "class_type": "CLIPTextEncode"
            }
        }
        
        return workflow
