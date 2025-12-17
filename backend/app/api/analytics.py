"""Analytics API endpoints for engagement analytics and metrics."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.services.engagement_analytics_service import EngagementAnalyticsService
from app.services.character_performance_tracking_service import (
    CharacterPerformanceTrackingService,
)
from app.services.content_strategy_adjustment_service import (
    ContentStrategyAdjustmentService,
)
from app.services.trend_following_service import TrendFollowingService
from app.services.hashtag_strategy_automation_service import (
    HashtagStrategyAutomationService,
)
from app.services.sentiment_analysis_service import (
    SentimentAnalysisService,
    SentimentAnalysisRequest,
    SentimentAnalysisResult,
    SentimentLabel,
)
from app.services.audience_analysis_service import AudienceAnalysisService
from app.services.roi_calculation_service import ROICalculationService

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


class RecordMetricsRequest(BaseModel):
    """Request model for recording performance metrics."""

    metric_date: str = Field(..., description="Date for metrics (YYYY-MM-DD)")
    metrics: dict[str, float] = Field(..., description="Dictionary of metric_type to value")
    platform: Optional[str] = Field(None, description="Platform name")
    platform_account_id: Optional[str] = Field(None, description="Platform account ID")
    metadata: Optional[dict[str, Any]] = Field(None, description="Additional metadata")


class CharacterPerformanceResponse(BaseModel):
    """Response model for character performance tracking."""

    character_id: str
    from_date: Optional[str]
    to_date: Optional[str]
    platform: Optional[str]
    performance_data: list[dict[str, Any]]


class PerformanceTrendResponse(BaseModel):
    """Response model for performance trends."""

    character_id: str
    metric_type: str
    platform: Optional[str]
    from_date: str
    to_date: str
    trend: list[dict[str, float | str]]


@router.post("/characters/{character_id}/record", tags=["analytics"])
async def record_character_metrics(
    character_id: str,
    request: RecordMetricsRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Record performance metrics for a character.

    Path Parameters:
        character_id: Character ID (UUID).

    Request Body:
        metric_date: Date for which metrics are recorded (YYYY-MM-DD).
        metrics: Dictionary mapping metric_type to metric_value.
        platform: Optional platform name.
        platform_account_id: Optional platform account ID.
        metadata: Optional additional metadata.

    Returns:
        Success message.
    """
    try:
        service = CharacterPerformanceTrackingService(db)

        # Parse character_id
        try:
            character_id_uuid = UUID(character_id)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid character_id format: {character_id}"
            )

        # Parse metric_date
        try:
            metric_date = date.fromisoformat(request.metric_date)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid date format: {request.metric_date}"
            )

        # Parse platform_account_id if provided
        platform_account_id_uuid = None
        if request.platform_account_id:
            try:
                platform_account_id_uuid = UUID(request.platform_account_id)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid platform_account_id format: {request.platform_account_id}",
                )

        await service.record_metrics(
            character_id=character_id_uuid,
            metric_date=metric_date,
            metrics=request.metrics,
            platform=request.platform,
            platform_account_id=platform_account_id_uuid,
            metadata=request.metadata,
        )

        return {"ok": True, "message": "Metrics recorded successfully"}
    except Exception as e:
        logger.exception("Error recording character metrics")
        raise HTTPException(
            status_code=500, detail=f"Error recording metrics: {str(e)}"
        )


