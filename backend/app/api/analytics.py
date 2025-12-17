"""Analytics API endpoints for engagement analytics and metrics."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.services.engagement_analytics_service import EngagementAnalyticsService

logger = get_logger(__name__)

router = APIRouter()


class AnalyticsOverviewResponse(BaseModel):
    """Response model for analytics overview."""

    total_posts: int
    total_engagement: int
    total_followers: int
    total_reach: int
    engagement_rate: float
    follower_growth: int
    top_performing_posts: list[dict]
    platform_breakdown: dict[str, dict[str, int]]
    trends: dict[str, list[int]]


class CharacterAnalyticsResponse(BaseModel):
    """Response model for character-specific analytics."""

    character_id: str
    total_posts: int
    total_engagement: int
    total_followers: int
    total_reach: int
    engagement_rate: float
    follower_growth: int
    average_engagement_per_post: float
    best_platform: Optional[str]
    total_posts_by_platform: dict[str, int]
    top_performing_posts: list[dict]
    platform_breakdown: dict[str, dict[str, int]]
    trends: dict[str, list[int]]


class PostAnalyticsResponse(BaseModel):
    """Response model for post-specific analytics."""

    post_id: str
    character_id: str
    platform: str
    post_type: Optional[str]
    platform_post_id: Optional[str]
    platform_post_url: Optional[str]
    published_at: Optional[str]
    likes: int
    comments: int
    shares: int
    views: int
    total_engagement: int
    engagement_rate: float
    hashtags: list[str]
    mentions: list[str]
    last_engagement_sync_at: Optional[str]


class BestPerformingContentAnalysisResponse(BaseModel):
    """Response model for best-performing content analysis."""

    total_posts_analyzed: int
    content_type_analysis: dict[str, dict[str, float | int]]
    hashtag_analysis: list[dict[str, str | float | int]]
    posting_time_analysis: dict[str, list[dict[str, int | float | str]]]
    caption_analysis: dict[str, float | dict[str, int]]
    platform_analysis: dict[str, dict[str, float | int]]
    top_performing_posts: list[dict[str, str | int | float | list | None]]
    recommendations: list[dict[str, str]]


@router.get("/overview", response_model=AnalyticsOverviewResponse, tags=["analytics"])
async def get_analytics_overview(
    character_id: Optional[str] = Query(None, description="Filter by character ID"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    from_date: Optional[str] = Query(
        None, description="Start date (ISO format: YYYY-MM-DD)"
    ),
    to_date: Optional[str] = Query(None, description="End date (ISO format: YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsOverviewResponse:
    """
    Get analytics overview with aggregated metrics.

    Query Parameters:
        character_id: Optional character ID to filter by.
        platform: Optional platform name to filter by.
        from_date: Optional start date for date range filter (YYYY-MM-DD).
        to_date: Optional end date for date range filter (YYYY-MM-DD).

    Returns:
        Analytics overview with metrics, top posts, platform breakdown, and trends.
    """
    try:
        service = EngagementAnalyticsService(db)

        # Parse dates if provided
        from_date_dt = None
        to_date_dt = None
        if from_date:
            from_date_dt = datetime.fromisoformat(from_date)
        if to_date:
            to_date_dt = datetime.fromisoformat(to_date)

        # Parse character_id if provided
        character_id_uuid = None
        if character_id:
            try:
                character_id_uuid = UUID(character_id)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid character_id format: {character_id}"
                )

        data = await service.get_overview(
            character_id=character_id_uuid,
            platform=platform,
            from_date=from_date_dt,
            to_date=to_date_dt,
        )

        return AnalyticsOverviewResponse(**data)
    except Exception as e:
        logger.exception("Error getting analytics overview")
        raise HTTPException(status_code=500, detail=f"Error getting analytics: {str(e)}")


@router.get(
    "/characters/{character_id}",
    response_model=CharacterAnalyticsResponse,
    tags=["analytics"],
)
async def get_character_analytics(
    character_id: str,
    from_date: Optional[str] = Query(
        None, description="Start date (ISO format: YYYY-MM-DD)"
    ),
    to_date: Optional[str] = Query(None, description="End date (ISO format: YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
) -> CharacterAnalyticsResponse:
    """
    Get character-specific analytics.

    Path Parameters:
        character_id: Character ID (UUID).

    Query Parameters:
        from_date: Optional start date for date range filter (YYYY-MM-DD).
        to_date: Optional end date for date range filter (YYYY-MM-DD).

    Returns:
        Character-specific analytics with metrics and platform breakdown.
    """
    try:
        service = EngagementAnalyticsService(db)

        # Parse character_id
        try:
            character_id_uuid = UUID(character_id)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid character_id format: {character_id}"
            )

        # Parse dates if provided
        from_date_dt = None
        to_date_dt = None
        if from_date:
            from_date_dt = datetime.fromisoformat(from_date)
        if to_date:
            to_date_dt = datetime.fromisoformat(to_date)

        data = await service.get_character_analytics(
            character_id=character_id_uuid,
            from_date=from_date_dt,
            to_date=to_date_dt,
        )

        return CharacterAnalyticsResponse(**data)
    except ValueError as e:
        logger.exception("Error getting character analytics")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Error getting character analytics")
        raise HTTPException(status_code=500, detail=f"Error getting analytics: {str(e)}")


@router.get(
    "/posts/{post_id}", response_model=PostAnalyticsResponse, tags=["analytics"]
)
async def get_post_analytics(
    post_id: str, db: AsyncSession = Depends(get_db)
) -> PostAnalyticsResponse:
    """
    Get post-specific analytics.

    Path Parameters:
        post_id: Post ID (UUID).

    Returns:
        Post-specific analytics with engagement metrics.
    """
    try:
        service = EngagementAnalyticsService(db)

        # Parse post_id
        try:
            post_id_uuid = UUID(post_id)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid post_id format: {post_id}"
            )

        data = await service.get_post_analytics(post_id_uuid)

        return PostAnalyticsResponse(**data)
    except ValueError as e:
        logger.exception("Error getting post analytics")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Error getting post analytics")
        raise HTTPException(status_code=500, detail=f"Error getting analytics: {str(e)}")


@router.get(
    "/best-performing-content",
    response_model=BestPerformingContentAnalysisResponse,
    tags=["analytics"],
)
async def get_best_performing_content_analysis(
    character_id: Optional[str] = Query(None, description="Filter by character ID"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    from_date: Optional[str] = Query(
        None, description="Start date (ISO format: YYYY-MM-DD)"
    ),
    to_date: Optional[str] = Query(None, description="End date (ISO format: YYYY-MM-DD)"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of items in top lists"),
    db: AsyncSession = Depends(get_db),
) -> BestPerformingContentAnalysisResponse:
    """
    Analyze best-performing content to identify patterns and recommendations.

    Query Parameters:
        character_id: Optional character ID to filter by.
        platform: Optional platform name to filter by.
        from_date: Optional start date for date range filter (YYYY-MM-DD).
        to_date: Optional end date for date range filter (YYYY-MM-DD).
        limit: Maximum number of items to return in top lists (1-50).

    Returns:
        Best-performing content analysis with patterns, top performers, and recommendations.
    """
    try:
        service = EngagementAnalyticsService(db)

        # Parse dates if provided
        from_date_dt = None
        to_date_dt = None
        if from_date:
            from_date_dt = datetime.fromisoformat(from_date)
        if to_date:
            to_date_dt = datetime.fromisoformat(to_date)

        # Parse character_id if provided
        character_id_uuid = None
        if character_id:
            try:
                character_id_uuid = UUID(character_id)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid character_id format: {character_id}"
                )

        data = await service.get_best_performing_content_analysis(
            character_id=character_id_uuid,
            platform=platform,
            from_date=from_date_dt,
            to_date=to_date_dt,
            limit=limit,
        )

        return BestPerformingContentAnalysisResponse(**data)
    except Exception as e:
        logger.exception("Error getting best-performing content analysis")
        raise HTTPException(
            status_code=500, detail=f"Error getting analysis: {str(e)}"
        )
