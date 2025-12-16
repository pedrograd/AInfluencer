"""Character voice generation service.

This service integrates voice cloning with the character system,
providing character-specific voice operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.character import Character
from app.services.voice_cloning_service import (
    VoiceCloningRequest,
    VoiceCloningResult,
    VoiceGenerationRequest,
    VoiceGenerationResult,
    VoiceCloningError,
    voice_cloning_service,
)

logger = get_logger(__name__)


@dataclass
class CharacterVoiceCloneRequest:
    """Request to clone a voice for a character.
    
    Attributes:
        character_id: UUID of the character.
        reference_audio_path: Path to reference audio file (minimum 6 seconds).
        voice_name: Optional name for the voice (defaults to character name + " Voice").
        language: Language code for the voice (default: en).
    """

    character_id: str | UUID
    reference_audio_path: str | Path
    voice_name: str | None = None
    language: str = "en"


@dataclass
class CharacterVoiceGenerateRequest:
    """Request to generate speech for a character.
    
    Attributes:
        character_id: UUID of the character.
        text: Text to convert to speech.
        language: Language code for generation (default: en).
        speed: Speech speed multiplier (default: 1.0).
        emotion: Emotion/style for voice (optional).
    """

    character_id: str | UUID
    text: str
    language: str = "en"
    speed: float = 1.0
    emotion: str | None = None


class CharacterVoiceError(RuntimeError):
    """Error from character voice service."""

    pass


class CharacterVoiceService:
    """Service for character-specific voice operations."""

    def __init__(self) -> None:
        """Initialize character voice service."""
        self.voice_service = voice_cloning_service

    async def clone_voice_for_character(
        self, request: CharacterVoiceCloneRequest, db: AsyncSession | None = None
    ) -> VoiceCloningResult:
        """
        Clone a voice for a character.

        Args:
            request: Character voice cloning request
            db: Optional database session for loading character name

        Returns:
            VoiceCloningResult with cloned voice information

        Raises:
            CharacterVoiceError: If cloning fails
        """
        character_id_str = str(request.character_id)

        # Generate voice name if not provided
        voice_name = request.voice_name
        if not voice_name:
            # Load character name from database
            if db:
                try:
                    character_uuid = UUID(character_id_str)
                    query = select(Character).where(
                        Character.id == character_uuid,
                        Character.deleted_at.is_(None),
                    )
                    result = await db.execute(query)
                    character = result.scalar_one_or_none()
                    if character:
                        voice_name = f"{character.name} Voice"
                        logger.info(f"Loaded character name: {character.name}")
                    else:
                        logger.warning(
                            f"Character {character_id_str} not found, using fallback name"
                        )
                        voice_name = f"Character-{character_id_str[:8]}-Voice"
                except Exception as exc:
                    logger.warning(f"Failed to load character name: {exc}, using fallback")
                    voice_name = f"Character-{character_id_str[:8]}-Voice"
            else:
                # Fallback if no database session provided
                voice_name = f"Character-{character_id_str[:8]}-Voice"
                logger.warning(
                    f"No database session provided, using fallback voice name: {voice_name}"
                )

        try:
            # Clone voice using voice cloning service
            clone_request = VoiceCloningRequest(
                reference_audio_path=request.reference_audio_path,
                voice_name=voice_name,
                character_id=character_id_str,
                language=request.language,
            )
            result = self.voice_service.clone_voice(clone_request)

            logger.info(
                f"Voice cloned for character {character_id_str}: {result.voice_name} (ID: {result.voice_id})"
            )

            return result
        except VoiceCloningError as exc:
            raise CharacterVoiceError(f"Failed to clone voice for character: {exc}") from exc
        except Exception as exc:
            raise CharacterVoiceError(f"Unexpected error during voice cloning: {exc}") from exc

    async def generate_voice_for_character(
        self, request: CharacterVoiceGenerateRequest, db: AsyncSession | None = None
    ) -> VoiceGenerationResult:
        """
        Generate speech for a character using their cloned voice.

        Args:
            request: Character voice generation request

        Returns:
            VoiceGenerationResult with generated audio file path

        Raises:
            CharacterVoiceError: If generation fails
        """
        character_id_str = str(request.character_id)

        # Find voice for character
        voices = self.voice_service.list_voices(character_id=character_id_str)
        if not voices:
            raise CharacterVoiceError(
                f"No voice found for character {character_id_str}. Clone a voice first."
            )

        # Use the first voice found for this character
        # TODO: Support multiple voices per character (step 2)
        voice_name = voices[0]["voice_name"]

        try:
            # Generate voice using voice cloning service
            generate_request = VoiceGenerationRequest(
                text=request.text,
                voice_name=voice_name,
                character_id=character_id_str,
                language=request.language,
                speed=request.speed,
                emotion=request.emotion,
            )
            result = self.voice_service.generate_voice(generate_request)

            logger.info(
                f"Voice generated for character {character_id_str}: {result.audio_path}"
            )

            return result
        except VoiceCloningError as exc:
            raise CharacterVoiceError(f"Failed to generate voice for character: {exc}") from exc
        except Exception as exc:
            raise CharacterVoiceError(f"Unexpected error during voice generation: {exc}") from exc

    def get_character_voices(self, character_id: str | UUID) -> list[dict[str, Any]]:
        """
        Get all voices for a character.

        Args:
            character_id: UUID of the character

        Returns:
            List of voice information dictionaries
        """
        character_id_str = str(character_id)
        return self.voice_service.list_voices(character_id=character_id_str)

    def delete_character_voice(self, character_id: str | UUID, voice_id: str) -> bool:
        """
        Delete a voice for a character.

        Args:
            character_id: UUID of the character
            voice_id: Voice ID to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        character_id_str = str(character_id)

        # Verify voice belongs to character
        voices = self.get_character_voices(character_id_str)
        voice_ids = [v["voice_id"] for v in voices]
        if voice_id not in voice_ids:
            logger.warning(
                f"Voice {voice_id} not found for character {character_id_str}"
            )
            return False

        return self.voice_service.delete_voice(voice_id)


# Singleton instance
character_voice_service = CharacterVoiceService()

