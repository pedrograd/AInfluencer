"""
Workflow Manager
Builds ComfyUI workflows for image and video generation
"""
import json
from pathlib import Path
from typing import Dict, Optional, Any
from models import Character

class WorkflowManager:
    """Manages ComfyUI workflow generation"""
    
    def __init__(self, workflow_base_path: Optional[Path] = None):
        if workflow_base_path is None:
            workflow_base_path = Path(__file__).parent.parent.parent / "comfyui_workflow_base.json"
        self.workflow_base_path = workflow_base_path
        self.base_workflow = self._load_base_workflow()
    
    def _load_base_workflow(self) -> Dict[str, Any]:
        """Load base workflow template"""
        if self.workflow_base_path.exists():
            with open(self.workflow_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def build_image_workflow(
        self,
        prompt: str,
        negative_prompt: str = "",
        settings: Optional[Dict[str, Any]] = None,
        character: Optional[Character] = None,
        face_consistency: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build image generation workflow"""
        # Start with base workflow
        workflow = json.loads(json.dumps(self.base_workflow))  # Deep copy
        
        settings = settings or {}
        
        # Find and update prompt nodes
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict):
                class_type = node_data.get("class_type", "")
                
                # Update positive prompt
                if class_type == "CLIPTextEncode":
                    inputs = node_data.get("inputs", {})
                    text = inputs.get("text", "")
                    # Check if it's negative prompt (contains keywords)
                    if any(word in text.lower() for word in ['low quality', 'worst quality', 'bad anatomy']):
                        if negative_prompt:
                            node_data["inputs"]["text"] = negative_prompt
                    else:
                        node_data["inputs"]["text"] = prompt
                
                # Update sampler settings
                elif class_type == "KSampler":
                    inputs = node_data.get("inputs", {})
                    if "seed" in settings:
                        seed = settings["seed"]
                        if seed == -1:
                            import random
                            seed = random.randint(0, 2**32 - 1)
                        inputs["seed"] = seed
                    if "steps" in settings:
                        inputs["steps"] = settings["steps"]
                    if "cfg_scale" in settings:
                        inputs["cfg_scale"] = settings["cfg_scale"]
                    if "sampler_name" in settings:
                        inputs["sampler_name"] = settings["sampler_name"]
                
                # Update checkpoint
                elif class_type == "CheckpointLoaderSimple":
                    if "model" in settings:
                        inputs = node_data.get("inputs", {})
                        inputs["ckpt_name"] = settings["model"]
        
        # Add face consistency if enabled
        if face_consistency and face_consistency.get("enabled") and character:
            workflow = self._add_face_consistency(workflow, character, face_consistency)
        
        return workflow
    
    def build_video_workflow(
        self,
        prompt: str,
        negative_prompt: str = "",
        settings: Optional[Dict[str, Any]] = None,
        character: Optional[Character] = None,
        source_image: Optional[Any] = None,
        face_consistency: Optional[Dict[str, Any]] = None,
        method: str = "animatediff"
    ) -> Dict[str, Any]:
        """
        Build video generation workflow
        
        This method is now primarily handled by VideoGenerationService,
        but kept for backward compatibility and basic workflows.
        """
        settings = settings or {}
        
        # For basic video workflows, start with image workflow
        workflow = self.build_image_workflow(
            prompt=prompt,
            negative_prompt=negative_prompt,
            settings=settings,
            character=character,
            face_consistency=face_consistency
        )
        
        # Video-specific modifications would be added here
        # But actual video workflows are built by VideoGenerationService
        
        return workflow
    
    def _add_face_consistency(
        self,
        workflow: Dict[str, Any],
        character: Character,
        face_consistency: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add face consistency nodes to workflow"""
        # This is now handled by FaceConsistencyService
        # Keep this method for backward compatibility but delegate to service
        return workflow
    
    def build_inpainting_workflow(
        self,
        image_base64: str,
        mask_base64: str,
        prompt: str,
        negative_prompt: str = "",
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build inpainting workflow"""
        workflow = self.build_image_workflow(
            prompt=prompt,
            negative_prompt=negative_prompt,
            settings=settings or {}
        )
        
        # Add image and mask loading nodes
        # This is a simplified version - actual implementation would add proper ComfyUI nodes
        workflow["_inpainting"] = {
            "image_base64": image_base64,
            "mask_base64": mask_base64,
            "type": "inpainting"
        }
        
        return workflow
    
    def build_outpainting_workflow(
        self,
        image_base64: str,
        mask_base64: str,
        prompt: str,
        negative_prompt: str = "",
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build outpainting workflow"""
        # Similar to inpainting but with different mask
        return self.build_inpainting_workflow(
            image_base64=image_base64,
            mask_base64=mask_base64,
            prompt=prompt,
            negative_prompt=negative_prompt,
            settings=settings
        )
    
    def build_img2img_workflow(
        self,
        image_base64: str,
        prompt: str,
        negative_prompt: str = "",
        strength: float = 0.75,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build image-to-image workflow"""
        workflow = self.build_image_workflow(
            prompt=prompt,
            negative_prompt=negative_prompt,
            settings=settings or {}
        )
        
        # Add img2img configuration
        workflow["_img2img"] = {
            "image_base64": image_base64,
            "strength": strength,
            "type": "img2img"
        }
        
        return workflow
    
    def build_controlnet_workflow(
        self,
        control_image_base64: str,
        control_type: str,
        prompt: str,
        negative_prompt: str = "",
        control_strength: float = 1.0,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build ControlNet workflow"""
        workflow = self.build_image_workflow(
            prompt=prompt,
            negative_prompt=negative_prompt,
            settings=settings or {}
        )
        
        # Add ControlNet configuration
        workflow["_controlnet"] = {
            "control_image_base64": control_image_base64,
            "control_type": control_type,
            "control_strength": control_strength,
            "type": "controlnet"
        }
        
        return workflow
    
    def build_style_transfer_workflow(
        self,
        content_image_base64: str,
        style_image_base64: str,
        strength: float = 0.5,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build style transfer workflow"""
        workflow = self.build_image_workflow(
            prompt="style transfer",
            negative_prompt="",
            settings=settings or {}
        )
        
        # Add style transfer configuration
        workflow["_style_transfer"] = {
            "content_image_base64": content_image_base64,
            "style_image_base64": style_image_base64,
            "strength": strength,
            "type": "style_transfer"
        }
        
        return workflow
    
    def build_background_replacement_workflow(
        self,
        image_base64: str,
        new_background_prompt: str,
        remove_background: bool = True,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build background replacement workflow"""
        prompt = f"{new_background_prompt}, professional background"
        workflow = self.build_image_workflow(
            prompt=prompt,
            negative_prompt="person, subject, foreground",
            settings=settings or {}
        )
        
        # Add background replacement configuration
        workflow["_background_replacement"] = {
            "image_base64": image_base64,
            "remove_background": remove_background,
            "type": "background_replacement"
        }
        
        return workflow
    
    def build_face_swap_workflow(
        self,
        source_image_base64: str,
        target_image_base64: str,
        face_index: int = 0,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build face swap workflow"""
        workflow = self.build_image_workflow(
            prompt="face swap",
            negative_prompt="",
            settings=settings or {}
        )
        
        # Add face swap configuration
        workflow["_face_swap"] = {
            "source_image_base64": source_image_base64,
            "target_image_base64": target_image_base64,
            "face_index": face_index,
            "type": "face_swap"
        }
        
        return workflow
