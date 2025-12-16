"""Voice cloning and generation API endpoints.

This module provides API endpoints for voice-related operations including:
- Voice cloning from reference audio using Coqui TTS/XTTS
- Voice generation from text using cloned voices
- Voice management (list, delete)
- Service health checks
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.voice_cloning_service import (
    VoiceCloningError,
    VoiceCloningRequest,
    VoiceGenerationRequest,
    voice_cloning_service,
)

router = APIRouter()


class CloneVoiceRequest(BaseModel):
    """Request model for voice cloning."""

    reference_audio_path: str = Field(..., min_length=1, max_length=2048, description="Path to reference audio file (minimum 6 seconds)")
    voice_name: str = Field(..., min_length=1, max_length=128, description="Name to assign to the cloned voice")
    character_id: str | None = Field(default=None, max_length=128, description="UUID of the character this voice belongs to (optional)")
    language: str = Field(default="en", max_length=8, description="Language code for the voice (default: 'en')")


@router.post("/clone")
def clone_voice(req: CloneVoiceRequest) -> dict:
    """
    Clone a voice from reference audio using Coqui TTS/XTTS.

    Creates a cloned voice model from a reference audio file. The reference
    audio should be at least 6 seconds long and contain clear speech.
    
    Args:
        req: Voice cloning request with reference audio path, voice name, and optional character ID
        
    Returns:
        dict: Response with cloned voice information:
            On success: {"ok": True, "voice_name": "...", "voice_id": "...", ...}
            On error: {"ok": False, "error": "error message"}
    """
    try:
        request = VoiceCloningRequest(
            reference_audio_path=req.reference_audio_path,
            voice_name=req.voice_name,
            character_id=req.character_id,
            language=req.language,
        )
        result = voice_cloning_service.clone_voice(request)
        return {
            "ok": True,
            "voice_name": result.voice_name,
            "voice_id": result.voice_id,
            "voice_path": str(result.voice_path),
            "character_id": result.character_id,
            "language": result.language,
            "status": result.status,
        }
    except VoiceCloningError as exc:
        return {"ok": False, "error": str(exc), "message": f"Voice cloning failed: {str(exc)}"}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "message": f"Unexpected error during voice cloning: {str(exc)}"}


class GenerateVoiceRequest(BaseModel):
    """Request model for voice generation."""

    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert to speech (1-5000 characters)")
    voice_name: str = Field(..., min_length=1, max_length=128, description="Name of the cloned voice to use")
    character_id: str | None = Field(default=None, max_length=128, description="UUID of the character (optional, used to find voice if voice_name matches)")
    language: str = Field(default="en", max_length=8, description="Language code for generation (default: 'en')")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed multiplier (0.5-2.0, default: 1.0)")
    emotion: str | None = Field(default=None, max_length=64, description="Emotion/style for voice (optional)")


@router.post("/generate")
def generate_voice(req: GenerateVoiceRequest) -> dict:
    """
    Generate speech from text using a cloned voice.

    Converts text to speech using a previously cloned voice model.
    The voice must have been created via the /voice/clone endpoint.
    
    Args:
        req: Voice generation request with text, voice name, and optional parameters
        
    Returns:
        dict: Response with generated audio information:
            On success: {"ok": True, "audio_path": "...", "voice_name": "...", ...}
            On error: {"ok": False, "error": "error message"}
    """
    try:
        request = VoiceGenerationRequest(
            text=req.text,
            voice_name=req.voice_name,
            character_id=req.character_id,
            language=req.language,
            speed=req.speed,
            emotion=req.emotion,
        )
        result = voice_cloning_service.generate_voice(request)
        return {
            "ok": True,
            "audio_path": str(result.audio_path),
            "voice_name": result.voice_name,
            "text": result.text,
            "language": result.language,
            "duration_seconds": result.duration_seconds,
            "generation_time_seconds": result.generation_time_seconds,
        }
    except VoiceCloningError as exc:
        return {"ok": False, "error": str(exc), "message": f"Voice generation failed: {str(exc)}"}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "message": f"Unexpected error during voice generation: {str(exc)}"}


@router.get("/list")
def list_voices(character_id: str | None = None) -> dict:
    """
    List all cloned voices.

    Returns a list of all available cloned voices, optionally filtered by character ID.
    
    Args:
        character_id: Optional character ID to filter voices
        
    Returns:
        dict: Response with list of voices:
            {"ok": True, "voices": [...]}
    """
    try:
        voices = voice_cloning_service.list_voices(character_id=character_id)
        return {
            "ok": True,
            "voices": voices,
            "count": len(voices),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "message": f"Failed to list voices: {str(exc)}"}


@router.delete("/{voice_id}")
def delete_voice(voice_id: str) -> dict:
    """
    Delete a cloned voice.

    Removes a voice model and all associated data. This operation cannot be undone.
    
    Args:
        voice_id: Voice ID to delete
        
    Returns:
        dict: Response indicating success or failure:
            On success: {"ok": True, "message": "Voice deleted successfully"}
            On error: {"ok": False, "error": "error message"}
    """
    try:
        deleted = voice_cloning_service.delete_voice(voice_id)
        if deleted:
            return {"ok": True, "message": f"Voice {voice_id} deleted successfully"}
        else:
            return {"ok": False, "error": f"Voice {voice_id} not found", "message": f"Voice {voice_id} not found"}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "message": f"Failed to delete voice: {str(exc)}"}


@router.get("/health")
def voice_health() -> dict:
    """
    Check voice cloning service health.

    Returns the health status of the voice cloning service including
    model information, voices directory, and voice count.
    
    Returns:
        dict: Health status information:
            {"ok": True, "status": "...", "model": "...", ...}
    """
    try:
        health = voice_cloning_service.check_health()
        return {
            "ok": True,
            **health,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "message": f"Health check failed: {str(exc)}"}

