"""Behavior randomization service for automation.

This service provides behavior randomization to make automation appear more natural
and avoid detection by platform algorithms. It complements HumanTimingService by
randomizing engagement patterns, selective engagement, and activity variations.
"""

from __future__ import annotations

import random
from typing import Literal

from app.core.logging import get_logger

logger = get_logger(__name__)


class BehaviorRandomizationService:
    """Service for randomizing automation behavior patterns."""

    def __init__(self) -> None:
        """Initialize behavior randomization service."""
        pass

    def should_engage_with_post(
        self,
        engagement_rate: float = 0.7,
        post_quality_score: float | None = None,
    ) -> bool:
        """
        Determine if we should engage with a post (selective engagement).

        Not every post should be engaged with - humans are selective. This adds
        natural variation to engagement patterns.

        Args:
            engagement_rate: Base probability of engaging (0.0 to 1.0, default: 0.7).
            post_quality_score: Optional quality score (0.0 to 1.0) to influence decision.

        Returns:
            True if should engage, False otherwise.
        """
        # Adjust engagement rate based on post quality if provided
        if post_quality_score is not None:
            # Higher quality posts are more likely to be engaged with
            adjusted_rate = engagement_rate * (0.5 + post_quality_score * 0.5)
            adjusted_rate = min(1.0, max(0.0, adjusted_rate))
        else:
            adjusted_rate = engagement_rate

        should_engage = random.random() < adjusted_rate
        if not should_engage:
            logger.debug(
                f"Skipping engagement (rate: {adjusted_rate:.2f}, quality: {post_quality_score})"
            )
        return should_engage

    def get_engagement_type(
        self,
        available_types: list[Literal["like", "comment", "share", "follow"]] | None = None,
        like_probability: float = 0.7,
        comment_probability: float = 0.2,
        share_probability: float = 0.08,
        follow_probability: float = 0.02,
    ) -> str:
        """
        Randomize engagement type (like, comment, share, follow).

        Humans don't always like - they mix engagement types. This creates natural
        variation in engagement patterns.

        Args:
            available_types: List of available engagement types. If None, uses all.
            like_probability: Probability of choosing "like" (default: 0.7).
            comment_probability: Probability of choosing "comment" (default: 0.2).
            share_probability: Probability of choosing "share" (default: 0.08).
            follow_probability: Probability of choosing "follow" (default: 0.02).

        Returns:
            Engagement type string.
        """
        if available_types is None:
            available_types = ["like", "comment", "share", "follow"]

        # Normalize probabilities to sum to 1.0
        total = like_probability + comment_probability + share_probability + follow_probability
        if total > 0:
            like_probability /= total
            comment_probability /= total
            share_probability /= total
            follow_probability /= total

        # Build weighted choices
        choices = []
        weights = []

        if "like" in available_types:
            choices.append("like")
            weights.append(like_probability)
        if "comment" in available_types:
            choices.append("comment")
            weights.append(comment_probability)
        if "share" in available_types:
            choices.append("share")
            weights.append(share_probability)
        if "follow" in available_types:
            choices.append("follow")
            weights.append(follow_probability)

        if not choices:
            return "like"  # Default fallback

        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]

        engagement_type = random.choices(choices, weights=weights, k=1)[0]
        logger.debug(f"Selected engagement type: {engagement_type}")
        return engagement_type

    def should_follow_back(
        self,
        follow_back_rate: float = 0.6,
        account_quality_score: float | None = None,
    ) -> bool:
        """
        Determine if we should follow back an account (selective following).

        Humans don't follow everyone back - they're selective. This creates natural
        following patterns.

        Args:
            follow_back_rate: Base probability of following back (0.0 to 1.0, default: 0.6).
            account_quality_score: Optional quality score (0.0 to 1.0) to influence decision.

        Returns:
            True if should follow back, False otherwise.
        """
        # Adjust follow-back rate based on account quality if provided
        if account_quality_score is not None:
            # Higher quality accounts are more likely to be followed back
            adjusted_rate = follow_back_rate * (0.5 + account_quality_score * 0.5)
            adjusted_rate = min(1.0, max(0.0, adjusted_rate))
        else:
            adjusted_rate = follow_back_rate

        should_follow = random.random() < adjusted_rate
        if not should_follow:
            logger.debug(
                f"Skipping follow-back (rate: {adjusted_rate:.2f}, quality: {account_quality_score})"
            )
        return should_follow

    def get_activity_level(self, base_level: float = 1.0) -> float:
        """
        Get randomized activity level multiplier.

        Activity levels vary naturally - some days are more active than others.
        This creates natural variation in daily activity patterns.

        Args:
            base_level: Base activity level (default: 1.0).

        Returns:
            Activity level multiplier (0.5 to 1.5).
        """
        # Random variation: ±50% of base level
        variation = random.uniform(0.5, 1.5)
        activity_level = base_level * variation
        logger.debug(f"Activity level: {activity_level:.2f} (base: {base_level:.2f})")
        return activity_level

    def should_take_break(self, break_probability: float = 0.05) -> bool:
        """
        Determine if we should take a random break (inactivity period).

        Humans take breaks - coffee, lunch, etc. This adds natural inactivity periods.

        Args:
            break_probability: Probability of taking a break (default: 0.05 = 5%).

        Returns:
            True if should take a break, False otherwise.
        """
        should_break = random.random() < break_probability
        if should_break:
            logger.debug("Taking random break (human-like behavior)")
        return should_break

    def get_break_duration(self, min_minutes: float = 15.0, max_minutes: float = 120.0) -> float:
        """
        Get randomized break duration.

        Args:
            min_minutes: Minimum break duration in minutes (default: 15).
            max_minutes: Maximum break duration in minutes (default: 120).

        Returns:
            Break duration in minutes.
        """
        duration = random.uniform(min_minutes, max_minutes)
        logger.debug(f"Break duration: {duration:.1f} minutes")
        return duration

    def should_simulate_error(self, error_probability: float = 0.01) -> bool:
        """
        Determine if we should simulate a human error (typo, correction, etc.).

        Humans make occasional mistakes. This adds natural error patterns (very rare).

        Args:
            error_probability: Probability of simulating an error (default: 0.01 = 1%).

        Returns:
            True if should simulate error, False otherwise.
        """
        should_error = random.random() < error_probability
        if should_error:
            logger.debug("Simulating human error (typo/correction)")
        return should_error

    def get_engagement_batch_size(
        self,
        min_size: int = 1,
        max_size: int = 10,
        base_size: int = 5,
    ) -> int:
        """
        Get randomized engagement batch size.

        Humans don't engage in perfectly consistent batches - there's natural variation.

        Args:
            min_size: Minimum batch size (default: 1).
            max_size: Maximum batch size (default: 10).
            base_size: Base batch size (default: 5).

        Returns:
            Randomized batch size.
        """
        # Random variation around base size
        variation = random.randint(-2, 2)
        batch_size = max(min_size, min(max_size, base_size + variation))
        logger.debug(f"Engagement batch size: {batch_size} (base: {base_size})")
        return batch_size

    def get_comment_length(
        self,
        min_words: int = 3,
        max_words: int = 20,
        average_words: int = 8,
    ) -> int:
        """
        Get randomized comment length in words.

        Comments vary in length naturally - some are short, some are longer.

        Args:
            min_words: Minimum comment length in words (default: 3).
            max_words: Maximum comment length in words (default: 20).
            average_words: Average comment length in words (default: 8).

        Returns:
            Comment length in words.
        """
        # Use normal distribution around average, clamped to min/max
        # Simplified: use uniform distribution with bias toward average
        if random.random() < 0.7:  # 70% chance of being near average
            length = random.randint(
                max(min_words, average_words - 3),
                min(max_words, average_words + 3),
            )
        else:
            length = random.randint(min_words, max_words)

        logger.debug(f"Comment length: {length} words (avg: {average_words})")
        return length

    def get_engagement_delay_variation(self, base_delay: float, variation_percent: float = 0.3) -> float:
        """
        Add random variation to engagement delays.

        Args:
            base_delay: Base delay in seconds.
            variation_percent: Variation percentage (default: 0.3 = ±30%).

        Returns:
            Delay with random variation.
        """
        variation = random.uniform(1.0 - variation_percent, 1.0 + variation_percent)
        varied_delay = base_delay * variation
        logger.debug(f"Delay variation: {varied_delay:.1f}s (base: {base_delay:.1f}s)")
        return varied_delay
