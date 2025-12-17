"""Live interaction simulation service for continuous real-time engagement updates."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.core.logging import get_logger
from app.models.post import Post
from app.services.follower_interaction_simulation_service import FollowerInteractionSimulationService

logger = get_logger(__name__)


class LiveInteractionSimulationService:
    """Service for continuously simulating live interactions for active posts.
    
    This service runs as a background task and periodically updates engagement
    for active posts (published within the last 48 hours), simulating how real
    social media engagement gradually increases over time.
    
    Unlike the one-time batch simulation, this service:
    - Continuously updates engagement for active posts
    - Gradually increases engagement counts over time
    - Respects engagement decay curves (most engagement in first 24-48 hours)
    - Can be started/stopped via API
    """

    def __init__(self) -> None:
        """Initialize live interaction simulation service."""
        self._is_running = False
        self._task: Optional[asyncio.Task[None]] = None
        self._interval_seconds = 300  # Default: update every 5 minutes
        self._max_post_age_hours = 48  # Only process posts published within 48 hours

    @property
    def is_running(self) -> bool:
        """Check if live simulation is currently running."""
        return self._is_running and self._task is not None and not self._task.done()

    @property
    def interval_seconds(self) -> int:
        """Get current update interval in seconds."""
        return self._interval_seconds

    def set_interval(self, seconds: int) -> None:
        """Set update interval in seconds.
        
        Args:
            seconds: Update interval in seconds (minimum 60, maximum 3600)
        """
        if seconds < 60:
            raise ValueError("Interval must be at least 60 seconds")
        if seconds > 3600:
            raise ValueError("Interval must be at most 3600 seconds (1 hour)")
        self._interval_seconds = seconds
        logger.info(f"Live interaction simulation interval set to {seconds} seconds")

    def set_max_post_age(self, hours: int) -> None:
        """Set maximum post age for processing.
        
        Args:
            hours: Maximum age in hours (default: 48)
        """
        if hours < 1:
            raise ValueError("Max post age must be at least 1 hour")
        if hours > 168:  # 1 week
            raise ValueError("Max post age must be at most 168 hours (1 week)")
        self._max_post_age_hours = hours
        logger.info(f"Live interaction simulation max post age set to {hours} hours")

    async def _simulation_loop(self) -> None:
        """Background task loop that continuously updates engagement for active posts."""
        logger.info("Live interaction simulation loop started")
        
        while self._is_running:
            # Create a new database session for this cycle
            async with async_session_maker() as db:
                try:
                    # Calculate cutoff time for active posts
                    cutoff_time = datetime.now() - timedelta(hours=self._max_post_age_hours)
                    
                    # Find all active published posts
                    query = (
                        select(Post)
                        .where(
                            and_(
                                Post.status == "published",
                                Post.published_at >= cutoff_time,
                                Post.published_at.isnot(None),
                            )
                        )
                        .order_by(Post.published_at.desc())
                    )
                    
                    result = await db.execute(query)
                    posts = result.scalars().all()
                    
                    if posts:
                        logger.debug(f"Processing {len(posts)} active posts for live interaction simulation")
                        
                        # Create simulation service with this session
                        simulation_service = FollowerInteractionSimulationService(db)
                        
                        # Process each post
                        updated_count = 0
                        for post in posts:
                            try:
                                # Calculate hours since post was published
                                if post.published_at:
                                    hours_since_post = (
                                        datetime.now(post.published_at.tzinfo) - post.published_at
                                    ).total_seconds() / 3600
                                    
                                    # Only update if post is still in active engagement window
                                    if hours_since_post <= self._max_post_age_hours:
                                        # Use the existing simulation service to calculate
                                        # realistic engagement based on current post age
                                        await simulation_service.simulate_interactions_for_post(
                                            post.id
                                        )
                                        updated_count += 1
                            except Exception as e:
                                logger.error(
                                    f"Error updating engagement for post {post.id}: {e}",
                                    exc_info=True,
                                )
                        
                        if updated_count > 0:
                            logger.info(
                                f"Live interaction simulation: updated engagement for {updated_count} posts"
                            )
                    else:
                        logger.debug("No active posts to process for live interaction simulation")
                    
                except Exception as exc:
                    logger.error(
                        f"Error in live interaction simulation loop: {exc}",
                        exc_info=True,
                    )
            
            # Wait for next interval (outside of db session context)
            try:
                await asyncio.sleep(self._interval_seconds)
            except asyncio.CancelledError:
                logger.info("Live interaction simulation loop cancelled")
                break
        
        logger.info("Live interaction simulation loop stopped")
        self._is_running = False

    async def start(self) -> None:
        """Start the live interaction simulation background task."""
        if self.is_running:
            logger.warning("Live interaction simulation is already running")
            return
        
        self._is_running = True
        loop = asyncio.get_event_loop()
        self._task = loop.create_task(self._simulation_loop())
        logger.info(
            f"Live interaction simulation started (interval: {self._interval_seconds}s, "
            f"max post age: {self._max_post_age_hours}h)"
        )

    async def stop(self) -> None:
        """Stop the live interaction simulation background task."""
        if not self.is_running:
            logger.warning("Live interaction simulation is not running")
            return
        
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        self._task = None
        logger.info("Live interaction simulation stopped")

    async def get_status(self) -> dict:
        """Get current status of live interaction simulation.
        
        Returns:
            Dict with status information including is_running, interval, etc.
        """
        return {
            "is_running": self.is_running,
            "interval_seconds": self._interval_seconds,
            "max_post_age_hours": self._max_post_age_hours,
        }


# Global instance for managing live interaction simulation
_live_simulation_service: Optional[LiveInteractionSimulationService] = None


def get_live_simulation_service() -> LiveInteractionSimulationService:
    """Get or create global live interaction simulation service instance.
    
    Returns:
        Live interaction simulation service instance
    """
    global _live_simulation_service
    if _live_simulation_service is None:
        _live_simulation_service = LiveInteractionSimulationService()
    return _live_simulation_service