@router.get(
    "/characters/{character_id}/performance",
    response_model=CharacterPerformanceResponse,
    tags=["analytics"],
)
async def get_character_performance(
    character_id: str,
    from_date: Optional[str] = Query(
        None, description="Start date (ISO format: YYYY-MM-DD)"
    ),
    to_date: Optional[str] = Query(None, description="End date (ISO format: YYYY-MM-DD)"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    metric_types: Optional[str] = Query(
        None, description="Comma-separated list of metric types"
    ),
    db: AsyncSession = Depends(get_db),
) -> CharacterPerformanceResponse:
    """
    Get historical performance metrics for a character.

    Path Parameters:
        character_id: Character ID (UUID).

    Query Parameters:
        from_date: Optional start date for date range filter (YYYY-MM-DD).
        to_date: Optional end date for date range filter (YYYY-MM-DD).
        platform: Optional platform name to filter by.
        metric_types: Optional comma-separated list of metric types.

    Returns:
        Character performance data with historical metrics.
    """
    try:
        service = CharacterPerformanceTrackingService(db)

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
            try:
                from_date_dt = date.fromisoformat(from_date)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid from_date format: {from_date}"
                )
        if to_date:
            try:
                to_date_dt = date.fromisoformat(to_date)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid to_date format: {to_date}"
                )

        # Parse metric_types if provided
        metric_types_list = None
        if metric_types:
            metric_types_list = [m.strip() for m in metric_types.split(",")]

        data = await service.get_character_performance(
            character_id=character_id_uuid,
            from_date=from_date_dt,
            to_date=to_date_dt,
            platform=platform,
            metric_types=metric_types_list,
        )

        return CharacterPerformanceResponse(**data)
    except Exception as e:
        logger.exception("Error getting character performance")
        raise HTTPException(
            status_code=500, detail=f"Error getting performance: {str(e)}"
        )


@router.get(
    "/characters/{character_id}/trends/{metric_type}",
    response_model=PerformanceTrendResponse,
    tags=["analytics"],
)
async def get_performance_trends(
    character_id: str,
    metric_type: str,
    days: int = Query(default=30, ge=1, le=365, description="Number of days to look back"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    db: AsyncSession = Depends(get_db),
) -> PerformanceTrendResponse:
    """
    Get performance trends for a specific metric over time.

    Path Parameters:
        character_id: Character ID (UUID).
        metric_type: Type of metric to track (follower_count, engagement_rate, etc.).

    Query Parameters:
        days: Number of days to look back (1-365, default: 30).
        platform: Optional platform name to filter by.

    Returns:
        Performance trend data with dates and values.
    """
    try:
        service = CharacterPerformanceTrackingService(db)

        # Parse character_id
        try:
            character_id_uuid = UUID(character_id)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid character_id format: {character_id}"
            )

        data = await service.get_performance_trends(
            character_id=character_id_uuid,
            metric_type=metric_type,
            days=days,
            platform=platform,
        )

        return PerformanceTrendResponse(**data)
    except Exception as e:
        logger.exception("Error getting performance trends")
        raise HTTPException(
            status_code=500, detail=f"Error getting trends: {str(e)}"
        )


