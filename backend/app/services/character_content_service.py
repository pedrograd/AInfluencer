"""Character-specific content generation service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from app.models.character import Character, CharacterAppearance, CharacterPersonality
from app.models.character_style import CharacterImageStyle
from app.services.caption_generation_service import (
    CaptionGenerationRequest,
    CaptionGenerationResult,
    caption_generation_service,
)
from app.services.generation_service import generation_service
from app.services.text_generation_service import (
    TextGenerationRequest,
    TextGenerationResult,
    text_generation_service,
)

logger = get_logger(__name__)


@dataclass
class CharacterContentRequest:
    """Request for character-specific content generation.
    
    Attributes:
        character_id: UUID of the character for persona-consistent content generation.
        content_type: Type of content to generate (image, video, text, audio, image_with_caption).
        prompt: Generation prompt, None to use character defaults.
        style_id: Optional UUID of character image style to apply, None to use default style.
        platform: Target platform for content style (instagram, twitter, facebook, tiktok).
        category: Content category (post, story, reel, short, message), None for general content.
        include_caption: Whether to generate caption for images (only applies to image content_type).
        is_nsfw: Whether the content is NSFW (not safe for work).
    """

    character_id: UUID
    content_type: str  # image, video, text, audio, image_with_caption
    prompt: str | None = None
    style_id: UUID | None = None  # Optional image style ID to apply
    platform: str = "instagram"  # instagram, twitter, facebook, tiktok
    category: str | None = None  # post, story, reel, short, message
    include_caption: bool = False  # For images, generate caption too
    is_nsfw: bool = False


@dataclass
class CharacterContentResult:
    """Result of character-specific content generation.
    
    Attributes:
        character_id: UUID of the character used for generation.
        content_type: Type of content that was generated (image, video, text, audio, image_with_caption).
        content_id: UUID of the content item in database if stored, None otherwise.
        file_path: Path to the generated content file, None if generation failed.
        caption: Generated caption text (for image content with caption), None otherwise.
        hashtags: List of generated hashtags (for image content with caption), None otherwise.
        full_caption: Complete caption with hashtags (for image content with caption), None otherwise.
        metadata: Additional metadata about the generation (model used, settings, etc.), None if not available.
    """

    character_id: UUID
    content_type: str
    content_id: str | None = None  # If stored in database
    file_path: str | None = None
    caption: str | None = None
    hashtags: list[str] | None = None
    full_caption: str | None = None
    metadata: dict[str, Any] | None = None


class CharacterContentService:
    """Service for generating character-specific content."""

    def __init__(self) -> None:
        """Initialize character content service."""
        pass

    async def generate_content(
        self,
        request: CharacterContentRequest,
        character: Character,
        personality: CharacterPersonality | None = None,
        appearance: CharacterAppearance | None = None,
        style: CharacterImageStyle | None = None,
    ) -> CharacterContentResult:
        """
        Generate character-specific content.

        Args:
            request: Content generation request
            character: Character model
            personality: Character personality (optional, will load if None)
            appearance: Character appearance (optional, will load if None)

        Returns:
            CharacterContentResult with generated content

        Raises:
            ValueError: If request is invalid
        """
        # Build character persona dict for text generation
        character_persona = self._build_persona_dict(character, personality)

        if request.content_type == "image":
            return await self._generate_image(request, character, personality, appearance, style, character_persona)
        elif request.content_type == "image_with_caption":
            return await self._generate_image_with_caption(
                request, character, personality, appearance, style, character_persona
            )
        elif request.content_type == "text":
            return await self._generate_text(request, character, personality, character_persona)
        elif request.content_type == "video":
            # Video generation not yet implemented
            raise ValueError("Video generation not yet implemented")
        elif request.content_type == "audio":
            # Audio generation not yet implemented
            raise ValueError("Audio generation not yet implemented")
        else:
            raise ValueError(f"Unsupported content type: {request.content_type}")

    async def _generate_image(
        self,
        request: CharacterContentRequest,
        character: Character,
        personality: CharacterPersonality | None,
        appearance: CharacterAppearance | None,
        style: CharacterImageStyle | None,
        character_persona: dict[str, Any],
    ) -> CharacterContentResult:
        """Generate character-specific image with optional style."""
        # Build prompt with character appearance and style modifications
        prompt = request.prompt or "A natural, high-quality photo"
        if style and style.prompt_prefix:
            prompt = f"{style.prompt_prefix}, {prompt}"
        elif appearance and appearance.default_prompt_prefix:
            prompt = f"{appearance.default_prompt_prefix}, {prompt}"

        if style and style.prompt_suffix:
            prompt = f"{prompt}, {style.prompt_suffix}"

        # Build negative prompt
        negative_prompt = None
        if style and style.negative_prompt_addition:
            negative_prompt = style.negative_prompt_addition
        if appearance and appearance.negative_prompt:
            if negative_prompt:
                negative_prompt = f"{appearance.negative_prompt}, {negative_prompt}"
            else:
                negative_prompt = appearance.negative_prompt

        # Determine generation settings (style overrides appearance defaults)
        checkpoint = None
        if style and style.checkpoint:
            checkpoint = style.checkpoint
        elif appearance and appearance.base_model:
            checkpoint = appearance.base_model

        width = style.width if style and style.width else 1024
        height = style.height if style and style.height else 1024
        steps = style.steps if style and style.steps else 25
        cfg = float(style.cfg) if style and style.cfg else 7.0
        sampler_name = style.sampler_name if style and style.sampler_name else "euler"
        scheduler = style.scheduler if style and style.scheduler else "normal"

        # Create image generation job
        job = generation_service.create_image_job(
            prompt=prompt,
            negative_prompt=negative_prompt,
            seed=None,
            checkpoint=checkpoint,
            width=width,
            height=height,
            steps=steps,
            cfg=cfg,
            sampler_name=sampler_name,
            scheduler=scheduler,
            batch_size=1,
        )

        return CharacterContentResult(
            character_id=request.character_id,
            content_type="image",
            content_id=None,  # Will be set when job completes
            file_path=None,  # Will be set when job completes
            metadata={"job_id": job.id, "job_state": job.state},
        )

    async def _generate_image_with_caption(
        self,
        request: CharacterContentRequest,
        character: Character,
        personality: CharacterPersonality | None,
        appearance: CharacterAppearance | None,
        style: CharacterImageStyle | None,
        character_persona: dict[str, Any],
    ) -> CharacterContentResult:
        """Generate character-specific image with caption."""
        # First generate image
        image_result = await self._generate_image(
            request, character, personality, appearance, style, character_persona
        )

        # Then generate caption (using placeholder image description for now)
        # TODO: Use image analysis/vision model to generate description
        image_description = request.prompt or "A social media image post"

        caption_request = CaptionGenerationRequest(
            character_id=str(request.character_id),
            image_path=None,  # Will be set when image is ready
            image_description=image_description,
            platform=request.platform,
            style=None,  # Auto-detect from personality
            include_hashtags=True,
            max_length=None,  # Platform-specific default
        )

        caption_result = caption_generation_service.generate_caption(caption_request, character_persona)

        return CharacterContentResult(
            character_id=request.character_id,
            content_type="image_with_caption",
            content_id=image_result.content_id,
            file_path=image_result.file_path,
            caption=caption_result.caption,
            hashtags=caption_result.hashtags,
            full_caption=caption_result.full_caption,
            metadata={
                **(image_result.metadata or {}),
                "caption_style": caption_result.style,
                "platform": caption_result.platform,
            },
        )

    async def _generate_text(
        self,
        request: CharacterContentRequest,
        character: Character,
        personality: CharacterPersonality | None,
        character_persona: dict[str, Any],
    ) -> CharacterContentResult:
        """Generate character-specific text content."""
        if not request.prompt:
            raise ValueError("Prompt is required for text generation")

        # Build text generation prompt with character context
        full_prompt = self._build_text_prompt(request, character, personality)

        # Use character's LLM settings if available
        temperature = 0.7
        if personality and personality.temperature:
            temperature = float(personality.temperature)

        text_request = TextGenerationRequest(
            prompt=full_prompt,
            model="llama3:8b",
            character_id=str(request.character_id),
            character_persona=character_persona,
            temperature=temperature,
            max_tokens=None,  # Use default
            system_prompt=personality.llm_personality_prompt if personality else None,
        )

        text_result = text_generation_service.generate_text(text_request)

        return CharacterContentResult(
            character_id=request.character_id,
            content_type="text",
            content_id=None,
            file_path=None,
            caption=text_result.text,
            metadata={
                "model": text_result.model,
                "tokens_generated": text_result.tokens_generated,
                "generation_time_seconds": text_result.generation_time_seconds,
            },
        )

    def _build_persona_dict(
        self,
        character: Character,
        personality: CharacterPersonality | None,
    ) -> dict[str, Any]:
        """Build persona dictionary from character and personality."""
        persona: dict[str, Any] = {
            "name": character.name,
            "bio": character.bio,
        }

        if personality:
            persona.update(
                {
                    "personality_traits": {
                        "extroversion": float(personality.extroversion) if personality.extroversion else 0.5,
                        "creativity": float(personality.creativity) if personality.creativity else 0.5,
                        "humor": float(personality.humor) if personality.humor else 0.5,
                        "professionalism": float(personality.professionalism)
                        if personality.professionalism
                        else 0.5,
                        "authenticity": float(personality.authenticity) if personality.authenticity else 0.5,
                    },
                    "communication_style": personality.communication_style,
                    "content_tone": personality.content_tone,
                    "preferred_topics": personality.preferred_topics or [],
                }
            )

        return persona

    def _build_text_prompt(
        self,
        request: CharacterContentRequest,
        character: Character,
        personality: CharacterPersonality | None,
    ) -> str:
        """Build text generation prompt with character context."""
        parts: list[str] = []

        # Add character context
        if character.bio:
            parts.append(f"Character: {character.name}")
            parts.append(f"Bio: {character.bio}")

        # Add personality context
        if personality and personality.preferred_topics:
            parts.append(f"Interests: {', '.join(personality.preferred_topics)}")

        # Add main prompt
        parts.append(request.prompt or "Generate engaging social media content")

        # Add platform-specific guidance
        if request.platform == "twitter":
            parts.append("Keep it concise and engaging (under 280 characters).")
        elif request.platform == "tiktok":
            parts.append("Keep it short and catchy (under 150 characters).")

        return "\n".join(parts)


# Singleton instance
character_content_service = CharacterContentService()

