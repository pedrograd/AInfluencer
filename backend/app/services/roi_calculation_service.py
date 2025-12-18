"""ROI calculation service for calculating return on investment metrics."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.analytics import Analytics

logger = get_logger(__name__)


class ROICalculationService:
    """Service for calculating ROI (Return on Investment) metrics."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize ROI calculation service.

        Args:
            db: Database session.
        """
        self.db = db

    async def calculate_roi(
        self,
        character_id: UUID | None = None,
        platform: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> dict[str, Any]:
        """
        Calculate ROI metrics for a character or all characters.

        ROI = (Revenue - Cost) / Cost * 100

        Args:
            character_id: Optional character ID to filter by.
            platform: Optional platform name to filter by.
            from_date: Optional start date for date range filter.
            to_date: Optional end date for date range filter.

        Returns:
            Dictionary containing ROI metrics including:
            - total_revenue: Total revenue in the period
            - total_cost: Total cost in the period
            - net_profit: Revenue - Cost
            - roi_percentage: ROI percentage
            - roi_ratio: ROI ratio (revenue/cost)
            - period: Date range
            - breakdown_by_platform: ROI breakdown by platform
            - breakdown_by_character: ROI breakdown by character (if character_id not provided)
        """
        # Build base query for revenue metrics
        revenue_query = select(
            Analytics.character_id,
            Analytics.platform,
            func.sum(Analytics.metric_value).label("total_revenue"),
        ).where(Analytics.metric_type == "revenue")

        # Build base query for cost metrics
        cost_query = select(
            Analytics.character_id,
            Analytics.platform,
            func.sum(Analytics.metric_value).label("total_cost"),
        ).where(Analytics.metric_type == "cost")

        # Apply filters
        if character_id:
            revenue_query = revenue_query.where(Analytics.character_id == character_id)
            cost_query = cost_query.where(Analytics.character_id == character_id)

        if platform:
            revenue_query = revenue_query.where(Analytics.platform == platform)
            cost_query = cost_query.where(Analytics.platform == platform)

        if from_date:
            revenue_query = revenue_query.where(Analytics.metric_date >= from_date)
            cost_query = cost_query.where(Analytics.metric_date >= from_date)

        if to_date:
            revenue_query = revenue_query.where(Analytics.metric_date <= to_date)
            cost_query = cost_query.where(Analytics.metric_date <= to_date)

        # Group by character and platform
        revenue_query = revenue_query.group_by(Analytics.character_id, Analytics.platform)
        cost_query = cost_query.group_by(Analytics.character_id, Analytics.platform)

        # Execute queries
        revenue_result = await self.db.execute(revenue_query)
        cost_result = await self.db.execute(cost_query)

        revenue_data = revenue_result.all()
        cost_data = cost_result.all()

        # Calculate totals
        total_revenue = Decimal("0.00")
        total_cost = Decimal("0.00")

        # Process revenue data
        revenue_by_platform: dict[str, Decimal] = {}
        revenue_by_character: dict[str, Decimal] = {}

        for row in revenue_data:
            revenue_value = Decimal(str(row.total_revenue or 0))
            total_revenue += revenue_value

            platform_key = row.platform or "aggregate"
            revenue_by_platform[platform_key] = (
                revenue_by_platform.get(platform_key, Decimal("0.00")) + revenue_value
            )

            if not character_id:
                char_key = str(row.character_id)
                revenue_by_character[char_key] = (
                    revenue_by_character.get(char_key, Decimal("0.00")) + revenue_value
                )

        # Process cost data
        cost_by_platform: dict[str, Decimal] = {}
        cost_by_character: dict[str, Decimal] = {}

        for row in cost_data:
            cost_value = Decimal(str(row.total_cost or 0))
            total_cost += cost_value

            platform_key = row.platform or "aggregate"
            cost_by_platform[platform_key] = (
                cost_by_platform.get(platform_key, Decimal("0.00")) + cost_value
            )

            if not character_id:
                char_key = str(row.character_id)
                cost_by_character[char_key] = (
                    cost_by_character.get(char_key, Decimal("0.00")) + cost_value
                )

        # Calculate ROI
        net_profit = total_revenue - total_cost

        # ROI percentage: (Revenue - Cost) / Cost * 100
        # ROI ratio: Revenue / Cost
        roi_percentage = Decimal("0.00")
        roi_ratio = Decimal("0.00")

        if total_cost > 0:
            roi_percentage = (net_profit / total_cost) * Decimal("100.00")
            roi_ratio = total_revenue / total_cost
        elif total_revenue > 0:
            # If there's revenue but no cost, ROI is infinite (or very high)
            roi_percentage = Decimal("999999.99")
            roi_ratio = Decimal("999999.99")

        # Build platform breakdown
        breakdown_by_platform: list[dict[str, Any]] = []
        all_platforms = set(revenue_by_platform.keys()) | set(cost_by_platform.keys())

        for platform_key in all_platforms:
            platform_revenue = revenue_by_platform.get(platform_key, Decimal("0.00"))
            platform_cost = cost_by_platform.get(platform_key, Decimal("0.00"))
            platform_profit = platform_revenue - platform_cost

            platform_roi_percentage = Decimal("0.00")
            platform_roi_ratio = Decimal("0.00")

            if platform_cost > 0:
                platform_roi_percentage = (platform_profit / platform_cost) * Decimal("100.00")
                platform_roi_ratio = platform_revenue / platform_cost
            elif platform_revenue > 0:
                platform_roi_percentage = Decimal("999999.99")
                platform_roi_ratio = Decimal("999999.99")

            breakdown_by_platform.append(
                {
                    "platform": platform_key if platform_key != "aggregate" else None,
                    "revenue": float(platform_revenue),
                    "cost": float(platform_cost),
                    "net_profit": float(platform_profit),
                    "roi_percentage": float(platform_roi_percentage),
                    "roi_ratio": float(platform_roi_ratio),
                }
            )

        # Build character breakdown (only if character_id not provided)
        breakdown_by_character: list[dict[str, Any]] = []

        if not character_id:
            all_characters = set(revenue_by_character.keys()) | set(cost_by_character.keys())

            for char_key in all_characters:
                char_revenue = revenue_by_character.get(char_key, Decimal("0.00"))
                char_cost = cost_by_character.get(char_key, Decimal("0.00"))
                char_profit = char_revenue - char_cost

                char_roi_percentage = Decimal("0.00")
                char_roi_ratio = Decimal("0.00")

                if char_cost > 0:
                    char_roi_percentage = (char_profit / char_cost) * Decimal("100.00")
                    char_roi_ratio = char_revenue / char_cost
                elif char_revenue > 0:
                    char_roi_percentage = Decimal("999999.99")
                    char_roi_ratio = Decimal("999999.99")

                breakdown_by_character.append(
                    {
                        "character_id": char_key,
                        "revenue": float(char_revenue),
                        "cost": float(char_cost),
                        "net_profit": float(char_profit),
                        "roi_percentage": float(char_roi_percentage),
                        "roi_ratio": float(char_roi_ratio),
                    }
                )

        return {
            "total_revenue": float(total_revenue),
            "total_cost": float(total_cost),
            "net_profit": float(net_profit),
            "roi_percentage": float(roi_percentage),
            "roi_ratio": float(roi_ratio),
            "period": {
                "from_date": from_date.isoformat() if from_date else None,
                "to_date": to_date.isoformat() if to_date else None,
            },
            "character_id": str(character_id) if character_id else None,
            "platform": platform,
            "breakdown_by_platform": breakdown_by_platform,
            "breakdown_by_character": breakdown_by_character if not character_id else [],
        }

    async def record_revenue(
        self,
        character_id: UUID,
        revenue: Decimal,
        metric_date: date,
        platform: str | None = None,
        platform_account_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Record revenue for a character.

        Args:
            character_id: Character ID.
            revenue: Revenue amount.
            metric_date: Date for which revenue is recorded.
            platform: Optional platform name.
            platform_account_id: Optional platform account ID.
            metadata: Optional additional metadata.
        """
        # Check if record already exists
        query = select(Analytics).where(
            Analytics.character_id == character_id,
            Analytics.metric_date == metric_date,
            Analytics.metric_type == "revenue",
            Analytics.platform == platform,
            Analytics.platform_account_id == platform_account_id,
        )

        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing record
            existing.metric_value = revenue
            if metadata:
                existing.extra_data = metadata
        else:
            # Create new record
            new_record = Analytics(
                character_id=character_id,
                platform_account_id=platform_account_id,
                metric_date=metric_date,
                platform=platform,
                metric_type="revenue",
                metric_value=revenue,
                extra_data=metadata,
            )
            self.db.add(new_record)

        await self.db.commit()
        logger.info(
            f"Recorded revenue {revenue} for character {character_id} on {metric_date}"
        )

    async def record_cost(
        self,
        character_id: UUID,
        cost: Decimal,
        metric_date: date,
        platform: str | None = None,
        platform_account_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Record cost for a character.

        Args:
            character_id: Character ID.
            cost: Cost amount.
            metric_date: Date for which cost is recorded.
            platform: Optional platform name.
            platform_account_id: Optional platform account ID.
            metadata: Optional additional metadata (e.g., cost_type: "api", "infrastructure", etc.).
        """
        # Check if record already exists
        query = select(Analytics).where(
            Analytics.character_id == character_id,
            Analytics.metric_date == metric_date,
            Analytics.metric_type == "cost",
            Analytics.platform == platform,
            Analytics.platform_account_id == platform_account_id,
        )

        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing record
            existing.metric_value = cost
            if metadata:
                existing.extra_data = metadata
        else:
            # Create new record
            new_record = Analytics(
                character_id=character_id,
                platform_account_id=platform_account_id,
                metric_date=metric_date,
                platform=platform,
                metric_type="cost",
                metric_value=cost,
                extra_data=metadata,
            )
            self.db.add(new_record)

        await self.db.commit()
        logger.info(
            f"Recorded cost {cost} for character {character_id} on {metric_date}"
        )
