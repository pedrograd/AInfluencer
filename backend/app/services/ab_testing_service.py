"""A/B testing service for managing experiments and analyzing results."""

from __future__ import annotations

import math
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.ab_test import ABTest, ABTestStatus, ABTestVariant
from app.models.post import Post

logger = get_logger(__name__)


class ABTestingService:
    """Service for managing A/B tests and analyzing results."""

    def __init__(self, db: AsyncSession):
        """Initialize the A/B testing service.
        
        Args:
            db: Database session.
        """
        self.db = db

    async def create_test(
        self,
        character_id: UUID,
        name: str,
        test_type: str,
        variant_a_name: str = "Variant A",
        variant_b_name: str = "Variant B",
        variant_a_config: Optional[dict[str, Any]] = None,
        variant_b_config: Optional[dict[str, Any]] = None,
        description: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        target_sample_size: Optional[int] = None,
        significance_level: Decimal = Decimal("0.05"),
    ) -> ABTest:
        """Create a new A/B test.
        
        Args:
            character_id: Character ID for the test.
            name: Test name.
            test_type: Type of test (content, caption, hashtags, posting_time, etc.).
            variant_a_name: Name for variant A.
            variant_b_name: Name for variant B.
            variant_a_config: Configuration for variant A.
            variant_b_config: Configuration for variant B.
            description: Test description.
            start_date: Test start date.
            end_date: Test end date.
            target_sample_size: Target sample size per variant.
            significance_level: Statistical significance level.
            
        Returns:
            Created ABTest instance.
        """
        test = ABTest(
            character_id=character_id,
            name=name,
            description=description,
            test_type=test_type,
            status=ABTestStatus.DRAFT,
            variant_a_name=variant_a_name,
            variant_b_name=variant_b_name,
            variant_a_config=variant_a_config,
            variant_b_config=variant_b_config,
            start_date=start_date,
            end_date=end_date,
            target_sample_size=target_sample_size,
            significance_level=significance_level,
        )
        self.db.add(test)
        await self.db.commit()
        await self.db.refresh(test)
        logger.info(f"Created A/B test {test.id} for character {character_id}")
        return test

    async def get_test(self, test_id: UUID) -> Optional[ABTest]:
        """Get an A/B test by ID.
        
        Args:
            test_id: Test ID.
            
        Returns:
            ABTest instance or None if not found.
        """
        result = await self.db.execute(select(ABTest).where(ABTest.id == test_id))
        return result.scalar_one_or_none()

    async def list_tests(
        self,
        character_id: Optional[UUID] = None,
        status: Optional[str] = None,
        test_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ABTest]:
        """List A/B tests with optional filters.
        
        Args:
            character_id: Filter by character ID.
            status: Filter by status.
            test_type: Filter by test type.
            limit: Maximum number of results.
            offset: Number of results to skip.
            
        Returns:
            List of ABTest instances.
        """
        query = select(ABTest)
        conditions = []
        
        if character_id:
            conditions.append(ABTest.character_id == character_id)
        if status:
            conditions.append(ABTest.status == status)
        if test_type:
            conditions.append(ABTest.test_type == test_type)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(ABTest.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def start_test(self, test_id: UUID) -> ABTest:
        """Start an A/B test.
        
        Args:
            test_id: Test ID.
            
        Returns:
            Updated ABTest instance.
            
        Raises:
            ValueError: If test is not in draft status.
        """
        test = await self.get_test(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")
        if test.status != ABTestStatus.DRAFT:
            raise ValueError(f"Test {test_id} is not in draft status")
        
        test.status = ABTestStatus.RUNNING
        test.start_date = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(test)
        logger.info(f"Started A/B test {test_id}")
        return test

    async def pause_test(self, test_id: UUID) -> ABTest:
        """Pause a running A/B test.
        
        Args:
            test_id: Test ID.
            
        Returns:
            Updated ABTest instance.
        """
        test = await self.get_test(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")
        if test.status != ABTestStatus.RUNNING:
            raise ValueError(f"Test {test_id} is not running")
        
        test.status = ABTestStatus.PAUSED
        await self.db.commit()
        await self.db.refresh(test)
        logger.info(f"Paused A/B test {test_id}")
        return test

    async def resume_test(self, test_id: UUID) -> ABTest:
        """Resume a paused A/B test.
        
        Args:
            test_id: Test ID.
            
        Returns:
            Updated ABTest instance.
        """
        test = await self.get_test(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")
        if test.status != ABTestStatus.PAUSED:
            raise ValueError(f"Test {test_id} is not paused")
        
        test.status = ABTestStatus.RUNNING
        await self.db.commit()
        await self.db.refresh(test)
        logger.info(f"Resumed A/B test {test_id}")
        return test

    async def complete_test(self, test_id: UUID) -> ABTest:
        """Complete an A/B test.
        
        Args:
            test_id: Test ID.
            
        Returns:
            Updated ABTest instance.
        """
        test = await self.get_test(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        test.status = ABTestStatus.COMPLETED
        test.end_date = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(test)
        logger.info(f"Completed A/B test {test_id}")
        return test

    async def assign_variant(
        self,
        test_id: UUID,
        post_id: UUID,
        variant_name: str,
        content_id: Optional[UUID] = None,
    ) -> ABTestVariant:
        """Assign a post to a test variant.
        
        Args:
            test_id: Test ID.
            post_id: Post ID to assign.
            variant_name: Variant name (variant_a_name or variant_b_name).
            content_id: Optional content ID if testing content variations.
            
        Returns:
            Created ABTestVariant instance.
        """
        test = await self.get_test(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")
        if test.status != ABTestStatus.RUNNING:
            raise ValueError(f"Test {test_id} is not running")
        if variant_name not in [test.variant_a_name, test.variant_b_name]:
            raise ValueError(f"Invalid variant name: {variant_name}")
        
        # Check if post is already assigned
        existing = await self.db.execute(
            select(ABTestVariant).where(
                and_(
                    ABTestVariant.test_id == test_id,
                    ABTestVariant.post_id == post_id,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Post {post_id} is already assigned to test {test_id}")
        
        variant = ABTestVariant(
            test_id=test_id,
            variant_name=variant_name,
            post_id=post_id,
            content_id=content_id,
        )
        self.db.add(variant)
        await self.db.commit()
        await self.db.refresh(variant)
        logger.info(f"Assigned post {post_id} to variant {variant_name} in test {test_id}")
        return variant

    async def update_variant_metrics(self, variant_id: UUID, metrics: dict[str, Any]) -> ABTestVariant:
        """Update metrics for a variant assignment.
        
        Args:
            variant_id: Variant assignment ID.
            metrics: Dictionary of metrics to update.
            
        Returns:
            Updated ABTestVariant instance.
        """
        variant = await self.db.get(ABTestVariant, variant_id)
        if not variant:
            raise ValueError(f"Variant {variant_id} not found")
        
        if variant.metrics:
            variant.metrics.update(metrics)
        else:
            variant.metrics = metrics
        
        await self.db.commit()
        await self.db.refresh(variant)
        return variant

    async def sync_variant_metrics_from_post(self, variant_id: UUID) -> ABTestVariant:
        """Sync variant metrics from the associated post.
        
        Args:
            variant_id: Variant assignment ID.
            
        Returns:
            Updated ABTestVariant instance.
        """
        variant = await self.db.get(ABTestVariant, variant_id)
        if not variant:
            raise ValueError(f"Variant {variant_id} not found")
        if not variant.post_id:
            raise ValueError(f"Variant {variant_id} has no associated post")
        
        post = await self.db.get(Post, variant.post_id)
        if not post:
            raise ValueError(f"Post {variant.post_id} not found")
        
        total_engagement = post.likes_count + post.comments_count + post.shares_count
        engagement_rate = (
            (total_engagement / post.views_count * 100) if post.views_count > 0 else 0.0
        )
        
        metrics = {
            "likes": post.likes_count,
            "comments": post.comments_count,
            "shares": post.shares_count,
            "views": post.views_count,
            "total_engagement": total_engagement,
            "engagement_rate": float(engagement_rate),
            "last_synced_at": datetime.utcnow().isoformat(),
        }
        
        return await self.update_variant_metrics(variant_id, metrics)

    async def get_test_results(self, test_id: UUID) -> dict[str, Any]:
        """Get statistical results for an A/B test.
        
        Args:
            test_id: Test ID.
            
        Returns:
            Dictionary with test results including metrics, statistics, and significance.
        """
        test = await self.get_test(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        # Get all variants for this test
        variants_query = select(ABTestVariant).where(ABTestVariant.test_id == test_id)
        variants_result = await self.db.execute(variants_query)
        variants = list(variants_result.scalars().all())
        
        # Sync metrics from posts if needed
        for variant in variants:
            if variant.post_id and (not variant.metrics or "last_synced_at" not in variant.metrics):
                try:
                    await self.sync_variant_metrics_from_post(variant.id)
                except Exception as e:
                    logger.warning(f"Failed to sync metrics for variant {variant.id}: {e}")
        
        # Refresh variants after sync
        variants_result = await self.db.execute(variants_query)
        variants = list(variants_result.scalars().all())
        
        # Separate by variant
        variant_a_items = [v for v in variants if v.variant_name == test.variant_a_name]
        variant_b_items = [v for v in variants if v.variant_name == test.variant_b_name]
        
        # Calculate metrics for each variant
        def calculate_variant_stats(items: list[ABTestVariant]) -> dict[str, Any]:
            if not items:
                return {
                    "count": 0,
                    "total_likes": 0,
                    "total_comments": 0,
                    "total_shares": 0,
                    "total_views": 0,
                    "total_engagement": 0,
                    "avg_engagement_rate": 0.0,
                    "avg_likes": 0.0,
                    "avg_comments": 0.0,
                    "avg_views": 0.0,
                }
            
            metrics_list = [item.metrics or {} for item in items]
            total_likes = sum(m.get("likes", 0) for m in metrics_list)
            total_comments = sum(m.get("comments", 0) for m in metrics_list)
            total_shares = sum(m.get("shares", 0) for m in metrics_list)
            total_views = sum(m.get("views", 0) for m in metrics_list)
            total_engagement = sum(m.get("total_engagement", 0) for m in metrics_list)
            engagement_rates = [m.get("engagement_rate", 0.0) for m in metrics_list if m.get("engagement_rate")]
            
            count = len(items)
            return {
                "count": count,
                "total_likes": total_likes,
                "total_comments": total_comments,
                "total_shares": total_shares,
                "total_views": total_views,
                "total_engagement": total_engagement,
                "avg_engagement_rate": sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0.0,
                "avg_likes": total_likes / count if count > 0 else 0.0,
                "avg_comments": total_comments / count if count > 0 else 0.0,
                "avg_views": total_views / count if count > 0 else 0.0,
            }
        
        variant_a_stats = calculate_variant_stats(variant_a_items)
        variant_b_stats = calculate_variant_stats(variant_b_items)
        
        # Calculate statistical significance (simple t-test approximation)
        def calculate_significance(stats_a: dict, stats_b: dict) -> dict[str, Any]:
            if stats_a["count"] == 0 or stats_b["count"] == 0:
                return {
                    "is_significant": False,
                    "p_value": 1.0,
                    "confidence": 0.0,
                }
            
            # Simple comparison based on engagement rate
            rate_a = stats_a["avg_engagement_rate"]
            rate_b = stats_b["avg_engagement_rate"]
            
            # Calculate improvement percentage
            if rate_a == 0:
                improvement = 100.0 if rate_b > 0 else 0.0
            else:
                improvement = ((rate_b - rate_a) / rate_a) * 100.0
            
            # Simple significance check (would need proper statistical test in production)
            # For MVP, we'll use a simple threshold-based approach
            sample_size = min(stats_a["count"], stats_b["count"])
            min_sample = 10  # Minimum sample size for significance
            rate_diff = abs(rate_b - rate_a)
            min_diff = 1.0  # Minimum difference for significance (1%)
            
            is_significant = (
                sample_size >= min_sample
                and rate_diff >= min_diff
                and (rate_b > rate_a or rate_a > rate_b)
            )
            
            # Estimate p-value (simplified)
            if is_significant and sample_size >= 30:
                p_value = 0.01  # Strong significance
            elif is_significant:
                p_value = 0.05  # Moderate significance
            else:
                p_value = 0.5  # Not significant
            
            confidence = (1.0 - p_value) * 100.0
            
            return {
                "is_significant": is_significant,
                "p_value": p_value,
                "confidence": confidence,
                "improvement_percentage": improvement,
                "winner": test.variant_b_name if rate_b > rate_a else test.variant_a_name if rate_a > rate_b else None,
            }
        
        significance = calculate_significance(variant_a_stats, variant_b_stats)
        
        return {
            "test_id": str(test_id),
            "test_name": test.name,
            "test_status": test.status,
            "variant_a": {
                "name": test.variant_a_name,
                "stats": variant_a_stats,
            },
            "variant_b": {
                "name": test.variant_b_name,
                "stats": variant_b_stats,
            },
            "significance": significance,
            "total_participants": len(variants),
            "created_at": test.created_at.isoformat() if test.created_at else None,
            "start_date": test.start_date.isoformat() if test.start_date else None,
            "end_date": test.end_date.isoformat() if test.end_date else None,
        }
