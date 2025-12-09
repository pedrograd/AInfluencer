"""
Advanced Generation Service
Handles inpainting, outpainting, image-to-image, ControlNet, style transfer, etc.
"""
import logging
from typing import Dict, Optional, Any, List, Tuple
from pathlib import Path
from PIL import Image
import numpy as np
import base64
import io

from services.comfyui_client import ComfyUIClient
from services.workflow_manager import WorkflowManager

logger = logging.getLogger(__name__)

class AdvancedGenerationService:
    """Service for advanced generation features"""
    
    def __init__(self, comfyui_client: ComfyUIClient):
        self.comfyui = comfyui_client
        self.workflow_manager = WorkflowManager()
    
    def inpainting(
        self,
        image_path: str,
        mask_path: Optional[str] = None,
        mask_data: Optional[bytes] = None,
        prompt: str = "",
        negative_prompt: str = "",
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform inpainting on an image
        
        Args:
            image_path: Path to input image
            mask_path: Path to mask image (optional, can use mask_data)
            mask_data: Mask image as bytes (optional)
            prompt: Inpainting prompt
            negative_prompt: Negative prompt
            settings: Generation settings
        
        Returns:
            Dict with workflow and configuration
        """
        # Load and prepare image
        image = Image.open(image_path)
        image_base64 = self._image_to_base64(image)
        
        # Prepare mask
        if mask_path:
            mask = Image.open(mask_path)
        elif mask_data:
            mask = Image.open(io.BytesIO(mask_data))
        else:
            raise ValueError("Either mask_path or mask_data must be provided")
        
        mask_base64 = self._image_to_base64(mask)
        
        # Build inpainting workflow
        workflow = self.workflow_manager.build_inpainting_workflow(
            image_base64=image_base64,
            mask_base64=mask_base64,
            prompt=prompt,
            negative_prompt=negative_prompt,
            settings=settings or {}
        )
        
        return {
            "workflow": workflow,
            "type": "inpainting",
            "settings": settings or {}
        }
    
    def outpainting(
        self,
        image_path: str,
        direction: str = "all",  # "all", "left", "right", "top", "bottom"
        extension_size: int = 512,
        prompt: str = "",
        negative_prompt: str = "",
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Extend image boundaries (outpainting)
        
        Args:
            image_path: Path to input image
            direction: Direction to extend
            extension_size: Size of extension in pixels
            prompt: Outpainting prompt
            negative_prompt: Negative prompt
            settings: Generation settings
        
        Returns:
            Dict with workflow and configuration
        """
        # Load image
        image = Image.open(image_path)
        image_base64 = self._image_to_base64(image)
        
        # Create mask for outpainting area
        mask = self._create_outpainting_mask(image, direction, extension_size)
        mask_base64 = self._image_to_base64(mask)
        
        # Build outpainting workflow
        workflow = self.workflow_manager.build_outpainting_workflow(
            image_base64=image_base64,
            mask_base64=mask_base64,
            prompt=prompt,
            negative_prompt=negative_prompt,
            settings=settings or {}
        )
        
        return {
            "workflow": workflow,
            "type": "outpainting",
            "direction": direction,
            "extension_size": extension_size,
            "settings": settings or {}
        }
    
    def image_to_image(
        self,
        image_path: str,
        prompt: str = "",
        negative_prompt: str = "",
        strength: float = 0.75,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Transform image using img2img
        
        Args:
            image_path: Path to input image
            prompt: Transformation prompt
            negative_prompt: Negative prompt
            strength: Transformation strength (0.0-1.0)
            settings: Generation settings
        
        Returns:
            Dict with workflow and configuration
        """
        # Load image
        image = Image.open(image_path)
        image_base64 = self._image_to_base64(image)
        
        # Build img2img workflow
        workflow = self.workflow_manager.build_img2img_workflow(
            image_base64=image_base64,
            prompt=prompt,
            negative_prompt=negative_prompt,
            strength=strength,
            settings=settings or {}
        )
        
        return {
            "workflow": workflow,
            "type": "image_to_image",
            "strength": strength,
            "settings": settings or {}
        }
    
    def controlnet_generation(
        self,
        control_image_path: str,
        control_type: str = "pose",  # "pose", "depth", "canny", "openpose", "seg"
        prompt: str = "",
        negative_prompt: str = "",
        control_strength: float = 1.0,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate using ControlNet
        
        Args:
            control_image_path: Path to control image (pose, depth map, etc.)
            control_type: Type of control (pose, depth, canny, etc.)
            prompt: Generation prompt
            negative_prompt: Negative prompt
            control_strength: ControlNet strength (0.0-2.0)
            settings: Generation settings
        
        Returns:
            Dict with workflow and configuration
        """
        # Load control image
        control_image = Image.open(control_image_path)
        control_base64 = self._image_to_base64(control_image)
        
        # Build ControlNet workflow
        workflow = self.workflow_manager.build_controlnet_workflow(
            control_image_base64=control_base64,
            control_type=control_type,
            prompt=prompt,
            negative_prompt=negative_prompt,
            control_strength=control_strength,
            settings=settings or {}
        )
        
        return {
            "workflow": workflow,
            "type": "controlnet",
            "control_type": control_type,
            "control_strength": control_strength,
            "settings": settings or {}
        }
    
    def style_transfer(
        self,
        content_image_path: str,
        style_image_path: str,
        strength: float = 0.5,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Apply style transfer
        
        Args:
            content_image_path: Path to content image
            style_image_path: Path to style reference image
            strength: Style transfer strength (0.0-1.0)
            settings: Generation settings
        
        Returns:
            Dict with workflow and configuration
        """
        # Load images
        content_image = Image.open(content_image_path)
        style_image = Image.open(style_image_path)
        
        content_base64 = self._image_to_base64(content_image)
        style_base64 = self._image_to_base64(style_image)
        
        # Build style transfer workflow
        workflow = self.workflow_manager.build_style_transfer_workflow(
            content_image_base64=content_base64,
            style_image_base64=style_base64,
            strength=strength,
            settings=settings or {}
        )
        
        return {
            "workflow": workflow,
            "type": "style_transfer",
            "strength": strength,
            "settings": settings or {}
        }
    
    def background_replacement(
        self,
        image_path: str,
        new_background_prompt: str = "",
        remove_background: bool = True,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Replace background using AI
        
        Args:
            image_path: Path to input image
            new_background_prompt: Prompt for new background
            remove_background: Whether to remove existing background first
            settings: Generation settings
        
        Returns:
            Dict with workflow and configuration
        """
        # Load image
        image = Image.open(image_path)
        image_base64 = self._image_to_base64(image)
        
        # Build background replacement workflow
        workflow = self.workflow_manager.build_background_replacement_workflow(
            image_base64=image_base64,
            new_background_prompt=new_background_prompt,
            remove_background=remove_background,
            settings=settings or {}
        )
        
        return {
            "workflow": workflow,
            "type": "background_replacement",
            "settings": settings or {}
        }
    
    def object_removal(
        self,
        image_path: str,
        object_mask_path: Optional[str] = None,
        object_mask_data: Optional[bytes] = None,
        prompt: str = "",
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Remove objects from image (uses inpainting)
        
        Args:
            image_path: Path to input image
            object_mask_path: Path to mask of object to remove
            object_mask_data: Mask as bytes
            prompt: Inpainting prompt for background
            settings: Generation settings
        
        Returns:
            Dict with workflow and configuration
        """
        return self.inpainting(
            image_path=image_path,
            mask_path=object_mask_path,
            mask_data=object_mask_data,
            prompt=prompt or "clean background, seamless",
            settings=settings
        )
    
    def object_addition(
        self,
        image_path: str,
        object_prompt: str,
        position: Optional[Tuple[int, int]] = None,
        mask_path: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add objects to image
        
        Args:
            image_path: Path to input image
            object_prompt: Description of object to add
            position: Position to add object (x, y)
            mask_path: Optional mask for where to add object
            settings: Generation settings
        
        Returns:
            Dict with workflow and configuration
        """
        # Load image
        image = Image.open(image_path)
        image_base64 = self._image_to_base64(image)
        
        # Create or load mask
        if mask_path:
            mask = Image.open(mask_path)
        elif position:
            # Create mask at position
            mask = self._create_position_mask(image, position)
        else:
            raise ValueError("Either position or mask_path must be provided")
        
        mask_base64 = self._image_to_base64(mask)
        
        # Build object addition workflow (inpainting with object prompt)
        workflow = self.workflow_manager.build_inpainting_workflow(
            image_base64=image_base64,
            mask_base64=mask_base64,
            prompt=object_prompt,
            negative_prompt="blurry, distorted, low quality",
            settings=settings or {}
        )
        
        return {
            "workflow": workflow,
            "type": "object_addition",
            "settings": settings or {}
        }
    
    def face_swap(
        self,
        source_image_path: str,
        target_image_path: str,
        face_index: int = 0,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Swap faces between images
        
        Args:
            source_image_path: Image with face to use
            target_image_path: Image to replace face in
            face_index: Which face to swap (if multiple)
            settings: Generation settings
        
        Returns:
            Dict with workflow and configuration
        """
        # Load images
        source_image = Image.open(source_image_path)
        target_image = Image.open(target_image_path)
        
        source_base64 = self._image_to_base64(source_image)
        target_base64 = self._image_to_base64(target_image)
        
        # Build face swap workflow
        workflow = self.workflow_manager.build_face_swap_workflow(
            source_image_base64=source_base64,
            target_image_base64=target_base64,
            face_index=face_index,
            settings=settings or {}
        )
        
        return {
            "workflow": workflow,
            "type": "face_swap",
            "face_index": face_index,
            "settings": settings or {}
        }
    
    def age_transformation(
        self,
        image_path: str,
        target_age: str = "younger",  # "younger", "older", or specific age
        strength: float = 0.5,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Transform age appearance
        
        Args:
            image_path: Path to input image
            target_age: Target age ("younger", "older", or age number)
            strength: Transformation strength
            settings: Generation settings
        
        Returns:
            Dict with workflow and configuration
        """
        # Build age transformation prompt
        if target_age == "younger":
            age_prompt = "younger appearance, youthful skin, smooth face"
        elif target_age == "older":
            age_prompt = "older appearance, mature features, aged skin"
        else:
            age_prompt = f"age {target_age} appearance"
        
        # Use img2img with age-specific prompt
        return self.image_to_image(
            image_path=image_path,
            prompt=age_prompt,
            strength=strength,
            settings=settings
        )
    
    def gender_transformation(
        self,
        image_path: str,
        target_gender: str = "opposite",  # "opposite", "male", "female"
        strength: float = 0.5,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Transform gender appearance
        
        Args:
            image_path: Path to input image
            target_gender: Target gender
            strength: Transformation strength
            settings: Generation settings
        
        Returns:
            Dict with workflow and configuration
        """
        # Build gender transformation prompt
        if target_gender == "male":
            gender_prompt = "male appearance, masculine features"
        elif target_gender == "female":
            gender_prompt = "female appearance, feminine features"
        else:
            gender_prompt = "opposite gender appearance"
        
        return self.image_to_image(
            image_path=image_path,
            prompt=gender_prompt,
            strength=strength,
            settings=settings
        )
    
    def body_type_modification(
        self,
        image_path: str,
        modification: str = "slimmer",  # "slimmer", "muscular", "curvier", etc.
        strength: float = 0.5,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Modify body type proportions
        
        Args:
            image_path: Path to input image
            modification: Type of modification
            strength: Modification strength
            settings: Generation settings
        
        Returns:
            Dict with workflow and configuration
        """
        # Build body modification prompt
        modification_prompts = {
            "slimmer": "slimmer body, athletic build",
            "muscular": "muscular build, toned body",
            "curvier": "curvier body, fuller figure",
            "taller": "taller appearance, longer legs",
            "shorter": "shorter appearance, proportional"
        }
        
        prompt = modification_prompts.get(modification, f"{modification} body type")
        
        return self.image_to_image(
            image_path=image_path,
            prompt=prompt,
            strength=strength,
            settings=settings
        )
    
    def object_addition(
        self,
        image_path: str,
        object_prompt: str,
        position: Optional[Tuple[int, int]] = None,
        size: Optional[Tuple[int, int]] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add objects to images
        
        Args:
            image_path: Path to input image
            object_prompt: Description of object to add
            position: Optional position (x, y)
            size: Optional size (width, height)
            settings: Generation settings
        
        Returns:
            Dict with workflow and configuration
        """
        # Load image
        image = Image.open(image_path)
        
        # Create mask for object addition area
        if position and size:
            mask = self._create_position_mask(image, position, size)
        else:
            # Default: center of image
            center_x = image.width // 2
            center_y = image.height // 2
            default_size = (256, 256)
            mask = self._create_position_mask(image, (center_x - 128, center_y - 128), default_size)
        
        mask_base64 = self._image_to_base64(mask)
        image_base64 = self._image_to_base64(image)
        
        # Use inpainting to add object
        workflow = self.workflow_manager.build_inpainting_workflow(
            image_base64=image_base64,
            mask_base64=mask_base64,
            prompt=object_prompt,
            negative_prompt="blurry, distorted, low quality",
            settings=settings or {}
        )
        
        return {
            "workflow": workflow,
            "type": "object_addition",
            "object_prompt": object_prompt,
            "settings": settings or {}
        }
    
    # Helper methods
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()
        return base64.b64encode(img_bytes).decode("utf-8")
    
    def _create_outpainting_mask(
        self,
        image: Image.Image,
        direction: str,
        extension_size: int
    ) -> Image.Image:
        """Create mask for outpainting"""
        width, height = image.size
        mask = Image.new("L", (width + extension_size * 2, height + extension_size * 2), 0)
        
        if direction == "all":
            # Mask entire border
            mask.paste(255, (0, 0, mask.width, extension_size))  # Top
            mask.paste(255, (0, mask.height - extension_size, mask.width, mask.height))  # Bottom
            mask.paste(255, (0, 0, extension_size, mask.height))  # Left
            mask.paste(255, (mask.width - extension_size, 0, mask.width, mask.height))  # Right
        elif direction == "left":
            mask.paste(255, (0, 0, extension_size, mask.height))
        elif direction == "right":
            mask.paste(255, (mask.width - extension_size, 0, mask.width, mask.height))
        elif direction == "top":
            mask.paste(255, (0, 0, mask.width, extension_size))
        elif direction == "bottom":
            mask.paste(255, (0, mask.height - extension_size, mask.width, mask.height))
        
        return mask
    
    def _create_position_mask(
        self,
        image: Image.Image,
        position: Tuple[int, int],
        size: Tuple[int, int] = (256, 256)
    ) -> Image.Image:
        """Create mask at specific position"""
        mask = Image.new("L", image.size, 0)
        x, y = position
        w, h = size
        
        # Ensure position is within bounds
        x = max(0, min(x, image.width - w))
        y = max(0, min(y, image.height - h))
        
        # Create white rectangle at position
        mask_rect = Image.new("L", (w, h), 255)
        mask.paste(mask_rect, (x, y))
        
        return mask
