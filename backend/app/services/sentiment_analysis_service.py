"""Sentiment analysis service for analyzing text sentiment."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SentimentLabel(str, Enum):
    """Sentiment label options."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class SentimentAnalysisRequest:
    """Request for sentiment analysis.
    
    Attributes:
        text: Text to analyze for sentiment.
        language: Language code (default: en).
    """

    text: str
    language: str = "en"


@dataclass
class SentimentAnalysisResult:
    """Result of sentiment analysis.
    
    Attributes:
        label: Sentiment label (positive, negative, neutral).
        score: Sentiment score (-1.0 to 1.0, where -1.0 is most negative, 1.0 is most positive).
        confidence: Confidence score (0.0 to 1.0).
        text: Original text analyzed.
        model: Model used for analysis.
    """

    label: SentimentLabel
    score: float
    confidence: float
    text: str
    model: str


class SentimentAnalysisError(Exception):
    """Error during sentiment analysis."""

    pass


class SentimentAnalysisService:
    """Service for analyzing text sentiment using Ollama."""

    def __init__(self, base_url: str | None = None) -> None:
        """
        Initialize sentiment analysis service.

        Args:
            base_url: Ollama base URL (default: http://localhost:11434)
        """
        self.base_url = (base_url or getattr(settings, "ollama_base_url", "http://localhost:11434")).rstrip("/")

    def analyze_sentiment(self, request: SentimentAnalysisRequest) -> SentimentAnalysisResult:
        """
        Analyze sentiment of text using Ollama.

        Args:
            request: Sentiment analysis request

        Returns:
            SentimentAnalysisResult with sentiment label, score, and confidence

        Raises:
            SentimentAnalysisError: If analysis fails
        """
        # Build sentiment analysis prompt
        prompt = self._build_sentiment_prompt(request.text, request.language)

        # Prepare Ollama API request
        payload: dict[str, Any] = {
            "model": "llama3:8b",  # Use default model
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature for consistent classification
                "num_predict": 50,  # Short response for classification
            },
        }

        # Call Ollama API
        url = f"{self.base_url}/api/generate"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.RequestError as exc:
            raise SentimentAnalysisError(f"Unable to reach Ollama at {self.base_url}: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise SentimentAnalysisError(f"Ollama API error: {exc.response.status_code} {exc.response.text}") from exc
        except Exception as exc:
            raise SentimentAnalysisError(f"Unexpected error during sentiment analysis: {exc}") from exc

        # Extract generated response
        generated_text = data.get("response", "").strip().lower()
        if not generated_text:
            raise SentimentAnalysisError("Ollama returned empty response")

        # Parse sentiment from response
        label, score, confidence = self._parse_sentiment_response(generated_text)

        return SentimentAnalysisResult(
            label=label,
            score=score,
            confidence=confidence,
            text=request.text,
            model="llama3:8b",
        )

    def _build_sentiment_prompt(self, text: str, language: str) -> str:
        """
        Build sentiment analysis prompt.

        Args:
            text: Text to analyze
            language: Language code

        Returns:
            Formatted prompt for sentiment analysis
        """
        return f"""Analyze the sentiment of the following text and respond with ONLY a JSON object in this exact format:
{{
  "label": "positive|negative|neutral",
  "score": -1.0 to 1.0,
  "confidence": 0.0 to 1.0
}}

Text to analyze:
{text}

Respond with ONLY the JSON object, no additional text."""

    def _parse_sentiment_response(self, response: str) -> tuple[SentimentLabel, float, float]:
        """
        Parse sentiment from Ollama response.

        Args:
            response: Raw response from Ollama

        Returns:
            Tuple of (label, score, confidence)

        Raises:
            SentimentAnalysisError: If parsing fails
        """
        import json
        import re

        # Try to extract JSON from response
        json_match = re.search(r"\{[^}]+\}", response)
        if json_match:
            try:
                data = json.loads(json_match.group())
                label_str = data.get("label", "neutral").lower()
                score = float(data.get("score", 0.0))
                confidence = float(data.get("confidence", 0.5))

                # Clamp values
                score = max(-1.0, min(1.0, score))
                confidence = max(0.0, min(1.0, confidence))

                # Map label
                if "positive" in label_str:
                    label = SentimentLabel.POSITIVE
                elif "negative" in label_str:
                    label = SentimentLabel.NEGATIVE
                else:
                    label = SentimentLabel.NEUTRAL

                return (label, score, confidence)
            except (json.JSONDecodeError, ValueError, KeyError) as exc:
                logger.warning(f"Failed to parse JSON from response: {exc}, response: {response}")

        # Fallback: simple keyword-based analysis
        return self._fallback_sentiment_analysis(response)

    def _fallback_sentiment_analysis(self, text: str) -> tuple[SentimentLabel, float, float]:
        """
        Fallback sentiment analysis using keyword matching.

        Args:
            text: Text to analyze

        Returns:
            Tuple of (label, score, confidence)
        """
        text_lower = text.lower()

        # Positive keywords
        positive_keywords = ["positive", "good", "great", "excellent", "love", "happy", "amazing", "wonderful", "fantastic"]
        # Negative keywords
        negative_keywords = ["negative", "bad", "terrible", "hate", "sad", "awful", "horrible", "disappointed"]

        positive_count = sum(1 for keyword in positive_keywords if keyword in text_lower)
        negative_count = sum(1 for keyword in negative_keywords if keyword in text_lower)

        if positive_count > negative_count:
            return (SentimentLabel.POSITIVE, 0.6, 0.7)
        elif negative_count > positive_count:
            return (SentimentLabel.NEGATIVE, -0.6, 0.7)
        else:
            return (SentimentLabel.NEUTRAL, 0.0, 0.5)
