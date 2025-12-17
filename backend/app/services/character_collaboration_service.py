"""Character collaboration simulation service for simulating character-to-character interactions."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from uuid import UUID
from typing import Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.post import Post
from app.models.character import Character, CharacterPersonality

logger = get_logger(__name__)


class CharacterCollaborationService:
    """Service for simulating realistic character-to-character interactions.
    
    Simulates interactions between characters (likes, comments, shares) based on:
    - Character personalities (extroversion, interests, communication style)
    - Post content and topics
    - Character compatibility (similar interests, complementary personalities)
    - Realistic interaction patterns (characters interact more with similar/compatible characters)
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize character collaboration simulation service."""
        self.db = db

    def _calculate_compatibility_score(
        self,
        actor: Character,
        actor_personality: Optional[CharacterPersonality],
        target: Character,
        target_personality: Optional[CharacterPersonality],
    ) -> float:
        """Calculate compatibility score between two characters (0.0 to 1.0).
        
        Higher score means characters are more likely to interact.
        
        Args:
            actor: Character performing the interaction
            actor_personality: Actor's personality traits
            target: Character whose post is being interacted with
            target_personality: Target's personality traits
            
        Returns:
            Compatibility score between 0.0 and 1.0
        """
        score = 0.5  # Base compatibility
        
        # Interest overlap (40% weight)
        if actor.interests and target.interests:
            actor_interests = set(interest.lower() for interest in actor.interests)
            target_interests = set(interest.lower() for interest in target.interests)
            if actor_interests and target_interests:
                overlap = len(actor_interests & target_interests) / len(actor_interests | target_interests)
                score += 0.4 * overlap
        
        # Personality compatibility (30% weight)
        if actor_personality and target_personality:
            # Extroversion: extroverts interact more, introverts interact less
            extro_diff = abs(float(actor_personality.extroversion or 0.5) - float(target_personality.extroversion or 0.5))
            extro_score = 1.0 - extro_diff  # Closer extroversion = higher compatibility
            score += 0.15 * extro_score
            
            # Similar communication styles increase compatibility
            if (actor_personality.communication_style and 
                target_personality.communication_style and
                actor_personality.communication_style.lower() == target_personality.communication_style.lower()):
                score += 0.15
        
        # Topic overlap (20% weight)
        if (actor_personality and target_personality and
            actor_personality.preferred_topics and target_personality.preferred_topics):
            actor_topics = set(topic.lower() for topic in actor_personality.preferred_topics)
            target_topics = set(topic.lower() for topic in target_personality.preferred_topics)
            if actor_topics and target_topics:
                topic_overlap = len(actor_topics & target_topics) / len(actor_topics | target_topics)
                score += 0.2 * topic_overlap
        
        # Location similarity (10% weight) - characters in same location interact more
        if actor.location and target.location:
            if actor.location.lower() == target.location.lower():
                score += 0.1
        
        return min(1.0, max(0.0, score))

    def _should_interact(self, compatibility_score: float, actor_extroversion: float) -> bool:
        """Determine if character should interact based on compatibility and personality.
        
        Args:
            compatibility_score: Compatibility score (0.0 to 1.0)
            actor_extroversion: Actor's extroversion level (0.0 to 1.0)
            
        Returns:
            True if interaction should occur
        """
        # Base interaction probability = compatibility * (0.3 + 0.7 * extroversion)
        # Extroverts interact more, introverts interact less
        interaction_probability = compatibility_score * (0.3 + 0.7 * actor_extroversion)
        return random.random() < interaction_probability

    def _calculate_interaction_counts(
        self,
        compatibility_score: float,
        actor_extroversion: float,
        post_age_hours: float,
    ) -> tuple[int, int, int]:
        """Calculate interaction counts (likes, comments, shares) for a post.
        
        Args:
            compatibility_score: Compatibility score (0.0 to 1.0)
            actor_extroversion: Actor's extroversion level (0.0 to 1.0)
            post_age_hours: Hours since post was published
            
        Returns:
            Tuple of (likes, comments, shares)
        """
        # Engagement decays with post age (most interactions happen in first 24-48 hours)
        age_decay = max(0.0, 1.0 - (post_age_hours / 72.0))  # Decay over 72 hours
        
        # Base interaction intensity based on compatibility and extroversion
        intensity = compatibility_score * (0.4 + 0.6 * actor_extroversion) * age_decay
        
        # Likes are most common
        likes = 1 if intensity > 0.3 else 0
        
        # Comments are less common, require higher compatibility/extroversion
        comments = 1 if intensity > 0.6 and random.random() < 0.4 else 0
        
        # Shares are rare, require very high compatibility
        shares = 1 if intensity > 0.8 and random.random() < 0.2 else 0
        
        return (likes, comments, shares)

    async def simulate_interaction(
        self,
        actor_character_id: UUID,
        target_post_id: UUID,
    ) -> Optional[Post]:
        """Simulate a single character interacting with another character's post.
        
        Args:
            actor_character_id: UUID of character performing the interaction
            target_post_id: UUID of post to interact with
            
        Returns:
            Updated Post object, or None if interaction shouldn't occur
        """
        # Load actor character with personality
        actor_query = (
            select(Character)
            .options(selectinload(Character.personality))
            .where(Character.id == actor_character_id)
            .where(Character.deleted_at.is_(None))
        )
        actor_result = await self.db.execute(actor_query)
        actor = actor_result.scalar_one_or_none()
        
        if not actor:
            logger.warning(f"Actor character {actor_character_id} not found")
            return None
        
        # Load target post with character and personality
        post_query = (
            select(Post)
            .options(selectinload(Post.character).selectinload(Character.personality))
            .where(Post.id == target_post_id)
            .where(Post.status == "published")
            .where(Post.published_at.isnot(None))
        )
        post_result = await self.db.execute(post_query)
        post = post_result.scalar_one_or_none()
        
        if not post:
            logger.warning(f"Target post {target_post_id} not found or not published")
            return None
        
        # Don't interact with own posts
        if post.character_id == actor_character_id:
            logger.debug(f"Character {actor_character_id} skipping own post {target_post_id}")
            return None
        
        # Load target character
        target = post.character
        if not target:
            logger.warning(f"Target character for post {target_post_id} not found")
            return None
        
        # Calculate compatibility
        actor_personality = actor.personality
        target_personality = getattr(target, 'personality', None)
        
        compatibility = self._calculate_compatibility_score(
            actor, actor_personality, target, target_personality
        )
        
        # Get actor extroversion
        actor_extroversion = float(actor_personality.extroversion or 0.5) if actor_personality else 0.5
        
        # Decide if interaction should occur
        if not self._should_interact(compatibility, actor_extroversion):
            logger.debug(
                f"Character {actor_character_id} not interacting with post {target_post_id} "
                f"(compatibility: {compatibility:.2f}, extroversion: {actor_extroversion:.2f})"
            )
            return None
        
        # Calculate post age
        if post.published_at:
            post_age = (datetime.utcnow() - post.published_at.replace(tzinfo=None)).total_seconds() / 3600.0
        else:
            post_age = 0.0
        
        # Calculate interaction counts
        likes, comments, shares = self._calculate_interaction_counts(
            compatibility, actor_extroversion, post_age
        )
        
        # Update post engagement
        if likes > 0:
            post.likes_count = (post.likes_count or 0) + likes
        if comments > 0:
            post.comments_count = (post.comments_count or 0) + comments
        if shares > 0:
            post.shares_count = (post.shares_count or 0) + shares
        
        post.last_engagement_sync_at = datetime.utcnow()
        
        await self.db.flush()
        await self.db.refresh(post)
        
        logger.info(
            f"Character {actor.name} ({actor_character_id}) interacted with "
            f"post {target_post_id} by {target.name}: "
            f"{likes} likes, {comments} comments, {shares} shares "
            f"(compatibility: {compatibility:.2f})"
        )
        
        return post

    async def simulate_interactions_for_character(
        self,
        actor_character_id: UUID,
        target_character_id: Optional[UUID] = None,
        platform: Optional[str] = None,
        limit: int = 10,
        max_posts_per_target: int = 3,
    ) -> list[Post]:
        """Simulate interactions for a character with other characters' posts.
        
        Args:
            actor_character_id: UUID of character performing interactions
            target_character_id: Optional specific character to interact with (None = all characters)
            platform: Optional platform filter
            limit: Maximum number of posts to consider
            max_posts_per_target: Maximum interactions per target character
            
        Returns:
            List of updated Post objects
        """
        # Build query for target posts
        query = (
            select(Post)
            .options(selectinload(Post.character).selectinload(Character.personality))
            .where(Post.status == "published")
            .where(Post.published_at.isnot(None))
            .where(Post.character_id != actor_character_id)  # Don't interact with own posts
            .order_by(Post.published_at.desc())
            .limit(limit)
        )
        
        if target_character_id:
            query = query.where(Post.character_id == target_character_id)
        
        if platform:
            query = query.where(Post.platform == platform)
        
        result = await self.db.execute(query)
        posts = result.scalars().all()
        
        # Group posts by character
        posts_by_character: dict[UUID, list[Post]] = {}
        for post in posts:
            if post.character_id not in posts_by_character:
                posts_by_character[post.character_id] = []
            posts_by_character[post.character_id].append(post)
        
        # Simulate interactions (limit per target character)
        updated_posts = []
        for target_char_id, target_posts in posts_by_character.items():
            # Limit interactions per target character
            posts_to_interact = target_posts[:max_posts_per_target]
            
            for post in posts_to_interact:
                try:
                    updated_post = await self.simulate_interaction(actor_character_id, post.id)
                    if updated_post:
                        updated_posts.append(updated_post)
                except Exception as e:
                    logger.error(
                        f"Error simulating interaction for post {post.id}: {e}",
                        exc_info=True
                    )
        
        logger.info(
            f"Simulated {len(updated_posts)} interactions for character {actor_character_id}"
        )
        
        return updated_posts

    async def simulate_collaboration_network(
        self,
        character_ids: Optional[list[UUID]] = None,
        platform: Optional[str] = None,
        interactions_per_character: int = 5,
    ) -> dict[str, int]:
        """Simulate a network of character interactions.
        
        Args:
            character_ids: Optional list of character IDs to include (None = all active characters)
            platform: Optional platform filter
            interactions_per_character: Number of interactions each character should perform
            
        Returns:
            Dictionary with statistics (total_interactions, characters_involved, posts_updated)
        """
        # Load all active characters
        if character_ids:
            char_query = (
                select(Character)
                .where(Character.id.in_(character_ids))
                .where(Character.deleted_at.is_(None))
                .where(Character.is_active == True)
            )
        else:
            char_query = (
                select(Character)
                .where(Character.deleted_at.is_(None))
                .where(Character.is_active == True)
            )
        
        char_result = await self.db.execute(char_query)
        characters = char_result.scalars().all()
        
        if len(characters) < 2:
            logger.warning("Need at least 2 characters for collaboration simulation")
            return {
                "total_interactions": 0,
                "characters_involved": len(characters),
                "posts_updated": 0,
            }
        
        # Simulate interactions for each character
        all_updated_posts: set[UUID] = set()
        total_interactions = 0
        
        for character in characters:
            try:
                updated_posts = await self.simulate_interactions_for_character(
                    character.id,
                    target_character_id=None,
                    platform=platform,
                    limit=interactions_per_character * 2,  # Get more posts to choose from
                    max_posts_per_target=2,
                )
                
                for post in updated_posts:
                    all_updated_posts.add(post.id)
                total_interactions += len(updated_posts)
                
            except Exception as e:
                logger.error(
                    f"Error simulating interactions for character {character.id}: {e}",
                    exc_info=True
                )
        
        logger.info(
            f"Collaboration network simulation complete: "
            f"{total_interactions} interactions, {len(characters)} characters, "
            f"{len(all_updated_posts)} posts updated"
        )
        
        return {
            "total_interactions": total_interactions,
            "characters_involved": len(characters),
            "posts_updated": len(all_updated_posts),
        }
