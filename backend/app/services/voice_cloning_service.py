"""Voice cloning service using Coqui TTS/XTTS."""

from __future__ import annotations

import json
import shutil
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger
from app.core.paths import voices_dir

logger = get_logger(__name__)

# Lazy import TTS to avoid import errors if not installed
try:
    from TTS.api import TTS

    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    TTS = None  # type: ignore


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

    def _get_tts(self):
        """Get or initialize TTS model (lazy loading)."""
        if not TTS_AVAILABLE:
            raise VoiceCloningError("Coqui TTS is not installed. Install with: pip install TTS")
        if self._tts is None:
            try:
                logger.info(f"Initializing Coqui TTS model: {self.model_name}")
                self._tts = TTS(self.model_name)
                logger.info("Coqui TTS model initialized successfully")
            except Exception as exc:
                logger.error(f"Failed to initialize Coqui TTS: {exc}")
                raise VoiceCloningError(f"Failed to initialize Coqui TTS: {exc}") from exc
        return self._tts

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
        reference_path = Path(request.reference_audio_path)
        if not reference_path.exists():
            raise VoiceCloningError(f"Reference audio file not found: {reference_path}")

        # Validate reference audio (XTTS requires at least 6 seconds)
        # Note: Full validation would require audio processing library, but we'll do basic checks
        if reference_path.stat().st_size < 1000:  # Basic size check (very small files likely invalid)
            logger.warning(f"Reference audio file is very small: {reference_path}")

        # Generate voice ID
        voice_id = str(uuid.uuid4())

        # Create voice directory
        voice_dir = self.voices_dir / voice_id
        voice_dir.mkdir(parents=True, exist_ok=True)

        # Copy and store reference audio
        reference_dest = voice_dir / "reference.wav"
        try:
            shutil.copy2(reference_path, reference_dest)
            logger.info(f"Copied reference audio to: {reference_dest}")
        except Exception as exc:
            raise VoiceCloningError(f"Failed to copy reference audio: {exc}") from exc

        # Store voice metadata
        metadata = {
            "voice_name": request.voice_name,
            "voice_id": voice_id,
            "character_id": request.character_id,
            "language": request.language,
            "reference_audio_path": str(reference_dest),
            "created_at": time.time(),
        }
        metadata_path = voice_dir / "metadata.json"
        try:
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
        except Exception as exc:
            logger.warning(f"Failed to save metadata: {exc}")

        logger.info(f"Voice cloning completed: {request.voice_name} (ID: {voice_id})")

        return VoiceCloningResult(
            voice_name=request.voice_name,
            voice_id=voice_id,
            voice_path=voice_dir,
            character_id=request.character_id,
            language=request.language,
            status="success",
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
        # Find voice directory
        voice_dir = self._find_voice_dir(request.voice_name, request.character_id)
        if not voice_dir or not voice_dir.exists():
            raise VoiceCloningError(f"Voice not found: {request.voice_name}")

        # Get reference audio path
        reference_audio = voice_dir / "reference.wav"
        if not reference_audio.exists():
            raise VoiceCloningError(f"Reference audio not found for voice: {request.voice_name}")

        # Generate output audio path
        audio_filename = f"{uuid.uuid4().hex[:8]}.wav"
        audio_path = self.voices_dir / "generated" / audio_filename
        audio_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Voice generation initiated: {request.voice_name} for text: {request.text[:50]}...")

        # Generate audio using Coqui TTS
        start_time = time.time()
        try:
            tts = self._get_tts()
            # XTTS-v2 API: tts.tts_to_file(text, speaker_wav, language, file_path)
            tts.tts_to_file(
                text=request.text,
                speaker_wav=str(reference_audio),
                language=request.language,
                file_path=str(audio_path),
            )
            generation_time = time.time() - start_time

            # Get audio duration (basic check - file exists)
            duration_seconds = None
            if audio_path.exists():
                # Note: Full duration calculation would require audio processing library
                # For now, we'll leave it as None or estimate from file size
                file_size = audio_path.stat().st_size
                # Rough estimate: ~16KB per second for 16kHz mono WAV
                duration_seconds = file_size / 16000.0 if file_size > 0 else None

            logger.info(f"Voice generation completed: {audio_path} (took {generation_time:.2f}s)")

            return VoiceGenerationResult(
                audio_path=audio_path,
                voice_name=request.voice_name,
                text=request.text,
                language=request.language,
                duration_seconds=duration_seconds,
                generation_time_seconds=generation_time,
            )
        except Exception as exc:
            logger.error(f"Voice generation failed: {exc}")
            # Clean up partial file if it exists
            if audio_path.exists():
                try:
                    audio_path.unlink()
                except Exception:
                    pass
            raise VoiceCloningError(f"Voice generation failed: {exc}") from exc

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

            # Load voice metadata from voice_dir
            metadata_path = voice_dir / "metadata.json"
            if metadata_path.exists():
                try:
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                    voice_info = {
                        "voice_id": metadata.get("voice_id", voice_dir.name),
                        "voice_name": metadata.get("voice_name", voice_dir.name),
                        "character_id": metadata.get("character_id"),
                        "language": metadata.get("language", "en"),
                        "voice_path": str(voice_dir),
                    }
                except Exception as exc:
                    logger.warning(f"Failed to load metadata for {voice_dir}: {exc}")
                    # Fallback to directory name
                    voice_info = {
                        "voice_id": voice_dir.name,
                        "voice_name": voice_dir.name,
                        "character_id": None,
                        "language": "en",
                        "voice_path": str(voice_dir),
                    }
            else:
                # No metadata file - use directory name as fallback
                voice_info = {
                    "voice_id": voice_dir.name,
                    "voice_name": voice_dir.name,
                    "character_id": None,
                    "language": "en",
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
        status = "healthy"
        error = None

        # Check if TTS is available
        if not TTS_AVAILABLE:
            status = "unhealthy"
            error = "Coqui TTS is not installed. Install with: pip install TTS"
        else:
            # Try to initialize TTS model to verify it's accessible
            try:
                tts = self._get_tts()
                if tts is None:
                    status = "unhealthy"
                    error = "Failed to initialize TTS model"
            except Exception as exc:
                status = "unhealthy"
                error = f"TTS initialization failed: {exc}"

        return {
            "status": status,
            "model": self.model_name,
            "voices_dir": str(self.voices_dir),
            "voices_count": len(self.list_voices()),
            "error": error,
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