@router.post("/characters/{character_id}/snapshot", tags=["analytics"])
async def create_performance_snapshot(
    character_id: str,
    snapshot_date: Optional[str] = Query(
        None, description="Date for snapshot (YYYY-MM-DD, defaults to today)"
    ),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Create a snapshot of current character performance by calculating metrics from posts.

    Path Parameters:
        character_id: Character ID (UUID).

    Query Parameters:
        snapshot_date: Optional date for snapshot (YYYY-MM-DD, defaults to today).

    Returns:
        Success message.
    """
    try:
        service = CharacterPerformanceTrackingService(db)

        # Parse character_id
        try:
            character_id_uuid = UUID(character_id)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid character_id format: {character_id}"
            )

        # Parse snapshot_date if provided
        snapshot_date_dt = None
        if snapshot_date:
            try:
                snapshot_date_dt = date.fromisoformat(snapshot_date)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid snapshot_date format: {snapshot_date}"
                )

        await service.snapshot_character_performance(
            character_id=character_id_uuid,
            snapshot_date=snapshot_date_dt,
        )

        return {"ok": True, "message": "Performance snapshot created successfully"}
    except Exception as e:
        logger.exception("Error creating performance snapshot")
        raise HTTPException(
            status_code=500, detail=f"Error creating snapshot: {str(e)}"
        )


# ===== Content Strategy Adjustment Endpoints =====

class StrategyAdjustmentResponse(BaseModel):
    """Response model for strategy adjustment."""

    adjusted: bool
    character_id: str
    platform: Optional[str]
    adjusted_at: str
    adjustments: dict[str, Any]
    recommendations: list[dict[str, str]]
    reason: Optional[str] = None
    analysis: Optional[dict[str, Any]] = None


class StrategyRecommendationsResponse(BaseModel):
    """Response model for strategy recommendations."""

    character_id: str
    platform: Optional[str]
    analysis_period: dict[str, Optional[str]]
    total_posts_analyzed: int
    recommendations: list[dict[str, str]]
    content_type_preferences: dict[str, Any]
    hashtag_strategy: dict[str, Any]
    caption_preferences: dict[str, Any]
    platform_focus: dict[str, Any]


@router.post(
    "/strategy/adjust/{character_id}",
    response_model=StrategyAdjustmentResponse,
    tags=["analytics", "strategy"],
)
async def adjust_content_strategy(
    character_id: str,
    platform: Optional[str] = Query(None, description="Filter by platform"),
    from_date: Optional[str] = Query(
        None, description="Start date (ISO format: YYYY-MM-DD)"
    ),
    to_date: Optional[str] = Query(None, description="End date (ISO format: YYYY-MM-DD)"),
    min_posts_required: int = Query(10, description="Minimum posts required for adjustment"),
    db: AsyncSession = Depends(get_db),
) -> StrategyAdjustmentResponse:
    """
    Automatically adjust content strategy for a character based on analytics.
    
    Analyzes performance data and automatically adjusts:
    - Posting times in automation rules
    - Content type preferences
    - Hashtag strategy
    - Caption length preferences
    - Platform focus
    """
    try:
        character_id_uuid = UUID(character_id)

        # Parse dates
        from_date_dt = None
        if from_date:
            try:
                from_date_dt = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid from_date format: {from_date}"
                )

        to_date_dt = None
        if to_date:
            try:
                to_date_dt = datetime.fromisoformat(to_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid to_date format: {to_date}"
                )

        service = ContentStrategyAdjustmentService(db)
        result = await service.adjust_strategy_for_character(
            character_id=character_id_uuid,
            platform=platform,
            from_date=from_date_dt,
            to_date=to_date_dt,
            min_posts_required=min_posts_required,
        )

        return StrategyAdjustmentResponse(**result)
    except ValueError as e:
        logger.exception("Error parsing request parameters")
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        logger.exception("Error adjusting content strategy")
        raise HTTPException(
            status_code=500, detail=f"Error adjusting strategy: {str(e)}"
        )


@router.get(
    "/strategy/recommendations/{character_id}",
    response_model=StrategyRecommendationsResponse,
    tags=["analytics", "strategy"],
)
async def get_strategy_recommendations(
    character_id: str,
    platform: Optional[str] = Query(None, description="Filter by platform"),
    from_date: Optional[str] = Query(
        None, description="Start date (ISO format: YYYY-MM-DD)"
    ),
    to_date: Optional[str] = Query(None, description="End date (ISO format: YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
) -> StrategyRecommendationsResponse:
    """
    Get content strategy recommendations without applying adjustments.
    
    Returns recommendations for:
    - Content type preferences
    - Hashtag strategy
    - Caption length preferences
    - Platform focus
    - Posting times
    """
    try:
        character_id_uuid = UUID(character_id)

        # Parse dates
        from_date_dt = None
        if from_date:
            try:
                from_date_dt = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid from_date format: {from_date}"
                )

        to_date_dt = None
        if to_date:
            try:
                to_date_dt = datetime.fromisoformat(to_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid to_date format: {to_date}"
                )

        service = ContentStrategyAdjustmentService(db)
        result = await service.get_strategy_recommendations(
            character_id=character_id_uuid,
            platform=platform,
            from_date=from_date_dt,
            to_date=to_date_dt,
        )

        return StrategyRecommendationsResponse(**result)
    except ValueError as e:
        logger.exception("Error parsing request parameters")
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        logger.exception("Error getting strategy recommendations")
        raise HTTPException(
            status_code=500, detail=f"Error getting recommendations: {str(e)}"
        )


# ===== Trend Following Endpoints =====

class TrendingHashtagResponse(BaseModel):
    """Response model for trending hashtag."""

    hashtag: str
    trend_score: float
    growth_rate: float
    recent_usage_count: int
    earlier_usage_count: int
    avg_engagement: float
    avg_views: float
    engagement_rate: float
    trend_direction: str


class TrendRecommendationsResponse(BaseModel):
    """Response model for trend recommendations."""

    character_id: str
    platform: Optional[str]
    analysis_period_days: int
    trending_hashtags: list[dict[str, Any]]
    hashtag_recommendations: list[dict[str, Any]]
    content_type_recommendations: list[dict[str, Any]]
    total_trends_analyzed: int


class TrendVelocityResponse(BaseModel):
    """Response model for trend velocity."""

    hashtag: str
    platform: Optional[str]
    days_analyzed: int
    daily_usage: dict[str, int]
    total_usage: int
    velocity: float
    trend: str


@router.get(
    "/trends/hashtags",
    response_model=list[TrendingHashtagResponse],
    tags=["analytics", "trends"],
)
async def get_trending_hashtags(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to look back"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    character_id: Optional[str] = Query(None, description="Filter by character ID"),
    min_usage_count: int = Query(default=2, ge=1, description="Minimum usage count"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
) -> list[TrendingHashtagResponse]:
    """
    Get trending hashtags based on usage and engagement over time.
    
    Analyzes hashtag trends by comparing recent usage to earlier periods,
    calculating growth rates, engagement metrics, and trend scores.
    """
    try:
        service = TrendFollowingService(db)

        # Parse character_id if provided
        character_id_uuid = None
        if character_id:
            try:
                character_id_uuid = UUID(character_id)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid character_id format: {character_id}"
                )

        trends = await service.analyze_hashtag_trends(
            days=days,
            platform=platform,
            character_id=character_id_uuid,
            min_usage_count=min_usage_count,
            limit=limit,
        )

        return [TrendingHashtagResponse(**trend) for trend in trends]
    except Exception as e:
        logger.exception("Error getting trending hashtags")
        raise HTTPException(
            status_code=500, detail=f"Error getting trending hashtags: {str(e)}"
        )


@router.get(
    "/trends/recommendations/{character_id}",
    response_model=TrendRecommendationsResponse,
    tags=["analytics", "trends"],
)
async def get_trend_recommendations(
    character_id: str,
    platform: Optional[str] = Query(None, description="Filter by platform"),
    days: int = Query(default=30, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of recommendations"),
    db: AsyncSession = Depends(get_db),
) -> TrendRecommendationsResponse:
    """
    Get trend recommendations for a character based on trending hashtags and content patterns.
    
    Provides personalized recommendations for:
    - Trending hashtags to use
    - Best content types for trending hashtags
    - Content strategies based on current trends
    """
    try:
        # Parse character_id
        try:
            character_id_uuid = UUID(character_id)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid character_id format: {character_id}"
            )

        service = TrendFollowingService(db)
        result = await service.get_trend_recommendations(
            character_id=character_id_uuid,
            platform=platform,
            days=days,
            limit=limit,
        )

        return TrendRecommendationsResponse(**result)
    except Exception as e:
        logger.exception("Error getting trend recommendations")
        raise HTTPException(
            status_code=500, detail=f"Error getting trend recommendations: {str(e)}"
        )


@router.get(
    "/trends/velocity/{hashtag}",
    response_model=TrendVelocityResponse,
    tags=["analytics", "trends"],
)
async def get_trend_velocity(
    hashtag: str,
    days: int = Query(default=7, ge=1, le=30, description="Number of days to analyze"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    db: AsyncSession = Depends(get_db),
) -> TrendVelocityResponse:
    """
    Get trend velocity for a specific hashtag (how fast it's growing).
    
    Analyzes daily usage patterns to determine if a hashtag is:
    - Accelerating (growing faster)
    - Stable (consistent usage)
    - Declining (decreasing usage)
    """
    try:
        service = TrendFollowingService(db)
        result = await service.get_trend_velocity(
            hashtag=hashtag,
            days=days,
            platform=platform,
        )

        return TrendVelocityResponse(**result)
    except Exception as e:
        logger.exception("Error getting trend velocity")
        raise HTTPException(
            status_code=500, detail=f"Error getting trend velocity: {str(e)}"
        )


class HashtagStrategyApplyResponse(BaseModel):
    """Response model for hashtag strategy application."""

    character_id: str
    platform: Optional[str]
    applied_at: str
    applied: bool
    reason: Optional[str] = None
    hashtag_strategy: dict[str, Any]
    automation_rules_updated: int
    recommended_hashtags: list[dict[str, Any]]
    primary_hashtags: list[str]
    hashtag_count_recommendation: int


class HashtagStrategyRecommendationsResponse(BaseModel):
    """Response model for hashtag strategy recommendations."""

    hashtags: list[str]
    primary_hashtags: list[str]
    count: int
    strategy: dict[str, Any]


@router.post(
    "/hashtag-strategy/apply/{character_id}",
    response_model=HashtagStrategyApplyResponse,
    tags=["analytics", "hashtags", "automation"],
)
async def apply_hashtag_strategy(
    character_id: str,
    platform: Optional[str] = Query(None, description="Filter by platform"),
    from_date: Optional[str] = Query(
        None, description="Start date (ISO format: YYYY-MM-DDTHH:MM:SS)"
    ),
    to_date: Optional[str] = Query(
        None, description="End date (ISO format: YYYY-MM-DDTHH:MM:SS)"
    ),
    min_posts_required: int = Query(
        default=10, ge=1, description="Minimum posts required for strategy"
    ),
    db: AsyncSession = Depends(get_db),
) -> HashtagStrategyApplyResponse:
    """
    Automatically apply hashtag strategy to a character's automation rules.
    
    Retrieves hashtag strategy recommendations from analytics and applies them to:
    - Automation rules (stores recommended hashtags in action_config)
    - Content generation preferences
    
    The strategy is based on performance analysis of the character's posts.
    """
    try:
        # Parse character_id
        try:
            character_id_uuid = UUID(character_id)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid character_id format: {character_id}"
            )

        # Parse dates if provided
        from_date_obj = None
        to_date_obj = None
        if from_date:
            try:
                from_date_obj = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid from_date format: {from_date}"
                )
        if to_date:
            try:
                to_date_obj = datetime.fromisoformat(to_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid to_date format: {to_date}"
                )

        service = HashtagStrategyAutomationService(db)
        result = await service.apply_hashtag_strategy_to_character(
            character_id=character_id_uuid,
            platform=platform,
            from_date=from_date_obj,
            to_date=to_date_obj,
            min_posts_required=min_posts_required,
        )

        return HashtagStrategyApplyResponse(**result)
    except Exception as e:
        logger.exception("Error applying hashtag strategy")
        raise HTTPException(
            status_code=500, detail=f"Error applying hashtag strategy: {str(e)}"
        )


@router.get(
    "/hashtag-strategy/recommendations/{character_id}",
    response_model=HashtagStrategyRecommendationsResponse,
    tags=["analytics", "hashtags"],
)
async def get_hashtag_strategy_recommendations(
    character_id: str,
    platform: Optional[str] = Query(None, description="Filter by platform"),
    count: Optional[int] = Query(
        None, ge=1, le=30, description="Number of hashtags to return"
    ),
    use_primary_only: bool = Query(
        default=False, description="Return only primary hashtags (top 5)"
    ),
    db: AsyncSession = Depends(get_db),
) -> HashtagStrategyRecommendationsResponse:
    """
    Get recommended hashtags for a character based on performance analytics.
    
    Returns hashtags that have performed well for the character based on:
    - Average engagement per hashtag
    - Post count per hashtag
    - Recent performance trends
    """
    try:
        # Parse character_id
        try:
            character_id_uuid = UUID(character_id)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid character_id format: {character_id}"
            )

        service = HashtagStrategyAutomationService(db)
        hashtags = await service.get_recommended_hashtags_for_character(
            character_id=character_id_uuid,
            platform=platform,
            count=count,
            use_primary_only=use_primary_only,
        )

        # Get full strategy for context
        strategy_service = ContentStrategyAdjustmentService(db)
        recommendations = await strategy_service.get_strategy_recommendations(
            character_id=character_id_uuid,
            platform=platform,
        )
        hashtag_strategy = recommendations.get("hashtag_strategy", {})

        return HashtagStrategyRecommendationsResponse(
            hashtags=hashtags,
            primary_hashtags=hashtag_strategy.get("primary_hashtags", []),
            count=len(hashtags),
            strategy=hashtag_strategy,
        )
    except Exception as e:
        logger.exception("Error getting hashtag strategy recommendations")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting hashtag strategy recommendations: {str(e)}",
        )


# ===== Sentiment Analysis Endpoints =====

class SentimentAnalysisRequestModel(BaseModel):
    """Request model for sentiment analysis."""

    text: str = Field(..., description="Text to analyze for sentiment")
    language: str = Field(default="en", description="Language code (default: en)")


class SentimentAnalysisResponseModel(BaseModel):
    """Response model for sentiment analysis."""

    label: str = Field(..., description="Sentiment label (positive, negative, neutral)")
    score: float = Field(..., description="Sentiment score (-1.0 to 1.0)")
    confidence: float = Field(..., description="Confidence score (0.0 to 1.0)")
    text: str = Field(..., description="Original text analyzed")
    model: str = Field(..., description="Model used for analysis")


@router.post(
    "/sentiment",
    response_model=SentimentAnalysisResponseModel,
    tags=["analytics", "sentiment"],
)
async def analyze_sentiment(
    request: SentimentAnalysisRequestModel,
) -> SentimentAnalysisResponseModel:
    """
    Analyze sentiment of text.
    
    Returns sentiment analysis with label (positive/negative/neutral),
    score (-1.0 to 1.0), and confidence (0.0 to 1.0).
    """
    try:
        service = SentimentAnalysisService()
        result = service.analyze_sentiment(
            SentimentAnalysisRequest(
                text=request.text,
                language=request.language,
            )
        )

        return SentimentAnalysisResponseModel(
            label=result.label.value,
            score=result.score,
            confidence=result.confidence,
            text=result.text,
            model=result.model,
        )
    except Exception as e:
        logger.exception("Error analyzing sentiment")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing sentiment: {str(e)}",
        )


# ===== Audience Analysis Endpoints =====

class AudienceAnalysisResponse(BaseModel):
    """Response model for audience analysis."""

    total_posts: int
    total_audience_reach: int
    platform_distribution: dict[str, dict[str, Any]]
    engagement_patterns: dict[str, Any]
    content_preferences: dict[str, dict[str, Any]]
    activity_patterns: dict[str, Any]
    audience_growth: dict[str, Any]
    engagement_quality: dict[str, Any]
    audience_insights: list[dict[str, str]]


@router.get(
    "/audience",
    response_model=AudienceAnalysisResponse,
    tags=["analytics", "audience"],
)
async def analyze_audience(
    character_id: Optional[str] = Query(None, description="Filter by character ID"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    from_date: Optional[str] = Query(
        None, description="Start date (ISO format: YYYY-MM-DD)"
    ),
    to_date: Optional[str] = Query(None, description="End date (ISO format: YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
) -> AudienceAnalysisResponse:
    """
    Analyze audience demographics and behavior patterns.
    
    Provides insights into:
    - Platform distribution and audience share
    - Engagement patterns by content type
    - Content preferences
    - Activity patterns (peak hours and days)
    - Audience growth trends
    - Engagement quality metrics
    - Actionable insights and recommendations
    """
    try:
        service = AudienceAnalysisService(db)

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

        data = await service.analyze_audience(
            character_id=character_id_uuid,
            platform=platform,
            from_date=from_date_dt,
            to_date=to_date_dt,
        )

        return AudienceAnalysisResponse(**data)
    except Exception as e:
        logger.exception("Error analyzing audience")
        raise HTTPException(
            status_code=500, detail=f"Error analyzing audience: {str(e)}"
        )


# ===== ROI Calculation Endpoints =====

class ROIResponse(BaseModel):
    """Response model for ROI calculation."""

    total_revenue: float
    total_cost: float
    net_profit: float
    roi_percentage: float
    roi_ratio: float
    period: dict[str, Optional[str]]
    character_id: Optional[str]
    platform: Optional[str]
    breakdown_by_platform: list[dict[str, Any]]
    breakdown_by_character: list[dict[str, Any]]


class RecordRevenueRequest(BaseModel):
    """Request model for recording revenue."""

    revenue: float = Field(..., ge=0, description="Revenue amount")
    metric_date: str = Field(..., description="Date for revenue (YYYY-MM-DD)")
    platform: Optional[str] = Field(None, description="Platform name")
    platform_account_id: Optional[str] = Field(None, description="Platform account ID")
    metadata: Optional[dict[str, Any]] = Field(None, description="Additional metadata")


class RecordCostRequest(BaseModel):
    """Request model for recording cost."""

    cost: float = Field(..., ge=0, description="Cost amount")
    metric_date: str = Field(..., description="Date for cost (YYYY-MM-DD)")
    platform: Optional[str] = Field(None, description="Platform name")
    platform_account_id: Optional[str] = Field(None, description="Platform account ID")
    metadata: Optional[dict[str, Any]] = Field(
        None, description="Additional metadata (e.g., cost_type: 'api', 'infrastructure')"
    )


@router.get("/roi", response_model=ROIResponse, tags=["analytics", "roi"])
async def calculate_roi(
    character_id: Optional[str] = Query(None, description="Filter by character ID"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    from_date: Optional[str] = Query(
        None, description="Start date (ISO format: YYYY-MM-DD)"
    ),
    to_date: Optional[str] = Query(None, description="End date (ISO format: YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
) -> ROIResponse:
    """
    Calculate ROI (Return on Investment) metrics.
    
    ROI = (Revenue - Cost) / Cost * 100
    
    Provides:
    - Total revenue and cost in the period
    - Net profit (revenue - cost)
    - ROI percentage and ratio
    - Breakdown by platform
    - Breakdown by character (if character_id not provided)
    """
    try:
        service = ROICalculationService(db)

        # Parse character_id if provided
        character_id_uuid = None
        if character_id:
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
            try:
                from_date_dt = date.fromisoformat(from_date)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid from_date format: {from_date}"
                )
        if to_date:
            try:
                to_date_dt = date.fromisoformat(to_date)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid to_date format: {to_date}"
                )

        data = await service.calculate_roi(
            character_id=character_id_uuid,
            platform=platform,
            from_date=from_date_dt,
            to_date=to_date_dt,
        )

        return ROIResponse(**data)
    except Exception as e:
        logger.exception("Error calculating ROI")
        raise HTTPException(status_code=500, detail=f"Error calculating ROI: {str(e)}")


@router.post("/characters/{character_id}/revenue", tags=["analytics", "roi"])
async def record_revenue(
    character_id: str,
    request: RecordRevenueRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Record revenue for a character.
    
    Records revenue from sources like:
    - Sponsorships
    - Affiliate links
    - Platform monetization
    - Direct sales
    """
    try:
        service = ROICalculationService(db)

        # Parse character_id
        try:
            character_id_uuid = UUID(character_id)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid character_id format: {character_id}"
            )

        # Parse metric_date
        try:
            metric_date_dt = date.fromisoformat(request.metric_date)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid date format: {request.metric_date}"
            )

        # Parse platform_account_id if provided
        platform_account_id_uuid = None
        if request.platform_account_id:
            try:
                platform_account_id_uuid = UUID(request.platform_account_id)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid platform_account_id format: {request.platform_account_id}",
                )

        from decimal import Decimal

        await service.record_revenue(
            character_id=character_id_uuid,
            revenue=Decimal(str(request.revenue)),
            metric_date=metric_date_dt,
            platform=request.platform,
            platform_account_id=platform_account_id_uuid,
            metadata=request.metadata,
        )

        return {"ok": True, "message": "Revenue recorded successfully"}
    except Exception as e:
        logger.exception("Error recording revenue")
        raise HTTPException(
            status_code=500, detail=f"Error recording revenue: {str(e)}"
        )


