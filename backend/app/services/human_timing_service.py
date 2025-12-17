"""Human-like timing patterns service for automation.

This service provides human-like delays and activity patterns to make automation
appear more natural and avoid detection by platform algorithms.
"""

from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class HumanTimingService:
    """Service for generating human-like timing patterns and delays."""

    def __init__(self) -> None:
        """Initialize human timing service."""
        pass

    def get_human_delay(
        self,
        min_seconds: float = 30.0,
        max_seconds: float = 300.0,
        include_breaks: bool = True,
        respect_sleep_hours: bool = True,
    ) -> float:
        """
        Calculate a human-like delay between actions.

        Args:
            min_seconds: Minimum delay in seconds (default: 30s).
            max_seconds: Maximum delay in seconds (default: 5min).
            include_breaks: Whether to include occasional longer breaks (coffee, lunch).
            respect_sleep_hours: Whether to respect sleep patterns (less activity at night).

        Returns:
            Delay in seconds.
        """
        # Base delay: random between min and max
        base = random.uniform(min_seconds, max_seconds)

        # Add occasional longer breaks (coffee, lunch) - 10% chance
        if include_breaks and random.random() < 0.1:
            break_duration = random.uniform(600, 3600)  # 10min to 1hr
            base += break_duration
            logger.debug(f"Adding break delay: {break_duration:.1f}s (total: {base:.1f}s)")

        # Add sleep patterns (less activity at night) - 2am to 6am
        if respect_sleep_hours:
            hour = datetime.now().hour
            if 2 <= hour <= 6:  # 2am-6am
                sleep_multiplier = random.uniform(2, 5)  # Much slower
                base *= sleep_multiplier
                logger.debug(
                    f"Sleep hours detected (hour: {hour}), applying multiplier: {sleep_multiplier:.1f} (total: {base:.1f}s)"
                )

        return base

    def get_activity_probability(self, hour: Optional[int] = None) -> float:
        """
        Get probability of activity at a given hour (0.0 to 1.0).

        Higher probability during peak hours (9am-9pm), lower during sleep hours (2am-6am).

        Args:
            hour: Hour of day (0-23). If None, uses current hour.

        Returns:
            Activity probability (0.0 to 1.0).
        """
        if hour is None:
            hour = datetime.now().hour

        # Peak hours: 9am-9pm (higher activity)
        if 9 <= hour <= 21:
            return random.uniform(0.7, 1.0)

        # Evening: 7pm-9pm (very active)
        if 19 <= hour <= 21:
            return random.uniform(0.8, 1.0)

        # Morning: 7am-9am (moderate activity)
        if 7 <= hour < 9:
            return random.uniform(0.5, 0.8)

        # Sleep hours: 2am-6am (very low activity)
        if 2 <= hour <= 6:
            return random.uniform(0.1, 0.3)

        # Late night: 10pm-2am (low activity)
        if hour >= 22 or hour < 2:
            return random.uniform(0.2, 0.5)

        # Default: moderate activity
        return random.uniform(0.4, 0.7)

    def should_skip_action(self, hour: Optional[int] = None) -> bool:
        """
        Determine if an action should be skipped based on activity patterns.

        Actions are more likely to be skipped during sleep hours or low-activity periods.

        Args:
            hour: Hour of day (0-23). If None, uses current hour.

        Returns:
            True if action should be skipped, False otherwise.
        """
        probability = self.get_activity_probability(hour)
        # Skip if random value is above probability threshold
        return random.random() > probability

    def get_weekend_multiplier(self) -> float:
        """
        Get activity multiplier for weekends (slightly less activity).

        Returns:
            Multiplier (0.8 to 1.0 for weekends, 1.0 for weekdays).
        """
        weekday = datetime.now().weekday()  # 0=Monday, 6=Sunday
        if weekday >= 5:  # Saturday or Sunday
            return random.uniform(0.8, 1.0)
        return 1.0

    async def wait_human_delay(
        self,
        min_seconds: float = 30.0,
        max_seconds: float = 300.0,
        include_breaks: bool = True,
        respect_sleep_hours: bool = True,
    ) -> None:
        """
        Wait for a human-like delay (async version).

        Args:
            min_seconds: Minimum delay in seconds (default: 30s).
            max_seconds: Maximum delay in seconds (default: 5min).
            include_breaks: Whether to include occasional longer breaks.
            respect_sleep_hours: Whether to respect sleep patterns.
        """
        delay = self.get_human_delay(
            min_seconds=min_seconds,
            max_seconds=max_seconds,
            include_breaks=include_breaks,
            respect_sleep_hours=respect_sleep_hours,
        )
        logger.debug(f"Waiting human-like delay: {delay:.1f}s")
        await asyncio.sleep(delay)

    def get_optimal_post_time(
        self,
        platform: str,
        timezone_offset_hours: int = 0,
    ) -> datetime:
        """
        Calculate optimal posting time for a platform.

        Args:
            platform: Platform name (instagram, twitter, facebook, etc.).
            timezone_offset_hours: Timezone offset in hours from UTC.

        Returns:
            Optimal posting datetime.
        """
        now = datetime.now()
        hour = (now.hour + timezone_offset_hours) % 24

        # Platform-specific optimal hours
        optimal_hours = {
            "instagram": [(11, 13), (19, 21)],  # 11am-1pm, 7pm-9pm
            "twitter": [(8, 10), (19, 21)],  # 8am-10am, 7pm-9pm
            "facebook": [(13, 15)],  # 1pm-3pm
            "telegram": None,  # Anytime
            "youtube": [(14, 16), (20, 22)],  # 2pm-4pm, 8pm-10pm
            "tiktok": [(19, 21)],  # 7pm-9pm
        }

        platform_hours = optimal_hours.get(platform.lower())
        if not platform_hours:
            # Default: use current time with small random variation
            variation_hours = random.randint(-2, 2)
            return now + timedelta(hours=variation_hours)

        # Find the next optimal time window
        for start_hour, end_hour in platform_hours:
            if start_hour <= hour < end_hour:
                # Within optimal window, add small random variation
                variation_minutes = random.randint(0, 30)
                return now + timedelta(minutes=variation_minutes)

        # Not in optimal window, find next window
        next_window = platform_hours[0]
        next_hour = next_window[0]
        if hour >= next_window[1]:
            # Past this window, use next day
            days_ahead = 1
        else:
            days_ahead = 0

        target_datetime = now.replace(hour=next_hour, minute=0, second=0, microsecond=0)
        target_datetime += timedelta(days=days_ahead)
        variation_minutes = random.randint(0, 30)
        return target_datetime + timedelta(minutes=variation_minutes)

    def get_engagement_delay(self, action_type: str = "like") -> float:
        """
        Get delay specific to engagement actions.

        Different actions have different natural delays:
        - Likes: Quick (30s - 2min)
        - Comments: Slower (1min - 5min, thinking time)
        - Follows: Moderate (30s - 3min)

        Args:
            action_type: Type of engagement action (like, comment, follow).

        Returns:
            Delay in seconds.
        """
        if action_type == "like":
            return random.uniform(30, 120)  # 30s - 2min
        elif action_type == "comment":
            return random.uniform(60, 300)  # 1min - 5min (thinking time)
        elif action_type == "follow":
            return random.uniform(30, 180)  # 30s - 3min
        else:
            return self.get_human_delay()  # Default

    async def wait_engagement_delay(self, action_type: str = "like") -> None:
        """
        Wait for engagement-specific delay (async version).

        Args:
            action_type: Type of engagement action (like, comment, follow).
        """
        delay = self.get_engagement_delay(action_type)
        logger.debug(f"Waiting engagement delay for {action_type}: {delay:.1f}s")
        await asyncio.sleep(delay)
