"""Competitor monitoring service for periodic tracking of competitor metrics."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.competitor import Competitor, CompetitorMonitoringSnapshot
from app.services.competitor_analysis_service import CompetitorAnalysisService

logger = get_logger(__name__)


class CompetitorMonitoringService:
    """Service for periodically monitoring competitor accounts and tracking metrics over time."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize competitor monitoring service.

        Args:
            db: Database session.
        """
        self.db = db
        self.analysis_service = CompetitorAnalysisService(db)

    async def monitor_competitor(self, competitor_id: UUID) -> dict[str, Any]:
        """
        Monitor a specific competitor and create a snapshot.

        This method fetches competitor metrics, runs analysis, and stores
        a snapshot. In a real implementation, this would fetch metrics from
        platform APIs. For now, it expects metrics to be provided via
        the competitor's metadata or requires manual metric input.

        Args:
            competitor_id: UUID of the competitor to monitor.

        Returns:
            Dictionary containing monitoring result with snapshot ID and analysis.
        """
        # Get competitor
        result = await self.db.execute(
            select(Competitor).where(Competitor.id == competitor_id)
        )
        competitor = result.scalar_one_or_none()

        if not competitor:
            raise ValueError(f"Competitor {competitor_id} not found")

        if competitor.monitoring_enabled != "true":
            raise ValueError(f"Monitoring is disabled for competitor {competitor_id}")

        # Get competitor metrics
        # In a real implementation, this would fetch from platform APIs
        # For now, we'll use metadata or require manual input
        competitor_metrics = await self._fetch_competitor_metrics(competitor)

        # Run analysis
        analysis_result = await self.analysis_service.analyze_competitor(
            competitor_name=competitor.competitor_name,
            competitor_platform=competitor.competitor_platform,
            competitor_metrics=competitor_metrics,
            character_id=competitor.character_id,
        )

        # Create snapshot
        snapshot = CompetitorMonitoringSnapshot(
            competitor_id=competitor.id,
            monitored_at=datetime.utcnow(),
            follower_count=competitor_metrics.get("follower_count"),
            following_count=competitor_metrics.get("following_count"),
            post_count=competitor_metrics.get("post_count"),
            engagement_rate=competitor_metrics.get("engagement_rate"),
            avg_likes=competitor_metrics.get("avg_likes"),
            avg_comments=competitor_metrics.get("avg_comments"),
            avg_shares=competitor_metrics.get("avg_shares"),
            metrics=competitor_metrics,
            analysis_result=analysis_result,
        )

        self.db.add(snapshot)

        # Update competitor last_monitored_at
        competitor.last_monitored_at = datetime.utcnow()
        competitor.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(snapshot)

        logger.info(
            f"Monitored competitor {competitor.competitor_name} "
            f"({competitor.competitor_platform}), snapshot ID: {snapshot.id}"
        )

        return {
            "snapshot_id": str(snapshot.id),
            "competitor_id": str(competitor.id),
            "monitored_at": snapshot.monitored_at.isoformat(),
            "metrics": competitor_metrics,
            "analysis": analysis_result,
        }

    async def monitor_all_due_competitors(self) -> list[dict[str, Any]]:
        """
        Monitor all competitors that are due for monitoring.

        A competitor is due if:
        - monitoring_enabled is true
        - last_monitored_at is None OR
        - (current_time - last_monitored_at) >= monitoring_frequency_hours

        Returns:
            List of monitoring results for each competitor monitored.
        """
        # Get all enabled competitors
        result = await self.db.execute(
            select(Competitor).where(Competitor.monitoring_enabled == "true")
        )
        competitors = result.scalars().all()

        now = datetime.utcnow()
        results: list[dict[str, Any]] = []

        for competitor in competitors:
            # Check if due for monitoring
            is_due = False

            if competitor.last_monitored_at is None:
                is_due = True
            else:
                hours_since_last = (now - competitor.last_monitored_at).total_seconds() / 3600
                if hours_since_last >= competitor.monitoring_frequency_hours:
                    is_due = True

            if is_due:
                try:
                    result = await self.monitor_competitor(competitor.id)
                    results.append(result)
                except Exception as e:
                    logger.error(
                        f"Error monitoring competitor {competitor.id} "
                        f"({competitor.competitor_name}): {e}"
                    )
                    results.append(
                        {
                            "competitor_id": str(competitor.id),
                            "error": str(e),
                            "monitored_at": now.isoformat(),
                        }
                    )

        return results

    async def _fetch_competitor_metrics(
        self, competitor: Competitor
    ) -> dict[str, Any]:
        """
        Fetch competitor metrics from platform APIs or metadata.

        In a real implementation, this would:
        - Use platform-specific APIs (Instagram Graph API, Twitter API, etc.)
        - Fetch follower count, post count, engagement metrics
        - Handle rate limiting and errors

        For now, this method:
        - Checks competitor metadata for stored metrics
        - Returns a default structure if no metrics found
        - In production, this would make actual API calls

        Args:
            competitor: Competitor model instance.

        Returns:
            Dictionary containing competitor metrics.
        """
        # Check if metrics are stored in extra_data
        if competitor.extra_data and isinstance(competitor.extra_data, dict):
            metrics = competitor.extra_data.get("metrics")
            if metrics and isinstance(metrics, dict):
                return metrics

        # If no metrics in metadata, return default structure
        # In production, this would fetch from platform APIs
        logger.warning(
            f"No metrics found for competitor {competitor.competitor_name}. "
            "Using default structure. In production, this would fetch from platform APIs."
        )

        return {
            "follower_count": 0,
            "following_count": 0,
            "post_count": 0,
            "engagement_rate": 0.0,
            "avg_likes": 0.0,
            "avg_comments": 0.0,
            "avg_shares": 0.0,
        }

    async def get_monitoring_history(
        self,
        competitor_id: UUID,
        limit: int = 100,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get monitoring history for a competitor.

        Args:
            competitor_id: UUID of the competitor.
            limit: Maximum number of snapshots to return (default: 100).
            start_date: Optional start date filter.
            end_date: Optional end date filter.

        Returns:
            List of snapshot dictionaries.
        """
        query = select(CompetitorMonitoringSnapshot).where(
            CompetitorMonitoringSnapshot.competitor_id == competitor_id
        )

        if start_date:
            query = query.where(CompetitorMonitoringSnapshot.monitored_at >= start_date)
        if end_date:
            query = query.where(CompetitorMonitoringSnapshot.monitored_at <= end_date)

        query = query.order_by(CompetitorMonitoringSnapshot.monitored_at.desc()).limit(limit)

        result = await self.db.execute(query)
        snapshots = result.scalars().all()

        return [
            {
                "id": str(snapshot.id),
                "monitored_at": snapshot.monitored_at.isoformat(),
                "follower_count": snapshot.follower_count,
                "following_count": snapshot.following_count,
                "post_count": snapshot.post_count,
                "engagement_rate": float(snapshot.engagement_rate)
                if snapshot.engagement_rate
                else None,
                "avg_likes": float(snapshot.avg_likes) if snapshot.avg_likes else None,
                "avg_comments": float(snapshot.avg_comments)
                if snapshot.avg_comments
                else None,
                "avg_shares": float(snapshot.avg_shares) if snapshot.avg_shares else None,
                "metrics": snapshot.metrics,
                "analysis_result": snapshot.analysis_result,
            }
            for snapshot in snapshots
        ]

    async def get_competitor_trends(
        self, competitor_id: UUID, days: int = 30
    ) -> dict[str, Any]:
        """
        Get trend analysis for a competitor over the specified period.

        Args:
            competitor_id: UUID of the competitor.
            days: Number of days to analyze (default: 30).

        Returns:
            Dictionary containing trend analysis with changes and growth rates.
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        history = await self.get_monitoring_history(
            competitor_id, limit=1000, start_date=start_date, end_date=end_date
        )

        if not history:
            return {
                "competitor_id": str(competitor_id),
                "period_days": days,
                "snapshots_count": 0,
                "trends": {},
            }

        # Sort by date (oldest first)
        history_sorted = sorted(history, key=lambda x: x["monitored_at"])

        first = history_sorted[0]
        last = history_sorted[-1]

        trends: dict[str, Any] = {}

        # Follower count trend
        if first.get("follower_count") and last.get("follower_count"):
            follower_change = last["follower_count"] - first["follower_count"]
            follower_growth_rate = (
                (follower_change / first["follower_count"]) * 100
                if first["follower_count"] > 0
                else 0
            )
            trends["follower_count"] = {
                "start": first["follower_count"],
                "end": last["follower_count"],
                "change": follower_change,
                "growth_rate_percent": round(follower_growth_rate, 2),
            }

        # Engagement rate trend
        if first.get("engagement_rate") and last.get("engagement_rate"):
            engagement_change = last["engagement_rate"] - first["engagement_rate"]
            trends["engagement_rate"] = {
                "start": first["engagement_rate"],
                "end": last["engagement_rate"],
                "change": round(engagement_change, 4),
            }

        # Average likes trend
        if first.get("avg_likes") and last.get("avg_likes"):
            likes_change = last["avg_likes"] - first["avg_likes"]
            trends["avg_likes"] = {
                "start": first["avg_likes"],
                "end": last["avg_likes"],
                "change": round(likes_change, 2),
            }

        return {
            "competitor_id": str(competitor_id),
            "period_days": days,
            "snapshots_count": len(history_sorted),
            "start_date": first["monitored_at"],
            "end_date": last["monitored_at"],
            "trends": trends,
        }
