"""Follower interaction simulation service for simulating realistic follower engagement."""

from __future__ import annotations

import random
import math
from datetime import datetime, timedelta
from uuid import UUID
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.post import Post
from app.models.platform_account import PlatformAccount

logger = get_logger(__name__)


class FollowerInteractionSimulationService:
    """Service for simulating realistic follower interactions with character posts.
    
    Simulates likes, comments, shares, and views based on:
    - Follower count
    - Platform-specific engagement rates
    - Post age (most engagement happens in first 24-48 hours)
    - Post type (reels/videos get more engagement than static posts)
    - Realistic timing patterns
    """

    # Platform-specific engagement rate ranges (as percentage of followers)
    # Format: (min_like_rate, max_like_rate, min_comment_rate, max_comment_rate, min_share_rate, max_share_rate)
    PLATFORM_ENGAGEMENT_RATES = {
        "instagram": {
            "post": (0.02, 0.08, 0.001, 0.005, 0.0005, 0.002),  # 2-8% likes, 0.1-0.5% comments, 0.05-0.2% shares
            "reel": (0.05, 0.15, 0.002, 0.008, 0.001, 0.004),  # Reels get more engagement
            "story": (0.10, 0.30, 0.005, 0.015, 0.0, 0.0),  # Stories: high view rate, no shares
        },
        "twitter": {
            "tweet": (0.01, 0.05, 0.002, 0.010, 0.001, 0.005),  # 1-5% likes, 0.2-1% comments, 0.1-0.5% shares
        },
        "facebook": {
            "post": (0.01, 0.06, 0.001, 0.004, 0.0005, 0.003),
        },
        "youtube": {
            "short": (0.02, 0.10, 0.001, 0.005, 0.0005, 0.002),
            "video": (0.01, 0.08, 0.002, 0.010, 0.001, 0.005),
        },
        "tiktok": {
            "video": (0.03, 0.12, 0.001, 0.006, 0.0005, 0.003),
        },
        "telegram": {
            "post": (0.05, 0.20, 0.002, 0.008, 0.001, 0.004),  # Telegram has higher engagement
        },
        "onlyfans": {
            "post": (0.15, 0.40, 0.010, 0.030, 0.0, 0.0),  # OnlyFans has very high engagement
            "message": (0.20, 0.50, 0.015, 0.040, 0.0, 0.0),
        },
    }

    # Default engagement rates if platform/type not found
    DEFAULT_ENGAGEMENT_RATES = (0.02, 0.08, 0.001, 0.005, 0.0005, 0.002)

    def __init__(self, db: AsyncSession) -> None:
        """Initialize follower interaction simulation service."""
        self.db = db

    def _get_engagement_rates(
        self, platform: str, post_type: Optional[str] = None
    ) -> tuple[float, float, float, float, float, float]:
        """Get engagement rate ranges for platform and post type.
        
        Args:
            platform: Platform name (instagram, twitter, etc.)
            post_type: Post type (post, reel, story, tweet, etc.)
            
        Returns:
            Tuple of (min_like_rate, max_like_rate, min_comment_rate, max_comment_rate, min_share_rate, max_share_rate)
        """
        platform_rates = self.PLATFORM_ENGAGEMENT_RATES.get(platform.lower(), {})
        
        # Try specific post type first
        if post_type and post_type.lower() in platform_rates:
            return platform_rates[post_type.lower()]
        
        # Try generic "post" type
        if "post" in platform_rates:
            return platform_rates["post"]
        
        # Use default rates
        return self.DEFAULT_ENGAGEMENT_RATES

    def _calculate_engagement_decay(self, hours_since_post: float) -> float:
        """Calculate engagement decay factor based on post age.
        
        Most engagement happens in first 24-48 hours, then decays exponentially.
        
        Args:
            hours_since_post: Hours since post was published
            
        Returns:
            Decay factor (0.0 to 1.0)
        """
        if hours_since_post <= 0:
            return 1.0
        
        # Exponential decay: 50% engagement in first 6 hours, 80% in first 24 hours, 95% in first 48 hours
        if hours_since_post <= 6:
            return 1.0 - (hours_since_post / 6) * 0.5
        elif hours_since_post <= 24:
            return 0.5 - ((hours_since_post - 6) / 18) * 0.3
        elif hours_since_post <= 48:
            return 0.2 - ((hours_since_post - 24) / 24) * 0.15
        else:
            # Very slow decay after 48 hours
            return max(0.05, 0.05 * math.exp(-(hours_since_post - 48) / 168))  # 1 week half-life

    def _calculate_realistic_engagement(
        self,
        follower_count: int,
        platform: str,
        post_type: Optional[str] = None,
        hours_since_post: float = 0.0,
    ) -> dict[str, int]:
        """Calculate realistic engagement counts.
        
        Args:
            follower_count: Number of followers
            platform: Platform name
            post_type: Post type
            hours_since_post: Hours since post was published
            
        Returns:
            Dict with likes, comments, shares, views counts
        """
        if follower_count == 0:
            return {"likes": 0, "comments": 0, "shares": 0, "views": 0}
        
        # Get engagement rate ranges
        (
            min_like_rate,
            max_like_rate,
            min_comment_rate,
            max_comment_rate,
            min_share_rate,
            max_share_rate,
        ) = self._get_engagement_rates(platform, post_type)
        
        # Calculate decay factor
        decay = self._calculate_engagement_decay(hours_since_post)
        
        # Calculate base engagement (before decay)
        like_rate = random.uniform(min_like_rate, max_like_rate)
        comment_rate = random.uniform(min_comment_rate, max_comment_rate)
        share_rate = random.uniform(min_share_rate, max_share_rate)
        
        # Apply decay
        like_rate *= decay
        comment_rate *= decay
        comment_rate *= decay  # Comments decay faster
        share_rate *= decay
        
        # Calculate counts
        likes = max(0, int(follower_count * like_rate))
        comments = max(0, int(follower_count * comment_rate))
        shares = max(0, int(follower_count * share_rate))
        
        # Views are typically higher than likes (not all viewers like)
        # Views = likes * multiplier (platform-specific)
        view_multipliers = {
            "instagram": {"post": 3.0, "reel": 5.0, "story": 1.2},
            "twitter": {"tweet": 2.5},
            "facebook": {"post": 2.0},
            "youtube": {"short": 4.0, "video": 3.0},
            "tiktok": {"video": 5.0},
            "telegram": {"post": 2.0},
            "onlyfans": {"post": 1.5, "message": 1.3},
        }
        
        multiplier = 2.0  # Default
        platform_multipliers = view_multipliers.get(platform.lower(), {})
        if post_type and post_type.lower() in platform_multipliers:
            multiplier = platform_multipliers[post_type.lower()]
        elif "post" in platform_multipliers:
            multiplier = platform_multipliers["post"]
        
        views = max(likes, int(likes * multiplier * decay))
        
        # Add some randomness to make it more realistic
        likes = max(0, int(likes * random.uniform(0.8, 1.2)))
        comments = max(0, int(comments * random.uniform(0.7, 1.3)))
        shares = max(0, int(shares * random.uniform(0.8, 1.2)))
        views = max(likes, int(views * random.uniform(0.9, 1.1)))
        
        return {
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "views": views,
        }

    async def simulate_interactions_for_post(
        self,
        post_id: UUID,
        override_engagement: Optional[dict[str, int]] = None,
    ) -> Post:
        """Simulate follower interactions for a specific post.
        
        Args:
            post_id: UUID of the post to simulate interactions for
            override_engagement: Optional dict with likes/comments/shares/views to set directly
            
        Returns:
            Updated Post object
            
        Raises:
            ValueError: If post not found
        """
        # Get post
        result = await self.db.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()
        
        if not post:
            raise ValueError(f"Post {post_id} not found")
        
        if post.status != "published" or not post.published_at:
            logger.debug(f"Post {post_id} not published yet, skipping simulation")
            return post
        
        # Get platform account to access follower count
        account_result = await self.db.execute(
            select(PlatformAccount).where(PlatformAccount.id == post.platform_account_id)
        )
        account = account_result.scalar_one_or_none()
        
        follower_count = account.follower_count if account else 0
        
        if override_engagement:
            # Use provided engagement values
            post.likes_count = override_engagement.get("likes", post.likes_count)
            post.comments_count = override_engagement.get("comments", post.comments_count)
            post.shares_count = override_engagement.get("shares", post.shares_count)
            post.views_count = override_engagement.get("views", post.views_count)
        else:
            # Calculate realistic engagement
            hours_since_post = (datetime.now(post.published_at.tzinfo) - post.published_at).total_seconds() / 3600
            
            engagement = self._calculate_realistic_engagement(
                follower_count=follower_count,
                platform=post.platform,
                post_type=post.post_type,
                hours_since_post=hours_since_post,
            )
            
            # Update post engagement (only increase, never decrease)
            post.likes_count = max(post.likes_count, engagement["likes"])
            post.comments_count = max(post.comments_count, engagement["comments"])
            post.shares_count = max(post.shares_count, engagement["shares"])
            post.views_count = max(post.views_count, engagement["views"])
        
        post.last_engagement_sync_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(post)
        
        logger.info(
            f"Simulated interactions for post {post_id}: "
            f"{post.likes_count} likes, {post.comments_count} comments, "
            f"{post.shares_count} shares, {post.views_count} views"
        )
        
        return post

    async def simulate_interactions_for_character(
        self,
        character_id: UUID,
        platform: Optional[str] = None,
        limit: int = 50,
    ) -> list[Post]:
        """Simulate interactions for all recent posts by a character.
        
        Args:
            character_id: UUID of the character
            platform: Optional platform filter
            limit: Maximum number of posts to process
            
        Returns:
            List of updated Post objects
        """
        # Build query
        query = (
            select(Post)
            .where(
                and_(
                    Post.character_id == character_id,
                    Post.status == "published",
                    Post.published_at.isnot(None),
                )
            )
            .order_by(Post.published_at.desc())
            .limit(limit)
        )
        
        if platform:
            query = query.where(Post.platform == platform)
        
        result = await self.db.execute(query)
        posts = result.scalars().all()
        
        updated_posts = []
        for post in posts:
            try:
                updated_post = await self.simulate_interactions_for_post(post.id)
                updated_posts.append(updated_post)
            except Exception as e:
                logger.error(f"Error simulating interactions for post {post.id}: {e}")
        
        logger.info(
            f"Simulated interactions for {len(updated_posts)} posts for character {character_id}"
        )
        
        return updated_posts

    async def simulate_interactions_for_recent_posts(
        self,
        hours: int = 48,
        limit: int = 100,
    ) -> list[Post]:
        """Simulate interactions for all recent posts across all characters.
        
        Args:
            hours: Only process posts published within this many hours
            limit: Maximum number of posts to process
            
        Returns:
            List of updated Post objects
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        query = (
            select(Post)
            .where(
                and_(
                    Post.status == "published",
                    Post.published_at >= cutoff_time,
                )
            )
            .order_by(Post.published_at.desc())
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        posts = result.scalars().all()
        
        updated_posts = []
        for post in posts:
            try:
                updated_post = await self.simulate_interactions_for_post(post.id)
                updated_posts.append(updated_post)
            except Exception as e:
                logger.error(f"Error simulating interactions for post {post.id}: {e}")
        
        logger.info(f"Simulated interactions for {len(updated_posts)} recent posts")
        
        return updated_posts
