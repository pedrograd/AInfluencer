"""NSFW (+18) content generation service with enhanced prompt engineering and safety features."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class NSFWContentConfig:
    """Configuration for NSFW content generation.
    
    Attributes:
        use_nsfw_checkpoint: Whether to use NSFW-optimized checkpoint (default: True).
        nsfw_checkpoint: Preferred checkpoint for NSFW content (optional).
        enhanced_prompt_modifiers: Additional prompt modifiers for NSFW content.
        quality_controls: Quality control negative prompts for NSFW content.
        safety_checks: Whether to perform safety validation (default: True).
    """
    use_nsfw_checkpoint: bool = True
    nsfw_checkpoint: str | None = None
    enhanced_prompt_modifiers: list[str] | None = None
    quality_controls: list[str] | None = None
    safety_checks: bool = True


class NSFWContentService:
    """Service for generating +18/NSFW content with enhanced prompt engineering and safety features.
    
    This service provides specialized handling for adult content generation including:
    - Enhanced prompt engineering for NSFW content
    - NSFW-optimized checkpoint selection
    - Quality controls specific to adult content
    - Safety validation and content warnings
    """
    
    # Default NSFW prompt modifiers for enhanced quality
    DEFAULT_NSFW_MODIFIERS = [
        "high quality",
        "detailed",
        "professional photography",
        "realistic",
        "mature content",
        "explicit",
        "adult",
        "+18",
    ]
    
    # Quality controls for NSFW content (negative prompts)
    DEFAULT_QUALITY_CONTROLS = [
        "low quality",
        "distorted",
        "bad anatomy",
        "bad proportions",
        "extra limbs",
        "mutated",
        "deformed",
        "blurry",
        "artifacts",
        "watermark",
        "text overlay",
        "poor lighting",
        "oversaturated",
        "undersaturated",
    ]
    
    # NSFW-specific quality controls
    NSFW_QUALITY_CONTROLS = [
        "bad hands",
        "bad fingers",
        "extra fingers",
        "missing fingers",
        "malformed hands",
        "bad face",
        "distorted face",
        "bad body proportions",
        "unnatural pose",
        "unrealistic",
    ]
    
    def __init__(self) -> None:
        """Initialize NSFW content service."""
        pass
    
    def enhance_prompt_for_nsfw(
        self,
        base_prompt: str,
        config: NSFWContentConfig | None = None,
    ) -> str:
        """
        Enhance prompt for NSFW content generation.
        
        Args:
            base_prompt: Base generation prompt.
            config: Optional NSFW configuration (uses defaults if None).
            
        Returns:
            Enhanced prompt with NSFW modifiers.
        """
        if config is None:
            config = NSFWContentConfig()
        
        # Start with base prompt
        enhanced_parts = [base_prompt]
        
        # Add default modifiers if not overridden
        modifiers = config.enhanced_prompt_modifiers or self.DEFAULT_NSFW_MODIFIERS
        enhanced_parts.extend(modifiers)
        
        # Join with commas for natural prompt flow
        enhanced_prompt = ", ".join(enhanced_parts)
        
        logger.debug(f"Enhanced NSFW prompt: {enhanced_prompt[:200]}...")
        return enhanced_prompt
    
    def build_nsfw_negative_prompt(
        self,
        base_negative_prompt: str | None = None,
        config: NSFWContentConfig | None = None,
    ) -> str:
        """
        Build comprehensive negative prompt for NSFW content.
        
        Args:
            base_negative_prompt: Base negative prompt (optional).
            config: Optional NSFW configuration (uses defaults if None).
            
        Returns:
            Comprehensive negative prompt with quality controls.
        """
        if config is None:
            config = NSFWContentConfig()
        
        negative_parts: list[str] = []
        
        # Start with base negative prompt if provided
        if base_negative_prompt:
            negative_parts.append(base_negative_prompt)
        
        # Add default quality controls
        quality_controls = config.quality_controls or self.DEFAULT_QUALITY_CONTROLS
        negative_parts.extend(quality_controls)
        
        # Add NSFW-specific quality controls
        negative_parts.extend(self.NSFW_QUALITY_CONTROLS)
        
        # Join with commas
        final_negative_prompt = ", ".join(negative_parts)
        
        logger.debug(f"Built NSFW negative prompt: {final_negative_prompt[:200]}...")
        return final_negative_prompt
    
    def select_nsfw_checkpoint(
        self,
        available_checkpoints: list[str],
        preferred_checkpoint: str | None = None,
        config: NSFWContentConfig | None = None,
    ) -> str | None:
        """
        Select appropriate checkpoint for NSFW content generation.
        
        Args:
            available_checkpoints: List of available checkpoint names.
            preferred_checkpoint: Preferred checkpoint name (optional).
            config: Optional NSFW configuration.
            
        Returns:
            Selected checkpoint name, or None if no suitable checkpoint found.
        """
        if config is None:
            config = NSFWContentConfig()
        
        # If not using NSFW checkpoint, return None (use default)
        if not config.use_nsfw_checkpoint:
            return None
        
        # If preferred checkpoint is specified and available, use it
        if preferred_checkpoint and preferred_checkpoint in available_checkpoints:
            logger.debug(f"Using preferred NSFW checkpoint: {preferred_checkpoint}")
            return preferred_checkpoint
        
        # If config specifies a checkpoint and it's available, use it
        if config.nsfw_checkpoint and config.nsfw_checkpoint in available_checkpoints:
            logger.debug(f"Using configured NSFW checkpoint: {config.nsfw_checkpoint}")
            return config.nsfw_checkpoint
        
        # Prefer checkpoints known to work well with NSFW content
        # These are common realistic/NSFW-friendly models
        nsfw_friendly_checkpoints = [
            "realisticVisionV60B1_v60B1.safetensors",
            "realisticVisionV60_v60.safetensors",
            "realisticVisionV50_v50.safetensors",
            "dreamshaperXL_v2TurboDpmppSDE.safetensors",
            "dreamshaperXL_v21TurboDpmppSDE.safetensors",
            "juggernautXL_v9.safetensors",
            "sd_xl_base_1.0.safetensors",
        ]
        
        # Find first available NSFW-friendly checkpoint
        for checkpoint in nsfw_friendly_checkpoints:
            # Check if any available checkpoint matches (case-insensitive, partial match)
            for available in available_checkpoints:
                if checkpoint.lower() in available.lower() or available.lower() in checkpoint.lower():
                    logger.debug(f"Selected NSFW-friendly checkpoint: {available}")
                    return available
        
        # If no specific checkpoint found, return None (will use default)
        logger.debug("No specific NSFW checkpoint found, using default")
        return None
    
    def get_nsfw_generation_settings(
        self,
        base_settings: dict[str, Any] | None = None,
        config: NSFWContentConfig | None = None,
    ) -> dict[str, Any]:
        """
        Get optimized generation settings for NSFW content.
        
        Args:
            base_settings: Base generation settings (optional).
            config: Optional NSFW configuration.
            
        Returns:
            Dictionary with optimized settings for NSFW content generation.
        """
        if config is None:
            config = NSFWContentConfig()
        
        # Start with base settings or defaults
        settings: dict[str, Any] = base_settings.copy() if base_settings else {}
        
        # Optimize settings for NSFW content quality
        # Higher steps for better quality
        if "steps" not in settings or settings.get("steps", 25) < 30:
            settings["steps"] = max(settings.get("steps", 25), 30)
        
        # Higher CFG for better prompt adherence
        if "cfg" not in settings or settings.get("cfg", 7.0) < 7.5:
            settings["cfg"] = max(settings.get("cfg", 7.0), 7.5)
        
        # Prefer quality samplers
        if "sampler_name" not in settings:
            settings["sampler_name"] = "dpmpp_2m"  # Better quality than euler
        
        # Prefer Karras scheduler for better quality
        if "scheduler" not in settings:
            settings["scheduler"] = "karras"
        
        logger.debug(f"NSFW generation settings: {settings}")
        return settings
    
    def validate_nsfw_content_safety(
        self,
        prompt: str,
        config: NSFWContentConfig | None = None,
    ) -> tuple[bool, str | None]:
        """
        Validate NSFW content safety (basic validation).
        
        Args:
            prompt: Generation prompt to validate.
            config: Optional NSFW configuration.
            
        Returns:
            Tuple of (is_safe, warning_message). is_safe=True means content is acceptable.
        """
        if config is None:
            config = NSFWContentConfig()
        
        # Skip safety checks if disabled
        if not config.safety_checks:
            return True, None
        
        # Basic safety validation
        # Check for potentially problematic content
        prompt_lower = prompt.lower()
        
        # List of terms that might indicate problematic content
        # This is a basic filter - can be enhanced with more sophisticated checks
        problematic_terms = [
            "illegal",
            "underage",
            "minor",
            "child",
            "non-consensual",
            "nonconsensual",
        ]
        
        for term in problematic_terms:
            if term in prompt_lower:
                warning = f"Prompt contains potentially problematic term: {term}"
                logger.warning(warning)
                return False, warning
        
        # Content is safe
        return True, None
    
    def get_nsfw_content_warning(self) -> str:
        """
        Get standard warning message for NSFW content.
        
        Returns:
            Warning message string.
        """
        return (
            "⚠️ NSFW Content Warning: This content is intended for adults only (18+). "
            "By generating this content, you confirm that you are of legal age and "
            "consent to viewing adult material."
        )


# Singleton instance
nsfw_content_service = NSFWContentService()
