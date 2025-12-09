"""
Prompt Engineering Service
Handles advanced prompt generation, optimization, and templates
Based on docs/20-ADVANCED-PROMPT-ENGINEERING.md
"""
import logging
from enum import Enum
from typing import Dict, Optional, Any, List, Union
from models import Character

logger = logging.getLogger(__name__)


class Platform(Enum):
    INSTAGRAM = "instagram"
    ONLYFANS = "onlyfans"
    TWITTER = "twitter"
    YOUTUBE = "youtube"

    @classmethod
    def from_value(cls, value: Optional[str]) -> "Platform":
        """Best-effort conversion from string to Platform enum."""
        if not value:
            return cls.INSTAGRAM
        try:
            return cls(value.lower())
        except ValueError:
            return cls.INSTAGRAM


class PromptEngineeringService:
    """Service for advanced prompt engineering"""
    
    # Quality modifiers
    QUALITY_MODIFIERS = [
        "8k uhd", "highly detailed", "sharp focus", "professional quality",
        "photorealistic", "ultra-realistic", "perfect anatomy", "flawless skin",
        "natural skin texture", "realistic lighting", "accurate proportions",
        "professional photography", "masterful", "best quality", "award winning"
    ]
    
    # Standard negative prompt
    STANDARD_NEGATIVE_PROMPT = (
        "low quality, worst quality, normal quality, lowres, low details, "
        "oversaturated, undersaturated, bad anatomy, bad proportions, "
        "blurry, disfigured, deformed, ugly, mutated, "
        "extra limbs, missing limbs, floating limbs, disconnected limbs, "
        "malformed hands, out of focus, long neck, long body, "
        "monochrome, grayscale, sepia, watermark, signature, text, logo, "
        "cartoon, anime, painting, drawing, 3d render, cgi, computer graphics, "
        "unrealistic, fake, artificial, ai generated, ai art, synthetic, "
        "extra fingers, missing fingers, too many fingers, wrong number of fingers, "
        "distorted face, asymmetrical face, blurry face, pixelated, "
        "artifacts, compression artifacts, jpeg artifacts, noise, grain"
    )
    
    # Platform-specific negative prompts
    PLATFORM_NEGATIVE_PROMPTS = {
        "instagram": (
            "nudity, explicit content, inappropriate, "
            "nsfw, adult content, revealing clothing"
        ),
        "onlyfans": (
            "cartoon, anime, unrealistic proportions, "
            "exaggerated features, fake appearance"
        ),
        "twitter": "",
        "youtube": ""
    }
    
    def __init__(self):
        pass
    
    def build_prompt(
        self,
        character: Optional[Character] = None,
        subject_description: Optional[str] = None,
        appearance_details: Optional[str] = None,
        pose_action: Optional[str] = None,
        setting_environment: Optional[str] = None,
        style_modifiers: Optional[List[str]] = None,
        quality_modifiers: Optional[List[str]] = None,
        platform: Union[str, Platform] = Platform.INSTAGRAM
    ) -> str:
        """Build a complete prompt from components"""
        components = []
        
        # Subject description (from character or provided)
        if character:
            components.append(self._get_character_description(character))
        elif subject_description:
            components.append(subject_description)
        
        # Appearance details
        if appearance_details:
            components.append(appearance_details)
        
        # Pose/Action
        if pose_action:
            components.append(pose_action)
        
        # Setting/Environment
        if setting_environment:
            components.append(setting_environment)
        
        # Style modifiers
        if style_modifiers:
            components.extend(style_modifiers)
        else:
            components.append("professional photography")
        
        # Quality modifiers
        if quality_modifiers:
            components.extend(quality_modifiers)
        else:
            components.extend(self.QUALITY_MODIFIERS[:5])  # Top 5
        
        return ", ".join(components)
    
    def build_negative_prompt(
        self,
        platform: Union[str, Platform] = Platform.INSTAGRAM,
        additional_negatives: Optional[List[str]] = None
    ) -> str:
        """Build negative prompt for platform"""
        negatives = [self.STANDARD_NEGATIVE_PROMPT]
        
        # Add platform-specific negatives
        platform_key = (
            platform.value if isinstance(platform, Platform) else (platform or "instagram").lower()
        )
        if platform_key in self.PLATFORM_NEGATIVE_PROMPTS:
            platform_neg = self.PLATFORM_NEGATIVE_PROMPTS[platform_key]
            if platform_neg:
                negatives.append(platform_neg)
        
        # Add additional negatives
        if additional_negatives:
            negatives.append(", ".join(additional_negatives))
        
        return ", ".join(negatives)
    
    def optimize_prompt(
        self,
        prompt: str,
        emphasis_words: Optional[List[str]] = None,
        deemphasis_words: Optional[List[str]] = None
    ) -> str:
        """Optimize prompt with weighting"""
        words = prompt.split(", ")
        
        # Apply emphasis
        if emphasis_words:
            for i, word in enumerate(words):
                if any(ew in word.lower() for ew in emphasis_words):
                    words[i] = f"(({word}))"  # Moderate emphasis
        
        # Apply deemphasis
        if deemphasis_words:
            for i, word in enumerate(words):
                if any(dw in word.lower() for dw in deemphasis_words):
                    words[i] = f"[{word}]"  # De-emphasis
        
        return ", ".join(words)
    
    def get_platform_prompt_template(self, platform: Union[str, Platform]) -> Dict[str, Any]:
        """Get platform-specific prompt template"""
        platform_key = (
            platform.value if isinstance(platform, Platform) else (platform or "instagram").lower()
        )
        templates = {
            "instagram": {
                "style": "professional fashion photography, Instagram aesthetic",
                "lighting": "soft natural lighting, warm color grading",
                "composition": "shallow depth of field, bokeh background",
                "quality": "8k uhd, highly detailed, sharp focus, photorealistic"
            },
            "onlyfans": {
                "style": "professional boudoir photography, artistic and tasteful",
                "lighting": "soft romantic lighting, warm golden tones",
                "composition": "shallow depth of field, elegant composition",
                "quality": "8k uhd, highly detailed, sharp focus, photorealistic"
            },
            "twitter": {
                "style": "lifestyle photography, authentic, natural",
                "lighting": "casual lighting, natural colors",
                "composition": "natural composition",
                "quality": "8k uhd, highly detailed, sharp focus, photorealistic"
            },
            "youtube": {
                "style": "high contrast lighting, vibrant colors",
                "lighting": "high contrast lighting",
                "composition": "clear subject, centered composition",
                "quality": "8k uhd, highly detailed, sharp focus, photorealistic"
            }
        }
        
        return templates.get(platform_key, templates["instagram"])
    
    def _get_character_description(self, character: Character) -> str:
        """Get character description for prompt"""
        desc = character.description or ""
        
        # If character has settings with appearance, use them
        if character.settings:
            appearance = character.settings.get("appearance", {})
            if appearance:
                parts = []
                if appearance.get("age"):
                    parts.append(f"{appearance['age']}-year-old")
                if appearance.get("gender"):
                    parts.append(appearance["gender"])
                if appearance.get("build"):
                    parts.append(appearance["build"])
                if appearance.get("height"):
                    parts.append(appearance["height"])
                
                if parts:
                    desc = ", ".join(parts) + ". " + desc
        
        return desc
    
    def generate_prompt_variations(
        self,
        base_prompt: str,
        count: int = 5,
        variation_type: str = "setting"
    ) -> List[str]:
        """Generate prompt variations"""
        variations = []
        
        settings = [
            "modern coffee shop setting",
            "beautiful park setting",
            "elegant bedroom setting",
            "professional studio setting",
            "outdoor natural setting",
            "urban street setting",
            "luxury hotel setting",
            "beach setting",
            "mountain setting",
            "city rooftop setting"
        ]
        
        poses = [
            "standing pose, natural smile, looking at camera",
            "sitting pose, relaxed expression, looking away",
            "walking pose, confident stride, natural movement",
            "leaning pose, casual expression, looking at camera",
            "laying pose, relaxed expression, natural position"
        ]
        
        for i in range(count):
            if variation_type == "setting":
                setting = settings[i % len(settings)]
                var_prompt = base_prompt.replace(
                    "setting", setting
                ) if "setting" in base_prompt else f"{base_prompt}, {setting}"
            elif variation_type == "pose":
                pose = poses[i % len(poses)]
                var_prompt = f"{base_prompt}, {pose}"
            else:
                var_prompt = base_prompt
            
            variations.append(var_prompt)
        
        return variations
