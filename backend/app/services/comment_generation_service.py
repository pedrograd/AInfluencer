"""Comment generation service for natural, varied comments using character personality."""

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
class CommentGenerationRequest:
    """Request for comment generation.
    
    Attributes:
        character_id: UUID of the character for persona-consistent comment generation.
        post_description: Description of the post being commented on (optional).
        post_media_type: Type of media (image, video, carousel, story).
        comment_style: Comment style (short, medium, long, emoji_heavy, casual, enthusiastic).
        max_length: Maximum comment length in characters (default: 150 for Instagram).
    """

    character_id: str
    post_description: str | None = None
    post_media_type: str = "image"  # image, video, carousel, story
    comment_style: str | None = None  # auto-detect from personality if None
    max_length: int = 150  # Instagram comment limit


@dataclass
class CommentGenerationResult:
    """Result of comment generation.
    
    Attributes:
        comment_text: Generated comment text.
        style: Comment style that was used.
        character_id: UUID of the character used for generation.
    """

    comment_text: str
    style: str
    character_id: str


class CommentGenerationService:
    """Service for generating natural, varied comments using character personality."""

    COMMENT_STYLES = [
        "short_casual",  # "Love this! ❤️"
        "medium_enthusiastic",  # "This is amazing! So inspiring! 🔥"
        "long_thoughtful",  # "This really resonates with me. The way you've captured..."
        "emoji_heavy",  # "🔥🔥🔥 This is incredible! ✨✨✨"
        "question",  # "Where did you get this? Would love to know more!"
        "compliment",  # "Your work is always so beautiful!"
        "relatable",  # "This is exactly how I feel! So true."
    ]

    def __init__(self) -> None:
        """Initialize comment generation service."""
        pass

    def generate_comment(
        self,
        request: CommentGenerationRequest,
        character_persona: dict[str, Any] | None = None,
    ) -> CommentGenerationResult:
        """
        Generate a natural, varied comment using character personality.

        Args:
            request: Comment generation request
            character_persona: Character persona dictionary (optional)

        Returns:
            CommentGenerationResult with generated comment

        Raises:
            ValueError: If request is invalid
        """
        # Determine style from persona if not provided
        style = request.comment_style or self._select_style_from_persona(character_persona)

        # Build comment prompt
        prompt = self._build_comment_prompt(request, style, character_persona)

        # Generate text using text generation service
        text_request = TextGenerationRequest(
            prompt=prompt,
            model="llama3:8b",
            character_id=request.character_id,
            character_persona=character_persona,
            temperature=0.9,  # Higher temperature for more variety
            max_tokens=min(request.max_length // 4, 50),  # Approximate token count
            system_prompt=self._build_system_prompt(style),
        )

        result = text_generation_service.generate_text(text_request)

        # Clean and validate comment
        comment_text = self._clean_comment(result.text, request.max_length)

        return CommentGenerationResult(
            comment_text=comment_text,
            style=style,
            character_id=request.character_id,
        )

    def _select_style_from_persona(self, persona: dict[str, Any] | None) -> str:
        """
        Select comment style based on character personality.

        Args:
            persona: Character persona dictionary

        Returns:
            Selected comment style
        """
        if not persona:
            return "medium_enthusiastic"

        # Use personality traits to select style
        personality_traits = persona.get("personality_traits", [])
        communication_style = persona.get("communication_style", "").lower()

        # Map personality to comment styles
        if "enthusiastic" in communication_style or "energetic" in str(personality_traits):
            return "medium_enthusiastic"
        elif "thoughtful" in communication_style or "introspective" in str(personality_traits):
            return "long_thoughtful"
        elif "casual" in communication_style:
            return "short_casual"
        elif "playful" in communication_style:
            return "emoji_heavy"
        else:
            # Default: vary between styles
            import random
            return random.choice(["short_casual", "medium_enthusiastic", "compliment"])

    def _build_comment_prompt(
        self,
        request: CommentGenerationRequest,
        style: str,
        character_persona: dict[str, Any] | None,
    ) -> str:
        """
        Build prompt for comment generation.

        Args:
            request: Comment generation request
            style: Comment style
            character_persona: Character persona dictionary

        Returns:
            Comment generation prompt
        """
        parts: list[str] = []

        # Style instruction
        style_instructions = {
            "short_casual": "Write a short, casual comment (under 20 words). Be friendly and natural.",
            "medium_enthusiastic": "Write an enthusiastic comment (20-40 words). Show genuine interest and energy.",
            "long_thoughtful": "Write a thoughtful, longer comment (40-60 words). Share a meaningful perspective.",
            "emoji_heavy": "Write a comment with emojis (15-30 words). Be playful and expressive.",
            "question": "Write a comment that asks a question (15-30 words). Show curiosity.",
            "compliment": "Write a genuine compliment (15-30 words). Be specific and sincere.",
            "relatable": "Write a relatable comment (20-40 words). Show you understand and relate.",
        }
        parts.append(style_instructions.get(style, "Write a natural, engaging comment."))

        # Post context
        if request.post_description:
            parts.append(f"Post description: {request.post_description}")
        parts.append(f"Media type: {request.post_media_type}")

        # Character context
        if character_persona:
            personality_traits = character_persona.get("personality_traits", [])
            communication_style = character_persona.get("communication_style", "")
            if personality_traits:
                parts.append(f"Character personality: {', '.join(str(personality_traits[:3]))}")
            if communication_style:
                parts.append(f"Communication style: {communication_style}")

        # Requirements
        parts.append(f"Keep comment under {request.max_length} characters.")
        parts.append("Make it sound natural and human-like. Avoid spammy or generic phrases.")
        parts.append("Generate ONLY the comment text, nothing else.")

        return "\n".join(parts)

    def _build_system_prompt(self, style: str) -> str:
        """
        Build system prompt for comment generation.

        Args:
            style: Comment style

        Returns:
            System prompt
        """
        return f"""You are generating Instagram comments that sound natural and human-like.
Style: {style}
Requirements:
- Sound authentic and genuine
- Match the character's personality
- Vary your comments (don't repeat the same phrases)
- Keep it appropriate and positive
- Use natural language, not marketing speak"""

    def _clean_comment(self, text: str, max_length: int) -> str:
        """
        Clean and validate generated comment.

        Args:
            text: Raw generated text
            max_length: Maximum comment length

        Returns:
            Cleaned comment text
        """
        # Remove quotes if wrapped
        text = text.strip().strip('"').strip("'")

        # Remove any prefix like "Comment:" or "Response:"
        prefixes = ["Comment:", "Response:", "Comment text:", "Generated comment:"]
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix) :].strip()

        # Truncate to max length
        if len(text) > max_length:
            # Try to truncate at word boundary
            truncated = text[:max_length].rsplit(" ", 1)[0]
            if len(truncated) > max_length * 0.8:  # Keep if at least 80% of max
                text = truncated
            else:
                text = text[:max_length]

        return text.strip()


# Singleton instance
comment_generation_service = CommentGenerationService()