@router.post("/characters/{character_id}/cost", tags=["analytics", "roi"])
async def record_cost(
    character_id: str,
    request: RecordCostRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Record cost for a character.
    
    Records costs from sources like:
    - API costs (content generation)
    - Infrastructure costs
    - Platform fees
    - Third-party service costs
    """
    try:
        service = ROICalculationService(db)

        # Parse character_id
        try:
            character_id_uuid = UUID(character_id)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid character_id format: {character_id}"
            )

        # Parse metric_date
        try:
            metric_date_dt = date.fromisoformat(request.metric_date)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid date format: {request.metric_date}"
            )

        # Parse platform_account_id if provided
        platform_account_id_uuid = None
        if request.platform_account_id:
            try:
                platform_account_id_uuid = UUID(request.platform_account_id)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid platform_account_id format: {request.platform_account_id}",
                )

        from decimal import Decimal

        await service.record_cost(
            character_id=character_id_uuid,
            cost=Decimal(str(request.cost)),
            metric_date=metric_date_dt,
            platform=request.platform,
            platform_account_id=platform_account_id_uuid,
            metadata=request.metadata,
        )

        return {"ok": True, "message": "Cost recorded successfully"}
    except Exception as e:
        logger.exception("Error recording cost")
        raise HTTPException(status_code=500, detail=f"Error recording cost: {str(e)}")
