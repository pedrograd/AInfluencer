"""
Prompt Engineering Service
Handles advanced prompt generation, optimization, and template management
"""
import logging
from typing import Dict, Optional, Any, List
from pathlib import Path
import json
import random

logger = logging.getLogger(__name__)

class PromptService:
    """Service for prompt engineering and optimization"""
    
    def __init__(self):
        self.templates_path = Path(__file__).parent.parent / "prompt_templates"
        self.templates_path.mkdir(exist_ok=True)
        self._load_templates()
    
    def _load_templates(self):
        """Load prompt templates"""
        self.templates = {
            "character": self._get_character_template(),
            "instagram": self._get_instagram_template(),
            "onlyfans": self._get_onlyfans_template(),
            "portrait": self._get_portrait_template(),
            "lifestyle": self._get_lifestyle_template()
        }
    
    def build_prompt(
        self,
        character_description: Optional[str] = None,
        pose: Optional[str] = None,
        setting: Optional[str] = None,
        style: Optional[str] = None,
        platform: Optional[str] = None,
        quality_modifiers: Optional[List[str]] = None
    ) -> str:
        """Build optimized prompt from components"""
        components = []
        
        # 1. Character description
        if character_description:
            components.append(character_description)
        else:
            components.append("A 25-year-old woman, athletic build")
        
        # 2. Pose/Action
        if pose:
            components.append(pose)
        else:
            components.append("standing pose, natural smile, looking at camera")
        
        # 3. Setting/Environment
        if setting:
            components.append(setting)
        else:
            components.append("modern setting, soft natural lighting")
        
        # 4. Style modifiers
        if style:
            components.append(style)
        else:
            components.append("professional photography")
        
        # 5. Quality modifiers
        if quality_modifiers:
            components.extend(quality_modifiers)
        else:
            components.extend(self._get_default_quality_modifiers())
        
        # 6. Platform-specific modifiers
        if platform:
            platform_modifiers = self._get_platform_modifiers(platform)
            components.extend(platform_modifiers)
        
        return ", ".join(components)
    
    def build_negative_prompt(
        self,
        platform: Optional[str] = None,
        custom_terms: Optional[List[str]] = None
    ) -> str:
        """Build comprehensive negative prompt"""
        terms = []
        
        # Standard negative terms
        terms.extend([
            "low quality", "worst quality", "normal quality", "lowres", "low details",
            "oversaturated", "undersaturated", "bad anatomy", "bad proportions",
            "blurry", "disfigured", "deformed", "ugly", "mutated",
            "extra limbs", "missing limbs", "floating limbs", "disconnected limbs",
            "malformed hands", "out of focus", "long neck", "long body",
            "monochrome", "grayscale", "sepia", "watermark", "signature", "text", "logo",
            "cartoon", "anime", "painting", "drawing", "3d render", "cgi", "computer graphics",
            "unrealistic", "fake", "artificial", "ai generated", "ai art", "synthetic",
            "extra fingers", "missing fingers", "too many fingers", "wrong number of fingers",
            "distorted face", "asymmetrical face", "blurry face", "pixelated",
            "artifacts", "compression artifacts", "jpeg artifacts", "noise", "grain"
        ])
        
        # Platform-specific terms
        if platform == "instagram":
            terms.extend([
                "nudity", "explicit content", "inappropriate", "nsfw", "adult content"
            ])
        elif platform == "onlyfans":
            terms.extend([
                "exaggerated proportions", "fake appearance"
            ])
        
        # Custom terms
        if custom_terms:
            terms.extend(custom_terms)
        
        return ", ".join(terms)
    
    def optimize_prompt(
        self,
        prompt: str,
        target_quality: str = "high"
    ) -> str:
        """Optimize existing prompt"""
        # Add quality modifiers if missing
        quality_keywords = [
            "highly detailed", "sharp focus", "photorealistic", "ultra-realistic"
        ]
        
        has_quality = any(keyword in prompt.lower() for keyword in quality_keywords)
        if not has_quality:
            prompt += ", " + ", ".join(self._get_default_quality_modifiers())
        
        # Ensure proper ordering (subject first, quality last)
        # This is a simplified version - full optimization would parse and reorder
        
        return prompt
    
    def apply_weighting(
        self,
        prompt: str,
        weights: Dict[str, float]
    ) -> str:
        """Apply attention weighting to prompt"""
        # Simple weighting implementation
        # Format: (word:weight) or ((word)) for emphasis
        weighted_prompt = prompt
        
        for word, weight in weights.items():
            if word in weighted_prompt:
                if weight > 1.0:
                    # Add emphasis
                    emphasis_level = int(weight)
                    weighted_word = "(" * emphasis_level + word + ")" * emphasis_level
                    weighted_prompt = weighted_prompt.replace(word, weighted_word)
                elif weight < 1.0:
                    # Add de-emphasis
                    weighted_word = f"[{word}]"
                    weighted_prompt = weighted_prompt.replace(word, weighted_word)
        
        return weighted_prompt
    
    def generate_variations(
        self,
        base_prompt: str,
        count: int = 5
    ) -> List[str]:
        """Generate prompt variations"""
        variations = []
        
        # Variation strategies
        poses = [
            "standing pose, natural smile",
            "sitting pose, relaxed expression",
            "walking pose, confident stride",
            "casual pose, looking away",
            "professional pose, direct gaze"
        ]
        
        settings = [
            "modern coffee shop, natural lighting",
            "outdoor park setting, golden hour",
            "studio setting, professional lighting",
            "indoor setting, soft window light",
            "urban setting, street photography style"
        ]
        
        for i in range(count):
            # Extract base components
            base = base_prompt
            
            # Replace pose if present
            for pose in poses:
                if pose in base.lower():
                    base = base.replace(pose, random.choice(poses))
                    break
            
            # Replace setting if present
            for setting in settings:
                if any(word in base.lower() for word in setting.split(", ")):
                    base = base.replace(setting, random.choice(settings))
                    break
            
            variations.append(base)
        
        return variations
    
    def _get_default_quality_modifiers(self) -> List[str]:
        """Get default quality modifiers"""
        return [
            "8k uhd", "highly detailed", "sharp focus", "professional quality",
            "photorealistic", "ultra-realistic", "perfect anatomy", "flawless skin",
            "natural skin texture", "realistic lighting", "accurate proportions"
        ]
    
    def _get_platform_modifiers(self, platform: str) -> List[str]:
        """Get platform-specific modifiers"""
        modifiers = {
            "instagram": [
                "Instagram aesthetic", "high-end lifestyle content", "aspirational",
                "fashion photography", "trendy"
            ],
            "onlyfans": [
                "professional boudoir photography", "artistic", "tasteful",
                "intimate but elegant"
            ],
            "twitter": [
                "lifestyle photography", "authentic", "natural", "casual"
            ],
            "youtube": [
                "high contrast lighting", "vibrant colors", "clear subject"
            ]
        }
        
        return modifiers.get(platform.lower(), [])
    
    def _get_character_template(self) -> str:
        """Get character description template"""
        return """A {age}-year-old {gender}, {build}, {height}. 
{face_description: eyes, nose, lips, jawline, cheekbones}. 
{hair_description: color, length, style, texture}. 
{skin_description: tone, texture, quality}. 
{distinguishing_features}."""
    
    def _get_instagram_template(self) -> str:
        """Get Instagram prompt template"""
        return """{character_description}, {stylish_outfit}, {trendy_setting}, 
professional fashion photography, Instagram aesthetic, 
high-end lifestyle content, aspirational, 
soft natural lighting, warm color grading, 
shallow depth of field, bokeh background, 
8k uhd, highly detailed, sharp focus, 
photorealistic, ultra-realistic"""
    
    def _get_onlyfans_template(self) -> str:
        """Get OnlyFans prompt template"""
        return """{character_description}, {intimate_setting}, 
professional boudoir photography, artistic, tasteful, 
soft romantic lighting, warm color grading, 
shallow depth of field, elegant composition, 
8k uhd, highly detailed, sharp focus, 
photorealistic, ultra-realistic, perfect anatomy"""
    
    def _get_portrait_template(self) -> str:
        """Get portrait prompt template"""
        return """{character_description}, 
professional portrait photography, fashion photography aesthetic, 
modern minimalist studio setting, soft diffused lighting, 
warm color grading, shallow depth of field, bokeh background, 
DSLR camera, 85mm lens, 8k uhd, highly detailed, 
sharp focus, photorealistic, ultra-realistic"""
    
    def _get_lifestyle_template(self) -> str:
        """Get lifestyle prompt template"""
        return """{character_description}, {casual_setting}, 
lifestyle photography, authentic natural feel, 
golden hour lighting, soft warm sunlight, 
natural outdoor setting, shallow depth of field, 
beautiful bokeh, professional photography, 
DSLR camera, 8k uhd, highly detailed, 
sharp focus, photorealistic, ultra-realistic"""
