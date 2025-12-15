"""Caption generation service for images."""

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
class CaptionGenerationRequest:
    """Request for caption generation."""

    character_id: str
    image_path: str | None = None
    content_id: str | None = None
    image_description: str | None = None
    platform: str = "instagram"  # instagram, twitter, facebook, tiktok
    style: str | None = None  # auto-detect from personality if None
    include_hashtags: bool = True
    max_length: int | None = None  # Platform-specific defaults if None


@dataclass
class CaptionGenerationResult:
    """Result of caption generation."""

    caption: str
    hashtags: list[str]
    full_caption: str  # Caption with hashtags
    style: str
    platform: str
    character_id: str


class CaptionGenerationService:
    """Service for generating captions for images."""

    # Platform-specific defaults
    PLATFORM_MAX_LENGTHS = {
        "instagram": 2200,
        "twitter": 280,
        "facebook": 5000,
        "tiktok": 150,
    }

    PLATFORM_HASHTAG_COUNTS = {
        "instagram": (5, 10),
        "twitter": (1, 3),
        "facebook": (1, 3),
        "tiktok": (3, 5),
    }

    def __init__(self) -> None:
        """Initialize caption generation service."""
        pass

    def generate_caption(
        self,
        request: CaptionGenerationRequest,
        character_persona: dict[str, Any] | None = None,
    ) -> CaptionGenerationResult:
        """
        Generate caption for an image.

        Args:
            request: Caption generation request
            character_persona: Character persona dictionary (optional)

        Returns:
            CaptionGenerationResult with generated caption

        Raises:
            ValueError: If request is invalid
        """
        # Determine style from persona if not provided
        style = request.style or self._detect_style_from_persona(character_persona)

        # Build caption prompt
        prompt = self._build_caption_prompt(request, style, character_persona)

        # Determine max tokens based on platform
        max_tokens = request.max_length or self._estimate_tokens_for_platform(request.platform)

        # Generate text using text generation service
        text_request = TextGenerationRequest(
            prompt=prompt,
            model="llama3:8b",  # Default model for captions
            character_id=request.character_id,
            character_persona=character_persona,
            temperature=0.8,  # Slightly creative for captions
            max_tokens=max_tokens,
            system_prompt=self._build_system_prompt(request.platform, style),
        )

        result = text_generation_service.generate_text(text_request)

        # Extract caption and hashtags
        caption_text = result.text.strip()
        caption, hashtags = self._parse_caption_and_hashtags(caption_text, request.include_hashtags)

        # Generate hashtags if needed
        if request.include_hashtags and not hashtags:
            hashtags = self._generate_hashtags(
                caption, request.platform, character_persona, request.image_description
            )

        # Build full caption
        full_caption = self._build_full_caption(caption, hashtags, request.platform)

        return CaptionGenerationResult(
            caption=caption,
            hashtags=hashtags,
            full_caption=full_caption,
            style=style,
            platform=request.platform,
            character_id=request.character_id,
        )

    def _detect_style_from_persona(self, persona: dict[str, Any] | None) -> str:
        """
        Detect caption style from character persona traits.
        
        Analyzes communication_style and content_tone to determine appropriate
        caption style (professional, creative, extroverted, introverted, casual).
        
        Args:
            persona: Character persona dictionary with communication_style and content_tone
        
        Returns:
            Caption style string (default: "casual" if persona is None)
        """
        if not persona:
            return "casual"

        communication_style = persona.get("communication_style", "").lower()
        content_tone = persona.get("content_tone", "").lower()

        # Map to caption styles
        if "professional" in communication_style or "professional" in content_tone:
            return "professional"
        elif "creative" in communication_style or "artistic" in content_tone:
            return "creative"
        elif "energetic" in communication_style or "extroverted" in content_tone:
            return "extroverted"
        elif "thoughtful" in communication_style or "introverted" in content_tone:
            return "introverted"
        else:
            return "casual"

    def _build_caption_prompt(
        self,
        request: CaptionGenerationRequest,
        style: str,
        persona: dict[str, Any] | None,
    ) -> str:
        """
        Build prompt for caption generation with style and platform context.
        
        Args:
            request: Caption generation request with image description and platform
            style: Caption style (extroverted, introverted, professional, casual, creative)
            persona: Character persona dictionary (optional)
        
        Returns:
            Formatted prompt string for LLM caption generation
        """
        parts: list[str] = []

        # Image description context
        if request.image_description:
            parts.append(f"Image description: {request.image_description}")
        else:
            parts.append("Generate a caption for a social media image post.")

        # Style instructions
        style_instructions = {
            "extroverted": "Write an energetic, engaging caption with questions. Be enthusiastic and interactive.",
            "introverted": "Write a thoughtful, reflective caption. Be personal and contemplative.",
            "professional": "Write an informative, polished caption. Be value-driven and clear.",
            "casual": "Write a relaxed, conversational caption. Be relatable and friendly.",
            "creative": "Write an artistic, expressive caption. Be unique and imaginative.",
        }
        parts.append(style_instructions.get(style, style_instructions["casual"]))

        # Caption structure
        parts.append(
            "Caption structure: [Hook/Opening] + [Main Content] + [Call-to-Action]. "
            "Keep it natural and engaging."
        )

        # Platform-specific guidance
        if request.platform == "twitter":
            parts.append("Keep it concise (under 280 characters).")
        elif request.platform == "tiktok":
            parts.append("Keep it short and catchy (under 150 characters).")

        # Build final prompt
        prompt = "\n".join(parts)
        return prompt

    def _build_system_prompt(self, platform: str, style: str) -> str:
        """
        Build system prompt for caption generation with platform and style context.
        
        Args:
            platform: Social media platform (instagram, twitter, tiktok, etc.)
            style: Caption style (extroverted, introverted, professional, casual, creative)
        
        Returns:
            System prompt string for LLM
        """
        return f"""You are a social media content creator writing captions for {platform} posts.
Your writing style is {style}.
Write engaging, natural captions that connect with your audience.
Keep hashtags separate from the main caption text."""

    def _parse_caption_and_hashtags(self, text: str, include_hashtags: bool) -> tuple[str, list[str]]:
        """
        Parse caption text and extract hashtags.
        
        Separates main caption text from hashtags. Removes duplicate hashtags.
        
        Args:
            text: Full caption text with potential hashtags
            include_hashtags: Whether to extract hashtags (if False, returns empty list)
        
        Returns:
            Tuple of (caption_text, hashtag_list)
        """
        if not include_hashtags:
            return text, []

        # Extract hashtags (words starting with #)
        lines = text.split("\n")
        caption_lines: list[str] = []
        hashtags: list[str] = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if line contains hashtags
            if line.startswith("#") or "#" in line:
                # Extract hashtags from line
                words = line.split()
                for word in words:
                    if word.startswith("#"):
                        hashtag = word.lstrip("#").strip()
                        if hashtag:
                            hashtags.append(hashtag)
                # If line has hashtags, don't include in caption
                if all(word.startswith("#") for word in words):
                    continue

            caption_lines.append(line)

        caption = "\n".join(caption_lines).strip()
        return caption, list(set(hashtags))  # Remove duplicates

    def _generate_hashtags(
        self,
        caption: str,
        platform: str,
        persona: dict[str, Any] | None,
        image_description: str | None,
    ) -> list[str]:
        """
        Generate relevant hashtags for caption using LLM.
        
        Generates platform-appropriate number of hashtags based on caption content
        and image description. Falls back to generic hashtags if generation fails.
        
        Args:
            caption: Caption text to generate hashtags for
            platform: Social media platform (determines hashtag count range)
            persona: Character persona dictionary (optional)
            image_description: Image description for context (optional)
        
        Returns:
            List of hashtag strings (without # prefix)
        """
        min_count, max_count = self.PLATFORM_HASHTAG_COUNTS.get(platform, (3, 5))

        # Build hashtag generation prompt
        prompt_parts = [
            f"Generate {min_count}-{max_count} relevant hashtags for this social media caption:",
            caption,
        ]

        if image_description:
            prompt_parts.append(f"Image context: {image_description}")

        prompt_parts.append(
            "Return only the hashtags, one per line, starting with #. "
            "Include a mix of popular and niche hashtags relevant to the content."
        )

        prompt = "\n".join(prompt_parts)

        # Generate hashtags using text generation service
        text_request = TextGenerationRequest(
            prompt=prompt,
            model="llama3:8b",
            temperature=0.7,
            max_tokens=100,  # Short response for hashtags
        )

        try:
            result = text_generation_service.generate_text(text_request)
            hashtag_text = result.text.strip()

            # Extract hashtags
            hashtags: list[str] = []
            for line in hashtag_text.split("\n"):
                line = line.strip()
                if line.startswith("#"):
                    hashtag = line.lstrip("#").strip()
                    if hashtag:
                        hashtags.append(hashtag)

            # Limit to max_count
            hashtags = hashtags[:max_count]

            # If we don't have enough, add some generic ones
            if len(hashtags) < min_count:
                generic_tags = ["lifestyle", "photography", "daily", "inspiration", "motivation"]
                for tag in generic_tags:
                    if tag not in hashtags and len(hashtags) < max_count:
                        hashtags.append(tag)

            return hashtags
        except Exception as exc:
            logger.warning(f"Failed to generate hashtags: {exc}")
            # Return generic hashtags as fallback
            return ["lifestyle", "photography", "daily"][:max_count]

    def _build_full_caption(self, caption: str, hashtags: list[str], platform: str) -> str:
        """
        Build full caption text with hashtags formatted for platform.
        
        Formats hashtags according to platform conventions (Instagram: separate line,
        Twitter: inline, etc.).
        
        Args:
            caption: Main caption text
            hashtags: List of hashtag strings (without # prefix)
            platform: Social media platform
        
        Returns:
            Full caption text with formatted hashtags
        """
        if not hashtags:
            return caption

        # Format hashtags
        hashtag_text = " ".join(f"#{tag}" for tag in hashtags)

        # Platform-specific formatting
        if platform == "instagram":
            # Instagram: caption on top, hashtags at bottom
            return f"{caption}\n\n{hashtag_text}"
        elif platform == "twitter":
            # Twitter: hashtags inline or at end
            return f"{caption} {hashtag_text}"
        else:
            # Default: hashtags at end
            return f"{caption}\n{hashtag_text}"

    def _estimate_tokens_for_platform(self, platform: str) -> int:
        """
        Estimate maximum tokens needed for platform-specific caption length.
        
        Uses platform character limits and rough token-to-character ratio (1:4).
        
        Args:
            platform: Social media platform
        
        Returns:
            Estimated maximum token count for caption generation
        """
        max_chars = self.PLATFORM_MAX_LENGTHS.get(platform, 500)
        # Rough estimate: 1 token ≈ 4 characters
        return max_chars // 4


# Singleton instance
caption_generation_service = CaptionGenerationService()

