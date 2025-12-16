"""Voice cloning service using Coqui TTS/XTTS."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger
from app.core.paths import voices_dir

logger = get_logger(__name__)


@dataclass
class VoiceCloningRequest:
    """Request for voice cloning.
    
    Attributes:
        reference_audio_path: Path to reference audio file (minimum 6 seconds).
        voice_name: Name to assign to the cloned voice.
        character_id: UUID of the character this voice belongs to, None for generic voice.
        language: Language code for the voice (default: en).
    """

    reference_audio_path: str | Path
    voice_name: str
    character_id: str | None = None
    language: str = "en"


@dataclass
class VoiceGenerationRequest:
    """Request for voice generation using cloned voice.
    
    Attributes:
        text: Text to convert to speech.
        voice_name: Name of the cloned voice to use.
        character_id: UUID of the character, None to use voice_name directly.
        language: Language code for generation (default: en).
        speed: Speech speed multiplier (default: 1.0).
        emotion: Emotion/style for voice (optional).
    """

    text: str
    voice_name: str
    character_id: str | None = None
    language: str = "en"
    speed: float = 1.0
    emotion: str | None = None


@dataclass
class VoiceCloningResult:
    """Result of voice cloning operation.
    
    Attributes:
        voice_name: Name assigned to the cloned voice.
        voice_id: Unique identifier for the cloned voice.
        voice_path: Path where the voice model/data is stored.
        character_id: UUID of the character this voice belongs to, None for generic voice.
        language: Language code of the cloned voice.
        status: Status of the cloning operation (success, failed, etc.).
    """

    voice_name: str
    voice_id: str
    voice_path: Path
    character_id: str | None = None
    language: str = "en"
    status: str = "success"


@dataclass
class VoiceGenerationResult:
    """Result of voice generation operation.
    
    Attributes:
        audio_path: Path to the generated audio file.
        voice_name: Name of the voice used for generation.
        text: Original text that was converted to speech.
        language: Language code used for generation.
        duration_seconds: Duration of the generated audio in seconds, None if not measured.
        generation_time_seconds: Time taken to generate the audio in seconds, None if not measured.
    """

    audio_path: Path
    voice_name: str
    text: str
    language: str = "en"
    duration_seconds: float | None = None
    generation_time_seconds: float | None = None


class VoiceCloningError(RuntimeError):
    """Error from voice cloning service."""

    pass


class VoiceCloningService:
    """Service for voice cloning and generation using Coqui TTS/XTTS."""

    def __init__(self, model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2") -> None:
        """
        Initialize voice cloning service.

        Args:
            model_name: Coqui TTS model name (default: XTTS-v2)
        """
        self.model_name = model_name
        self.voices_dir = voices_dir()
        self.voices_dir.mkdir(parents=True, exist_ok=True)
        self._tts = None  # Will be initialized lazily when needed

    def clone_voice(self, request: VoiceCloningRequest) -> VoiceCloningResult:
        """
        Clone a voice from reference audio.

        Args:
            request: Voice cloning request

        Returns:
            VoiceCloningResult with cloned voice information

        Raises:
            VoiceCloningError: If cloning fails
        """
        # TODO: Implement Coqui TTS voice cloning
        # This is step 1 - service structure only
        # Step 2 will add actual Coqui TTS integration
        
        reference_path = Path(request.reference_audio_path)
        if not reference_path.exists():
            raise VoiceCloningError(f"Reference audio file not found: {reference_path}")

        # Generate voice ID
        import uuid
        voice_id = str(uuid.uuid4())

        # Create voice directory
        voice_dir = self.voices_dir / voice_id
        voice_dir.mkdir(parents=True, exist_ok=True)

        # Store reference audio
        reference_dest = voice_dir / "reference.wav"
        # TODO: Copy and validate reference audio (step 2)

        logger.info(f"Voice cloning initiated: {request.voice_name} (ID: {voice_id})")

        return VoiceCloningResult(
            voice_name=request.voice_name,
            voice_id=voice_id,
            voice_path=voice_dir,
            character_id=request.character_id,
            language=request.language,
            status="pending",  # Will be "success" after actual cloning in step 2
        )

    def generate_voice(self, request: VoiceGenerationRequest) -> VoiceGenerationResult:
        """
        Generate speech from text using a cloned voice.

        Args:
            request: Voice generation request

        Returns:
            VoiceGenerationResult with generated audio file path

        Raises:
            VoiceCloningError: If generation fails
        """
        # TODO: Implement Coqui TTS voice generation
        # This is step 1 - service structure only
        # Step 2 will add actual Coqui TTS integration

        # Find voice directory
        voice_dir = self._find_voice_dir(request.voice_name, request.character_id)
        if not voice_dir or not voice_dir.exists():
            raise VoiceCloningError(f"Voice not found: {request.voice_name}")

        # Generate output audio path
        import uuid
        import time
        audio_filename = f"{uuid.uuid4().hex[:8]}.wav"
        audio_path = self.voices_dir / "generated" / audio_filename
        audio_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Voice generation initiated: {request.voice_name} for text: {request.text[:50]}...")

        # TODO: Call Coqui TTS to generate audio (step 2)
        # For now, return placeholder result
        return VoiceGenerationResult(
            audio_path=audio_path,
            voice_name=request.voice_name,
            text=request.text,
            language=request.language,
        )

    def list_voices(self, character_id: str | None = None) -> list[dict[str, Any]]:
        """
        List all cloned voices.

        Args:
            character_id: Optional character ID to filter voices

        Returns:
            List of voice information dictionaries
        """
        voices: list[dict[str, Any]] = []

        if not self.voices_dir.exists():
            return voices

        for voice_dir in self.voices_dir.iterdir():
            if not voice_dir.is_dir() or voice_dir.name == "generated":
                continue

            # TODO: Load voice metadata from voice_dir (step 2)
            voice_info = {
                "voice_id": voice_dir.name,
                "voice_name": voice_dir.name,  # TODO: Load from metadata
                "character_id": None,  # TODO: Load from metadata
                "language": "en",  # TODO: Load from metadata
                "voice_path": str(voice_dir),
            }

            if character_id is None or voice_info["character_id"] == character_id:
                voices.append(voice_info)

        return voices

    def delete_voice(self, voice_id: str) -> bool:
        """
        Delete a cloned voice.

        Args:
            voice_id: Voice ID to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        voice_dir = self.voices_dir / voice_id
        if not voice_dir.exists():
            return False

        import shutil
        try:
            shutil.rmtree(voice_dir)
            logger.info(f"Deleted voice: {voice_id}")
            return True
        except Exception as exc:
            logger.error(f"Failed to delete voice {voice_id}: {exc}")
            return False

    def check_health(self) -> dict[str, Any]:
        """
        Check voice cloning service health.

        Returns:
            Health status dictionary
        """
        # TODO: Check if Coqui TTS is installed and accessible (step 2)
        return {
            "status": "unknown",  # Will be "healthy" or "unhealthy" after step 2
            "model": self.model_name,
            "voices_dir": str(self.voices_dir),
            "voices_count": len(self.list_voices()),
        }

    def _find_voice_dir(self, voice_name: str, character_id: str | None = None) -> Path | None:
        """
        Find voice directory by name or character ID.

        Args:
            voice_name: Voice name to find
            character_id: Optional character ID to filter

        Returns:
            Path to voice directory, or None if not found
        """
        voices = self.list_voices(character_id=character_id)
        for voice in voices:
            if voice["voice_name"] == voice_name:
                return Path(voice["voice_path"])
        return None


# Singleton instance
voice_cloning_service = VoiceCloningService()

