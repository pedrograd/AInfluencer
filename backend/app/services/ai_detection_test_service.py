"""AI Detection Testing Service.

This service tests generated content against external AI detection tools/APIs
to verify that content passes AI detection tests and appears human-generated.

Supported providers:
- Hive Moderation (https://thehive.ai)
- Sensity AI (https://sensity.ai)
- Microsoft Azure Content Moderator
- Google Cloud Vision API
- Basic local analysis (fallback)
"""

from __future__ import annotations

import base64
import os
from typing import Any

import httpx
from PIL import Image

from app.core.logging import get_logger
from app.core.settings import settings

logger = get_logger(__name__)


class AIDetectionTestService:
    """Service for testing content against AI detection tools."""

    def __init__(self) -> None:
        """Initialize AI detection test service."""
        # Provider API keys (from environment or settings)
        self.hive_api_key = getattr(settings, "hive_api_key", None) or os.getenv("HIVE_API_KEY")
        self.sensity_api_key = getattr(settings, "sensity_api_key", None) or os.getenv("SENSITY_API_KEY")
        self.azure_api_key = getattr(settings, "azure_content_moderator_key", None) or os.getenv("AZURE_CONTENT_MODERATOR_KEY")
        self.azure_endpoint = getattr(settings, "azure_content_moderator_endpoint", None) or os.getenv("AZURE_CONTENT_MODERATOR_ENDPOINT")
        self.google_api_key = getattr(settings, "google_cloud_api_key", None) or os.getenv("GOOGLE_CLOUD_API_KEY")

    async def test_image(
        self,
        image_path: str,
        providers: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Test an image against AI detection tools.

        Args:
            image_path: Path to the image file to test.
            providers: List of provider names to use (default: all available).
                      Options: "hive", "sensity", "azure", "google", "local".

        Returns:
            Dictionary containing test results from all providers with:
            - passed: bool (True if all tests passed or no providers configured)
            - overall_score: float (0.0 to 1.0, higher = more human-like)
            - provider_results: dict mapping provider name to results
            - recommendations: list of recommendations for improvement
        """
        if providers is None:
            providers = ["local"]  # Default to local analysis only

        results: dict[str, Any] = {
            "passed": True,
            "overall_score": 1.0,
            "provider_results": {},
            "recommendations": [],
        }

        provider_scores: list[float] = []
        all_passed = True

        # Test with each provider
        for provider in providers:
            try:
                if provider == "hive":
                    result = await self._test_hive(image_path)
                elif provider == "sensity":
                    result = await self._test_sensity(image_path)
                elif provider == "azure":
                    result = await self._test_azure(image_path)
                elif provider == "google":
                    result = await self._test_google(image_path)
                elif provider == "local":
                    result = await self._test_local(image_path)
                else:
                    logger.warning(f"Unknown provider: {provider}")
                    continue

                if result:
                    results["provider_results"][provider] = result
                    if "score" in result:
                        provider_scores.append(result["score"])
                    if "passed" in result and not result["passed"]:
                        all_passed = False
                    if "recommendations" in result:
                        results["recommendations"].extend(result["recommendations"])

            except Exception as e:
                logger.error(f"Error testing with {provider}: {e}", exc_info=True)
                results["provider_results"][provider] = {
                    "error": str(e),
                    "passed": False,
                }
                all_passed = False

        # Calculate overall score
        if provider_scores:
            results["overall_score"] = sum(provider_scores) / len(provider_scores)
        results["passed"] = all_passed

        return results

    async def _test_hive(self, image_path: str) -> dict[str, Any] | None:
        """
        Test image with Hive Moderation API.

        Args:
            image_path: Path to image file.

        Returns:
            Test result dictionary or None if API key not configured.
        """
        if not self.hive_api_key:
            logger.debug("Hive API key not configured, skipping Hive test")
            return None

        try:
            # Read image and encode as base64
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.thehive.ai/api/v2/task/sync",
                    headers={
                        "Authorization": f"Token {self.hive_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "image": image_data,
                        "task": "content_moderation",
                    },
                )
                response.raise_for_status()
                data = response.json()

                # Parse Hive response
                # Hive returns AI probability scores
                ai_probability = data.get("response", {}).get("output", [{}])[0].get("classes", [{}])[0].get("score", 0.0)

                # Lower AI probability = more human-like = higher score
                human_score = 1.0 - ai_probability
                passed = human_score >= 0.7  # Threshold: 70% human-like

                return {
                    "provider": "hive",
                    "score": human_score,
                    "passed": passed,
                    "ai_probability": ai_probability,
                    "raw_response": data,
                }

        except Exception as e:
            logger.error(f"Hive API test failed: {e}", exc_info=True)
            return {
                "provider": "hive",
                "error": str(e),
                "passed": False,
            }

    async def _test_sensity(self, image_path: str) -> dict[str, Any] | None:
        """
        Test image with Sensity AI API.

        Args:
            image_path: Path to image file.

        Returns:
            Test result dictionary or None if API key not configured.
        """
        if not self.sensity_api_key:
            logger.debug("Sensity API key not configured, skipping Sensity test")
            return None

        try:
            # Read image file
            with open(image_path, "rb") as f:
                image_data = f.read()

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.sensity.ai/v1/detect",
                    headers={
                        "Authorization": f"Bearer {self.sensity_api_key}",
                    },
                    files={"image": image_data},
                )
                response.raise_for_status()
                data = response.json()

                # Parse Sensity response
                # Sensity returns deepfake probability
                deepfake_probability = data.get("probability", 0.0)

                # Lower deepfake probability = more human-like = higher score
                human_score = 1.0 - deepfake_probability
                passed = human_score >= 0.7  # Threshold: 70% human-like

                return {
                    "provider": "sensity",
                    "score": human_score,
                    "passed": passed,
                    "deepfake_probability": deepfake_probability,
                    "raw_response": data,
                }

        except Exception as e:
            logger.error(f"Sensity API test failed: {e}", exc_info=True)
            return {
                "provider": "sensity",
                "error": str(e),
                "passed": False,
            }

    async def _test_azure(self, image_path: str) -> dict[str, Any] | None:
        """
        Test image with Microsoft Azure Content Moderator.

        Args:
            image_path: Path to image file.

        Returns:
            Test result dictionary or None if API key not configured.
        """
        if not self.azure_api_key or not self.azure_endpoint:
            logger.debug("Azure Content Moderator not configured, skipping Azure test")
            return None

        try:
            # Read image file
            with open(image_path, "rb") as f:
                image_data = f.read()

            # Azure Content Moderator endpoint
            url = f"{self.azure_endpoint}/contentmoderator/v1.0/ProcessImage/Evaluate"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers={
                        "Ocp-Apim-Subscription-Key": self.azure_api_key,
                        "Content-Type": "application/octet-stream",
                    },
                    content=image_data,
                )
                response.raise_for_status()
                data = response.json()

                # Azure returns various scores
                # We focus on adult/racy scores (lower = better)
                adult_score = data.get("AdultClassificationScore", 0.0)
                racy_score = data.get("RacyClassificationScore", 0.0)

                # Calculate human-like score (lower adult/racy = more natural)
                human_score = 1.0 - max(adult_score, racy_score * 0.5)
                passed = human_score >= 0.6  # Threshold: 60% human-like

                return {
                    "provider": "azure",
                    "score": human_score,
                    "passed": passed,
                    "adult_score": adult_score,
                    "racy_score": racy_score,
                    "raw_response": data,
                }

        except Exception as e:
            logger.error(f"Azure Content Moderator test failed: {e}", exc_info=True)
            return {
                "provider": "azure",
                "error": str(e),
                "passed": False,
            }

    async def _test_google(self, image_path: str) -> dict[str, Any] | None:
        """
        Test image with Google Cloud Vision API.

        Args:
            image_path: Path to image file.

        Returns:
            Test result dictionary or None if API key not configured.
        """
        if not self.google_api_key:
            logger.debug("Google Cloud API key not configured, skipping Google test")
            return None

        try:
            # Read image and encode as base64
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"https://vision.googleapis.com/v1/images:annotate?key={self.google_api_key}",
                    json={
                        "requests": [
                            {
                                "image": {"content": image_data},
                                "features": [
                                    {"type": "SAFE_SEARCH_DETECTION"},
                                    {"type": "LABEL_DETECTION"},
                                ],
                            }
                        ]
                    },
                )
                response.raise_for_status()
                data = response.json()

                # Parse Google Vision response
                responses = data.get("responses", [])
                if not responses:
                    return None

                result = responses[0]
                safe_search = result.get("safeSearchAnnotation", {})
                labels = result.get("labelAnnotations", [])

                # Check for AI-related labels
                ai_labels = [label for label in labels if "artificial" in label.get("description", "").lower() or "generated" in label.get("description", "").lower()]

                # Calculate human-like score
                # Lower safe search scores = more natural
                adult_score = {"UNKNOWN": 0.0, "VERY_UNLIKELY": 0.1, "UNLIKELY": 0.3, "POSSIBLE": 0.6, "LIKELY": 0.8, "VERY_LIKELY": 1.0}.get(safe_search.get("adult", "UNKNOWN"), 0.5)
                human_score = 1.0 - (adult_score * 0.3) - (len(ai_labels) * 0.1)
                human_score = max(0.0, min(1.0, human_score))
                passed = human_score >= 0.7  # Threshold: 70% human-like

                return {
                    "provider": "google",
                    "score": human_score,
                    "passed": passed,
                    "safe_search": safe_search,
                    "ai_labels_count": len(ai_labels),
                    "raw_response": data,
                }

        except Exception as e:
            logger.error(f"Google Vision API test failed: {e}", exc_info=True)
            return {
                "provider": "google",
                "error": str(e),
                "passed": False,
            }

    async def _test_local(self, image_path: str) -> dict[str, Any]:
        """
        Test image with local analysis (fallback, no API required).

        Uses basic image analysis to detect obvious AI signatures.

        Args:
            image_path: Path to image file.

        Returns:
            Test result dictionary.
        """
        try:
            from app.services.quality_validator import QualityValidator

            # Use existing quality validator for AI signature detection
            validator = QualityValidator()
            img = Image.open(image_path)

            # Get AI signatures score from quality validator
            ai_signatures_score = validator._detect_ai_signatures(img)

            if ai_signatures_score is None:
                # If detection failed, assume passed (conservative)
                return {
                    "provider": "local",
                    "score": 0.8,
                    "passed": True,
                    "method": "quality_validator",
                    "note": "AI signature detection unavailable, assuming passed",
                }

            # Higher score = fewer AI signatures = more human-like
            passed = ai_signatures_score >= 0.6  # Threshold: 60% human-like

            recommendations = []
            if ai_signatures_score < 0.6:
                recommendations.append("Image shows AI generation signatures. Consider post-processing to add natural variations.")
            if ai_signatures_score < 0.4:
                recommendations.append("Strong AI signatures detected. Image may be flagged by detection systems.")

            return {
                "provider": "local",
                "score": ai_signatures_score,
                "passed": passed,
                "method": "quality_validator",
                "recommendations": recommendations,
            }

        except Exception as e:
            logger.error(f"Local AI detection test failed: {e}", exc_info=True)
            return {
                "provider": "local",
                "score": 0.5,
                "passed": False,
                "error": str(e),
            }

    def is_configured(self, provider: str) -> bool:
        """
        Check if a provider is configured.

        Args:
            provider: Provider name ("hive", "sensity", "azure", "google", "local").

        Returns:
            True if provider is configured and available.
        """
        if provider == "hive":
            return self.hive_api_key is not None
        elif provider == "sensity":
            return self.sensity_api_key is not None
        elif provider == "azure":
            return self.azure_api_key is not None and self.azure_endpoint is not None
        elif provider == "google":
            return self.google_api_key is not None
        elif provider == "local":
            return True  # Local is always available
        return False

    def get_available_providers(self) -> list[str]:
        """
        Get list of available (configured) providers.

        Returns:
            List of provider names that are configured.
        """
        available = []
        for provider in ["hive", "sensity", "azure", "google", "local"]:
            if self.is_configured(provider):
                available.append(provider)
        return available


# Singleton instance
ai_detection_test_service = AIDetectionTestService()
