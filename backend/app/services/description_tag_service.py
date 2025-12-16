"""Description and tag generation service for content items."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.logging import get_logger
from app.services.text_generation_service import (
    TextGenerationRequest,
    TextGenerationResult,
    text_generation_service,
)

logger = get_logger(__name__)


@dataclass
class DescriptionTagGenerationRequest:
    """Request for description and tag generation.
    
    Attributes:
        content_id: UUID of the content item in database (optional if image_path/prompt provided).
        character_id: UUID of the character for persona-consistent generation (optional).
        content_type: Type of content (image, video, text, audio).
        image_path: Path to the image file, None if using content_id instead (optional).
        prompt: Generation prompt used to create content (optional).
        platform: Target platform for tag generation context (instagram, twitter, facebook, tiktok, optional).
        max_tags: Maximum number of tags to generate (default: 10).
        include_hashtag_format: Whether to include hashtag format in tags (#tag format, default: False).
    """

    content_id: str | None = None
    character_id: str | None = None
    content_type: str = "image"  # image, video, text, audio
    image_path: str | None = None
    prompt: str | None = None
    platform: str | None = None
    max_tags: int = 10
    include_hashtag_format: bool = False


@dataclass
class DescriptionTagGenerationResult:
    """Result of description and tag generation.
    
    Attributes:
        description: Generated description text for the content.
        tags: List of generated tags (without # prefix unless include_hashtag_format is True).
        content_type: Type of content that was processed.
        character_id: UUID of the character used for persona-consistent generation (if provided).
    """

    description: str
    tags: list[str]
    content_type: str
    character_id: str | None = None


class DescriptionTagGenerationService:
    """Service for generating descriptions and tags for content items."""

    # Content type categories for tag generation
    CONTENT_TYPE_CATEGORIES = {
        "image": ["photography", "visual", "photo", "image"],
        "video": ["video", "moving", "clip", "content"],
        "text": ["text", "written", "post", "caption"],
        "audio": ["audio", "sound", "music", "voice"],
    }

    # Common tag prefixes based on content type
    TYPE_SPECIFIC_TAGS = {
        "image": ["photography", "photo", "picture", "visual"],
        "video": ["video", "clip", "film", "footage"],
        "text": ["text", "writing", "post", "content"],
        "audio": ["audio", "sound", "music", "podcast"],
    }

    def __init__(self) -> None:
        """Initialize description and tag generation service."""
        pass

    def generate_description_and_tags(
        self,
        request: DescriptionTagGenerationRequest,
        character_persona: dict[str, Any] | None = None,
    ) -> DescriptionTagGenerationResult:
        """
        Generate description and tags for a content item.

        Args:
            request: Description and tag generation request
            character_persona: Character persona dictionary (optional)

        Returns:
            DescriptionTagGenerationResult with generated description and tags

        Raises:
            ValueError: If request is invalid
        """
        # Validate request
        if not request.content_id and not request.image_path and not request.prompt:
            raise ValueError("At least one of content_id, image_path, or prompt must be provided")

        # Generate description
        description = self._generate_description(request, character_persona)

        # Generate tags
        tags = self._generate_tags(request, description, character_persona)

        return DescriptionTagGenerationResult(
            description=description,
            tags=tags,
            content_type=request.content_type,
            character_id=request.character_id,
        )

    def _generate_description(
        self,
        request: DescriptionTagGenerationRequest,
        persona: dict[str, Any] | None,
    ) -> str:
        """
        Generate a description for the content item.
        
        Creates a natural language description based on prompt, content type,
        and character persona (if available).
        
        Args:
            request: Description generation request with prompt, content_type, etc.
            persona: Character persona dictionary (optional)
        
        Returns:
            Generated description text
        """
        # Build description prompt
        prompt_parts = []

        # Content type context
        content_type_label = request.content_type.capitalize()
        prompt_parts.append(f"Generate a concise, natural description for a {content_type_label.lower()} content item.")

        # Prompt context
        if request.prompt:
            prompt_parts.append(f"Content was generated using this prompt: {request.prompt}")
        else:
            prompt_parts.append("Generate a description based on the content type and context.")

        # Character persona context (if available)
        if persona:
            personality_traits = persona.get("personality_traits", [])
            communication_style = persona.get("communication_style", "")
            if personality_traits or communication_style:
                persona_context = "This content belongs to a character with the following traits: "
                if personality_traits:
                    persona_context += f"Personality: {', '.join(personality_traits[:3])}. "
                if communication_style:
                    persona_context += f"Style: {communication_style}."
                prompt_parts.append(persona_context)

        # Platform context (if available)
        if request.platform:
            prompt_parts.append(f"This content is intended for {request.platform} platform.")

        # Description requirements
        prompt_parts.append(
            "Description requirements:\n"
            "- Be concise but descriptive (2-3 sentences, 50-150 words)\n"
            "- Use natural, engaging language\n"
            "- Highlight key visual or content elements\n"
            "- Make it suitable for metadata/search purposes"
        )

        prompt = "\n".join(prompt_parts)

        # Generate description using text generation service
        text_request = TextGenerationRequest(
            prompt=prompt,
            model="llama3:8b",
            character_id=request.character_id,
            character_persona=persona,
            temperature=0.7,
            max_tokens=200,  # ~150 words
            system_prompt="You are a content description generator. Create clear, concise, and engaging descriptions for social media content.",
        )

        try:
            result = text_generation_service.generate_text(text_request)
            description = result.text.strip()
            
            # Clean up description (remove quotes if wrapped)
            if description.startswith('"') and description.endswith('"'):
                description = description[1:-1]
            elif description.startswith("'") and description.endswith("'"):
                description = description[1:-1]
            
            return description
        except Exception as exc:
            logger.warning(f"Failed to generate description: {exc}")
            # Fallback description
            return self._generate_fallback_description(request)

    def _generate_tags(
        self,
        request: DescriptionTagGenerationRequest,
        description: str,
        persona: dict[str, Any] | None,
    ) -> list[str]:
        """
        Generate tags for the content item.
        
        Generates relevant tags based on description, content type, prompt,
        and character persona. Tags are useful for categorization and search.
        
        Args:
            request: Tag generation request with content_type, prompt, etc.
            description: Generated description text
            persona: Character persona dictionary (optional)
        
        Returns:
            List of tag strings (without # prefix unless include_hashtag_format is True)
        """
        # Build tag generation prompt
        prompt_parts = [
            f"Generate {request.max_tags} relevant tags for the following content description:",
            description,
        ]

        # Add prompt context if available
        if request.prompt:
            prompt_parts.append(f"\nOriginal generation prompt: {request.prompt}")

        # Add content type context
        prompt_parts.append(f"\nContent type: {request.content_type}")

        # Add character context if available
        if persona:
            interests = persona.get("interests", [])
            content_themes = persona.get("content_themes", [])
            if interests:
                prompt_parts.append(f"Character interests: {', '.join(interests[:5])}")
            if content_themes:
                prompt_parts.append(f"Content themes: {', '.join(content_themes[:3])}")

        # Platform context
        if request.platform:
            prompt_parts.append(f"Platform: {request.platform}")

        # Tag requirements
        prompt_parts.append(
            f"\nGenerate exactly {request.max_tags} tags with these requirements:\n"
            "- Use lowercase, single words or short phrases (max 2 words)\n"
            "- Include a mix of: content type tags, theme/topic tags, style tags, and platform tags\n"
            "- Make tags searchable and relevant for categorization\n"
            "- Return only the tags, one per line, no numbering or bullets"
        )

        prompt = "\n".join(prompt_parts)

        # Generate tags using text generation service
        text_request = TextGenerationRequest(
            prompt=prompt,
            model="llama3:8b",
            character_id=request.character_id,
            character_persona=persona,
            temperature=0.8,  # Slightly more creative for tag variety
            max_tokens=150,  # Short response for tags
            system_prompt="You are a content tagging expert. Generate relevant, searchable tags for social media content.",
        )

        try:
            result = text_generation_service.generate_text(text_request)
            tag_text = result.text.strip()

            # Extract tags from response
            tags: list[str] = []
            for line in tag_text.split("\n"):
                line = line.strip()
                # Remove bullets, numbering, dashes
                line = line.lstrip("- •*0123456789. ").strip()
                # Skip empty lines
                if not line:
                    continue
                # Remove hashtag prefix if present (we'll add it conditionally)
                if line.startswith("#"):
                    line = line[1:]
                # Normalize to lowercase
                line = line.lower()
                # Remove special characters except spaces and hyphens
                cleaned = "".join(c for c in line if c.isalnum() or c in (" ", "-")).strip()
                # Split multi-word tags, but keep if already a phrase
                if cleaned and len(cleaned) <= 30:  # Max tag length
                    tags.append(cleaned)

            # Limit to max_tags
            tags = tags[:request.max_tags]

            # Add content type specific tags if we don't have enough
            if len(tags) < request.max_tags:
                type_tags = self.TYPE_SPECIFIC_TAGS.get(request.content_type, [])
                for tag in type_tags:
                    if tag not in tags and len(tags) < request.max_tags:
                        tags.append(tag)

            # Add generic content tags if still not enough
            if len(tags) < request.max_tags:
                generic_tags = ["content", "social", "media", "post", "creative", "digital"]
                for tag in generic_tags:
                    if tag not in tags and len(tags) < request.max_tags:
                        tags.append(tag)

            # Apply hashtag format if requested
            if request.include_hashtag_format:
                tags = [f"#{tag}" if not tag.startswith("#") else tag for tag in tags]

            return tags[:request.max_tags]
        except Exception as exc:
            logger.warning(f"Failed to generate tags: {exc}")
            # Fallback tags
            return self._generate_fallback_tags(request)

    def _generate_fallback_description(self, request: DescriptionTagGenerationRequest) -> str:
        """
        Generate a fallback description if LLM generation fails.
        
        Args:
            request: Description generation request
        
        Returns:
            Fallback description text
        """
        content_type = request.content_type.capitalize()
        if request.prompt:
            # Extract key words from prompt
            prompt_words = request.prompt.split()[:10]
            prompt_summary = " ".join(prompt_words)
            return f"A {content_type.lower()} content item: {prompt_summary}..."
        else:
            return f"A {content_type.lower()} content item for social media."

    def _generate_fallback_tags(self, request: DescriptionTagGenerationRequest) -> list[str]:
        """
        Generate fallback tags if LLM generation fails.
        
        Args:
            request: Tag generation request
        
        Returns:
            List of fallback tag strings
        """
        tags = self.TYPE_SPECIFIC_TAGS.get(request.content_type, ["content"]).copy()

        # Add generic tags
        generic_tags = ["social", "media", "digital", "creative", "post"]
        for tag in generic_tags:
            if len(tags) < request.max_tags:
                tags.append(tag)

        # Add platform tag if available
        if request.platform and len(tags) < request.max_tags:
            tags.append(request.platform)

        # Apply hashtag format if requested
        if request.include_hashtag_format:
            tags = [f"#{tag}" if not tag.startswith("#") else tag for tag in tags]

        return tags[:request.max_tags]


# Singleton instance
description_tag_service = DescriptionTagGenerationService()

