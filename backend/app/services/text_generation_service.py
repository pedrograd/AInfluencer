"""Text generation service using Ollama."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TextGenerationRequest:
    """Request for text generation.
    
    Attributes:
        prompt: Text generation prompt.
        model: Ollama model name to use (default: llama3:8b).
        character_id: UUID of the character for persona-consistent generation, None for generic text.
        character_persona: Character personality dictionary, None to load from character_id or use defaults.
        temperature: Sampling temperature (0.0-2.0, higher = more creative, default: 0.7).
        max_tokens: Maximum number of tokens to generate, None for model default.
        system_prompt: Custom system prompt, None to use default or character-based prompt.
    """

    prompt: str
    model: str = "llama3:8b"
    character_id: str | None = None
    character_persona: dict[str, Any] | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    system_prompt: str | None = None


@dataclass
class TextGenerationResult:
    """Result of text generation.
    
    Attributes:
        text: Generated text content.
        model: Ollama model name that was used for generation.
        prompt: Original user prompt that was provided.
        full_prompt: Complete prompt including system prompt and character persona (if applicable).
        tokens_generated: Number of tokens generated, None if not available.
        generation_time_seconds: Time taken to generate the text in seconds, None if not measured.
    """

    text: str
    model: str
    prompt: str
    full_prompt: str
    tokens_generated: int | None = None
    generation_time_seconds: float | None = None


class OllamaError(RuntimeError):
    """Error from Ollama API."""

    pass


class TextGenerationService:
    """Service for generating text using Ollama."""

    def __init__(self, base_url: str | None = None) -> None:
        """
        Initialize text generation service.

        Args:
            base_url: Ollama base URL (default: http://localhost:11434)
        """
        self.base_url = (base_url or getattr(settings, "ollama_base_url", "http://localhost:11434")).rstrip("/")

    def generate_text(self, request: TextGenerationRequest) -> TextGenerationResult:
        """
        Generate text using Ollama.

        Args:
            request: Text generation request

        Returns:
            TextGenerationResult with generated text

        Raises:
            OllamaError: If generation fails
        """
        # Build full prompt with character persona if provided
        full_prompt = self._build_prompt(request)

        # Prepare Ollama API request
        payload: dict[str, Any] = {
            "model": request.model,
            "prompt": full_prompt,
            "stream": False,
        }

        if request.temperature is not None:
            payload["options"] = {"temperature": request.temperature}

        if request.max_tokens is not None:
            if "options" not in payload:
                payload["options"] = {}
            payload["options"]["num_predict"] = request.max_tokens

        if request.system_prompt:
            payload["system"] = request.system_prompt

        # Call Ollama API
        url = f"{self.base_url}/api/generate"
        import time

        start_time = time.time()
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.RequestError as exc:
            raise OllamaError(f"Unable to reach Ollama at {self.base_url}: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise OllamaError(f"Ollama API error: {exc.response.status_code} {exc.response.text}") from exc
        except Exception as exc:
            raise OllamaError(f"Unexpected error during text generation: {exc}") from exc

        generation_time = time.time() - start_time

        # Extract generated text
        generated_text = data.get("response", "")
        if not generated_text:
            raise OllamaError("Ollama returned empty response")

        # Extract token count if available
        tokens_generated = data.get("eval_count") or data.get("prompt_eval_count")

        return TextGenerationResult(
            text=generated_text.strip(),
            model=request.model,
            prompt=request.prompt,
            full_prompt=full_prompt,
            tokens_generated=tokens_generated,
            generation_time_seconds=generation_time,
        )

    def _build_prompt(self, request: TextGenerationRequest) -> str:
        """
        Build full prompt with character persona if provided.

        Args:
            request: Text generation request

        Returns:
            Full prompt string
        """
        prompt_parts: list[str] = []

        # Add character persona context if available
        if request.character_persona:
            persona_text = self._format_persona(request.character_persona)
            if persona_text:
                prompt_parts.append(f"Character persona:\n{persona_text}\n")

        # Add main prompt
        prompt_parts.append(request.prompt)

        return "\n".join(prompt_parts)

    def _format_persona(self, persona: dict[str, Any]) -> str:
        """
        Format character persona into prompt text.

        Args:
            persona: Character persona dictionary

        Returns:
            Formatted persona text
        """
        parts: list[str] = []

        # Personality traits
        if traits := persona.get("personality_traits"):
            if isinstance(traits, dict):
                trait_list = [f"{k}: {v}" for k, v in traits.items() if v]
                if trait_list:
                    parts.append(f"Personality: {', '.join(trait_list)}")

        # Communication style
        if style := persona.get("communication_style"):
            parts.append(f"Communication style: {style}")

        # Content tone
        if tone := persona.get("content_tone"):
            parts.append(f"Content tone: {tone}")

        # Bio/background
        if bio := persona.get("bio"):
            parts.append(f"Background: {bio}")

        return "\n".join(parts)

    def list_models(self) -> list[dict[str, Any]]:
        """
        List available Ollama models.

        Returns:
            List of model information dictionaries

        Raises:
            OllamaError: If request fails
        """
        url = f"{self.base_url}/api/tags"
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
                return data.get("models", [])
        except httpx.RequestError as exc:
            raise OllamaError(f"Unable to reach Ollama at {self.base_url}: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise OllamaError(f"Ollama API error: {exc.response.status_code} {exc.response.text}") from exc
        except Exception as exc:
            raise OllamaError(f"Unexpected error listing models: {exc}") from exc

    def check_health(self) -> dict[str, Any]:
        """
        Check Ollama service health.

        Returns:
            Health status dictionary

        Raises:
            OllamaError: If Ollama is not available
        """
        try:
            models = self.list_models()
            return {
                "status": "healthy",
                "base_url": self.base_url,
                "models_available": len(models),
                "models": [m.get("name", "unknown") for m in models],
            }
        except OllamaError as exc:
            return {
                "status": "unhealthy",
                "base_url": self.base_url,
                "error": str(exc),
            }


# Singleton instance
text_generation_service = TextGenerationService()

