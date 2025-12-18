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
from app.core.config import settings
from app.core.error_taxonomy import ErrorCode, classify_error, create_error_response
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
from app.services.competitor_analysis_service import CompetitorAnalysisService
from app.services.competitor_monitoring_service import CompetitorMonitoringService
from app.services.market_trend_prediction_service import MarketTrendPredictionService
from app.models.competitor import Competitor, CompetitorMonitoringSnapshot

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
        
        # Check if it's a database connection error
        error_str = str(e).lower()
        is_db_error = (
            "connection" in error_str
            or "unable to connect" in error_str
            or "operationalerror" in error_str
            or "database" in error_str
        )
        
        if is_db_error:
            # Return graceful degradation response
            return AnalyticsOverviewResponse(
                total_posts=0,
                total_engagement=0,
                total_followers=0,
                total_reach=0,
                engagement_rate=0.0,
                follower_growth=0,
                top_performing_posts=[],
                platform_breakdown={},
                trends={"follower_growth": [], "engagement": []},
            )
        
        # For other errors, raise HTTPException with taxonomy
        from fastapi import HTTPException
        error_code, remediation = classify_error(e, {"endpoint": "/api/analytics/overview"})
        error_response = create_error_response(
            error_code=error_code,
            message=f"Error getting analytics: {str(e)}",
            detail=f"If this is a database connection issue, ensure the database is configured and running." if settings.app_env == "dev" else None,
            remediation=remediation,
        )
        raise HTTPException(
            status_code=500,
            detail=error_response["message"],
        )


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


class CompetitorAnalysisRequest(BaseModel):
    """Request model for competitor analysis."""

    competitor_name: str = Field(..., description="Name or identifier of the competitor")
    competitor_platform: str = Field(..., description="Platform name (instagram, twitter, facebook, etc.)")
    character_id: Optional[str] = Field(None, description="Optional character ID to compare against")
    follower_count: int = Field(..., ge=0, description="Number of followers")
    following_count: Optional[int] = Field(None, ge=0, description="Number of following")
    post_count: Optional[int] = Field(None, ge=0, description="Number of posts")
    engagement_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Average engagement rate (0.0 to 1.0)")
    avg_likes: Optional[float] = Field(None, ge=0, description="Average likes per post")
    avg_comments: Optional[float] = Field(None, ge=0, description="Average comments per post")
    avg_shares: Optional[float] = Field(None, ge=0, description="Average shares per post")


class CompetitorAnalysisResponse(BaseModel):
    """Response model for competitor analysis."""

    competitor: dict[str, Any]
    our_metrics: dict[str, Any]
    comparison: dict[str, Any]
    recommendations: list[str]
    analysis_date: str


@router.post("/competitor", response_model=CompetitorAnalysisResponse, tags=["analytics", "competitors"])
async def analyze_competitor(
    request: CompetitorAnalysisRequest,
    db: AsyncSession = Depends(get_db),
) -> CompetitorAnalysisResponse:
    """
    Analyze a competitor account and compare with our characters.

    Request Body:
        competitor_name: Name or identifier of the competitor.
        competitor_platform: Platform name (instagram, twitter, facebook, telegram, onlyfans, youtube).
        character_id: Optional character ID to compare against specific character.
        follower_count: Number of followers (required).
        Other metrics: Optional metrics (following_count, post_count, engagement_rate, avg_likes, avg_comments, avg_shares).

    Returns:
        Competitor analysis with comparison, gaps, strengths, weaknesses, and recommendations.
    """
    try:
        service = CompetitorAnalysisService(db)

        # Parse character_id if provided
        character_id_uuid = None
        if request.character_id:
            try:
                character_id_uuid = UUID(request.character_id)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid character_id format: {request.character_id}"
                )

        # Extract metrics from request
        metrics_dict = {
            "follower_count": request.follower_count,
            "following_count": request.following_count,
            "post_count": request.post_count,
            "engagement_rate": request.engagement_rate,
            "avg_likes": request.avg_likes,
            "avg_comments": request.avg_comments,
            "avg_shares": request.avg_shares,
        }
        # Remove None values
        metrics_dict = {k: v for k, v in metrics_dict.items() if v is not None}

        data = await service.analyze_competitor(
            competitor_name=request.competitor_name,
            competitor_platform=request.competitor_platform,
            competitor_metrics=metrics_dict,
            character_id=character_id_uuid,
        )

        return CompetitorAnalysisResponse(**data)
    except ValueError as e:
        logger.exception("Error analyzing competitor")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error analyzing competitor")
        raise HTTPException(status_code=500, detail=f"Error analyzing competitor: {str(e)}")


# Competitor Monitoring Endpoints

class CompetitorCreateRequest(BaseModel):
    """Request model for creating a competitor to monitor."""

    character_id: str = Field(..., description="Character ID to compare against")
    competitor_name: str = Field(..., description="Name or identifier of the competitor")
    competitor_platform: str = Field(
        ..., description="Platform name (instagram, twitter, facebook, etc.)"
    )
    competitor_username: str | None = Field(None, description="Optional username/handle")
    monitoring_frequency_hours: int = Field(24, description="Monitoring frequency in hours")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")


class CompetitorUpdateRequest(BaseModel):
    """Request model for updating a competitor."""

    competitor_name: str | None = None
    competitor_username: str | None = None
    monitoring_enabled: bool | None = None
    monitoring_frequency_hours: int | None = None
    metadata: dict[str, Any] | None = None


class CompetitorResponse(BaseModel):
    """Response model for competitor."""

    id: str
    character_id: str
    competitor_name: str
    competitor_platform: str
    competitor_username: str | None
    monitoring_enabled: str
    monitoring_frequency_hours: int
    last_monitored_at: str | None
    metadata: dict[str, Any] | None
    created_at: str
    updated_at: str


class CompetitorMonitoringResultResponse(BaseModel):
    """Response model for competitor monitoring result."""

    snapshot_id: str | None
    competitor_id: str
    monitored_at: str
    metrics: dict[str, Any] | None
    analysis: dict[str, Any] | None
    error: str | None = None


@router.post("/competitors", response_model=CompetitorResponse, tags=["analytics", "competitors"])
async def create_competitor(
    request: CompetitorCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> CompetitorResponse:
    """
    Add a competitor to monitor.

    Request Body:
        character_id: Character ID to compare against.
        competitor_name: Name or identifier of the competitor.
        competitor_platform: Platform name (instagram, twitter, facebook, etc.).
        competitor_username: Optional username/handle.
        monitoring_frequency_hours: How often to monitor (default: 24 hours).
        metadata: Optional additional data including metrics.

    Returns:
        Created competitor information.
    """
    try:
        character_id_uuid = UUID(request.character_id)

        competitor = Competitor(
            character_id=character_id_uuid,
            competitor_name=request.competitor_name,
            competitor_platform=request.competitor_platform,
            competitor_username=request.competitor_username,
            monitoring_enabled="true",
            monitoring_frequency_hours=request.monitoring_frequency_hours,
            metadata=request.metadata,
        )

        db.add(competitor)
        await db.commit()
        await db.refresh(competitor)

        return CompetitorResponse(
            id=str(competitor.id),
            character_id=str(competitor.character_id),
            competitor_name=competitor.competitor_name,
            competitor_platform=competitor.competitor_platform,
            competitor_username=competitor.competitor_username,
            monitoring_enabled=competitor.monitoring_enabled,
            monitoring_frequency_hours=competitor.monitoring_frequency_hours,
            last_monitored_at=competitor.last_monitored_at.isoformat()
            if competitor.last_monitored_at
            else None,
            metadata=competitor.extra_data,
            created_at=competitor.created_at.isoformat(),
            updated_at=competitor.updated_at.isoformat(),
        )
    except ValueError as e:
        logger.exception("Error creating competitor")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error creating competitor")
        raise HTTPException(status_code=500, detail=f"Error creating competitor: {str(e)}")


@router.get("/competitors", response_model=list[CompetitorResponse], tags=["analytics", "competitors"])
async def list_competitors(
    character_id: str | None = Query(None, description="Filter by character ID"),
    platform: str | None = Query(None, description="Filter by platform"),
    enabled_only: bool = Query(False, description="Only return enabled competitors"),
    db: AsyncSession = Depends(get_db),
) -> list[CompetitorResponse]:
    """
    List all tracked competitors.

    Query Parameters:
        character_id: Optional filter by character ID.
        platform: Optional filter by platform.
        enabled_only: Only return competitors with monitoring enabled.

    Returns:
        List of competitors.
    """
    try:
        from sqlalchemy import select

        query = select(Competitor)

        if character_id:
            character_id_uuid = UUID(character_id)
            query = query.where(Competitor.character_id == character_id_uuid)

        if platform:
            query = query.where(Competitor.competitor_platform == platform)

        if enabled_only:
            query = query.where(Competitor.monitoring_enabled == "true")

        result = await db.execute(query)
        competitors = result.scalars().all()

        return [
            CompetitorResponse(
                id=str(c.id),
                character_id=str(c.character_id),
                competitor_name=c.competitor_name,
                competitor_platform=c.competitor_platform,
                competitor_username=c.competitor_username,
                monitoring_enabled=c.monitoring_enabled,
                monitoring_frequency_hours=c.monitoring_frequency_hours,
                last_monitored_at=c.last_monitored_at.isoformat() if c.last_monitored_at else None,
                metadata=c.extra_data,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
            )
            for c in competitors
        ]
    except ValueError as e:
        logger.exception("Error listing competitors")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error listing competitors")
        raise HTTPException(status_code=500, detail=f"Error listing competitors: {str(e)}")


@router.get("/competitors/{competitor_id}", response_model=CompetitorResponse, tags=["analytics", "competitors"])
async def get_competitor(
    competitor_id: str,
    db: AsyncSession = Depends(get_db),
) -> CompetitorResponse:
    """
    Get competitor details.

    Returns:
        Competitor information.
    """
    try:
        from sqlalchemy import select

        competitor_id_uuid = UUID(competitor_id)
        result = await db.execute(
            select(Competitor).where(Competitor.id == competitor_id_uuid)
        )
        competitor = result.scalar_one_or_none()

        if not competitor:
            raise HTTPException(status_code=404, detail=f"Competitor {competitor_id} not found")

        return CompetitorResponse(
            id=str(competitor.id),
            character_id=str(competitor.character_id),
            competitor_name=competitor.competitor_name,
            competitor_platform=competitor.competitor_platform,
            competitor_username=competitor.competitor_username,
            monitoring_enabled=competitor.monitoring_enabled,
            monitoring_frequency_hours=competitor.monitoring_frequency_hours,
            last_monitored_at=competitor.last_monitored_at.isoformat()
            if competitor.last_monitored_at
            else None,
            metadata=competitor.extra_data,
            created_at=competitor.created_at.isoformat(),
            updated_at=competitor.updated_at.isoformat(),
        )
    except ValueError as e:
        logger.exception("Error getting competitor")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error getting competitor")
        raise HTTPException(status_code=500, detail=f"Error getting competitor: {str(e)}")


@router.put("/competitors/{competitor_id}", response_model=CompetitorResponse, tags=["analytics", "competitors"])
async def update_competitor(
    competitor_id: str,
    request: CompetitorUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> CompetitorResponse:
    """
    Update competitor settings.

    Returns:
        Updated competitor information.
    """
    try:
        from sqlalchemy import select

        competitor_id_uuid = UUID(competitor_id)
        result = await db.execute(
            select(Competitor).where(Competitor.id == competitor_id_uuid)
        )
        competitor = result.scalar_one_or_none()

        if not competitor:
            raise HTTPException(status_code=404, detail=f"Competitor {competitor_id} not found")

        if request.competitor_name is not None:
            competitor.competitor_name = request.competitor_name
        if request.competitor_username is not None:
            competitor.competitor_username = request.competitor_username
        if request.monitoring_enabled is not None:
            competitor.monitoring_enabled = "true" if request.monitoring_enabled else "false"
        if request.monitoring_frequency_hours is not None:
            competitor.monitoring_frequency_hours = request.monitoring_frequency_hours
        if request.metadata is not None:
            competitor.extra_data = request.metadata

        await db.commit()
        await db.refresh(competitor)

        return CompetitorResponse(
            id=str(competitor.id),
            character_id=str(competitor.character_id),
            competitor_name=competitor.competitor_name,
            competitor_platform=competitor.competitor_platform,
            competitor_username=competitor.competitor_username,
            monitoring_enabled=competitor.monitoring_enabled,
            monitoring_frequency_hours=competitor.monitoring_frequency_hours,
            last_monitored_at=competitor.last_monitored_at.isoformat()
            if competitor.last_monitored_at
            else None,
            metadata=competitor.extra_data,
            created_at=competitor.created_at.isoformat(),
            updated_at=competitor.updated_at.isoformat(),
        )
    except ValueError as e:
        logger.exception("Error updating competitor")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error updating competitor")
        raise HTTPException(status_code=500, detail=f"Error updating competitor: {str(e)}")


@router.delete("/competitors/{competitor_id}", tags=["analytics", "competitors"])
async def delete_competitor(
    competitor_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Remove a competitor from monitoring.

    Returns:
        Success message.
    """
    try:
        from sqlalchemy import select

        competitor_id_uuid = UUID(competitor_id)
        result = await db.execute(
            select(Competitor).where(Competitor.id == competitor_id_uuid)
        )
        competitor = result.scalar_one_or_none()

        if not competitor:
            raise HTTPException(status_code=404, detail=f"Competitor {competitor_id} not found")

        await db.delete(competitor)
        await db.commit()

        return {"message": f"Competitor {competitor_id} deleted successfully"}
    except ValueError as e:
        logger.exception("Error deleting competitor")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error deleting competitor")
        raise HTTPException(status_code=500, detail=f"Error deleting competitor: {str(e)}")


@router.post(
    "/competitors/{competitor_id}/monitor",
    response_model=CompetitorMonitoringResultResponse,
    tags=["analytics", "competitors"],
)
async def monitor_competitor(
    competitor_id: str,
    db: AsyncSession = Depends(get_db),
) -> CompetitorMonitoringResultResponse:
    """
    Manually trigger monitoring for a specific competitor.

    Returns:
        Monitoring result with snapshot and analysis.
    """
    try:
        competitor_id_uuid = UUID(competitor_id)
        service = CompetitorMonitoringService(db)

        result = await service.monitor_competitor(competitor_id_uuid)

        return CompetitorMonitoringResultResponse(
            snapshot_id=result.get("snapshot_id"),
            competitor_id=result["competitor_id"],
            monitored_at=result["monitored_at"],
            metrics=result.get("metrics"),
            analysis=result.get("analysis"),
        )
    except ValueError as e:
        logger.exception("Error monitoring competitor")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error monitoring competitor")
        raise HTTPException(status_code=500, detail=f"Error monitoring competitor: {str(e)}")


@router.post(
    "/competitors/monitor-all",
    response_model=list[CompetitorMonitoringResultResponse],
    tags=["analytics", "competitors"],
)
async def monitor_all_competitors(
    db: AsyncSession = Depends(get_db),
) -> list[CompetitorMonitoringResultResponse]:
    """
    Monitor all competitors that are due for monitoring.

    Returns:
        List of monitoring results.
    """
    try:
        service = CompetitorMonitoringService(db)

        results = await service.monitor_all_due_competitors()

        return [
            CompetitorMonitoringResultResponse(
                snapshot_id=r.get("snapshot_id"),
                competitor_id=r["competitor_id"],
                monitored_at=r["monitored_at"],
                metrics=r.get("metrics"),
                analysis=r.get("analysis"),
                error=r.get("error"),
            )
            for r in results
        ]
    except Exception as e:
        logger.exception("Error monitoring all competitors")
        raise HTTPException(status_code=500, detail=f"Error monitoring all competitors: {str(e)}")


@router.get("/competitors/{competitor_id}/history", tags=["analytics", "competitors"])
async def get_competitor_history(
    competitor_id: str,
    limit: int = Query(100, description="Maximum number of snapshots to return"),
    start_date: datetime | None = Query(None, description="Start date filter"),
    end_date: datetime | None = Query(None, description="End date filter"),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """
    Get monitoring history for a competitor.

    Returns:
        List of monitoring snapshots.
    """
    try:
        competitor_id_uuid = UUID(competitor_id)
        service = CompetitorMonitoringService(db)

        history = await service.get_monitoring_history(
            competitor_id_uuid, limit=limit, start_date=start_date, end_date=end_date
        )

        return history
    except ValueError as e:
        logger.exception("Error getting competitor history")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error getting competitor history")
        raise HTTPException(status_code=500, detail=f"Error getting competitor history: {str(e)}")


@router.get("/competitors/{competitor_id}/trends", tags=["analytics", "competitors"])
async def get_competitor_trends(
    competitor_id: str,
    days: int = Query(30, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get trend analysis for a competitor.

    Returns:
        Trend analysis with changes and growth rates.
    """
    try:
        competitor_id_uuid = UUID(competitor_id)
        service = CompetitorMonitoringService(db)

        trends = await service.get_competitor_trends(competitor_id_uuid, days=days)

        return trends
    except ValueError as e:
        logger.exception("Error getting competitor trends")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error getting competitor trends")
        raise HTTPException(status_code=500, detail=f"Error getting competitor trends: {str(e)}")


# ===== Market Trend Prediction Endpoints =====

class MarketTrendPredictionResponse(BaseModel):
    """Response model for market trend predictions."""

    prediction_date: str
    days_ahead: int
    historical_days: int
    platform: Optional[str]
    character_id: Optional[str]
    hashtag_predictions: list[dict[str, Any]]
    content_type_predictions: list[dict[str, Any]]
    total_hashtag_predictions: int
    total_content_type_predictions: int


@router.get(
    "/trends/predictions",
    response_model=MarketTrendPredictionResponse,
    tags=["analytics", "trends", "prediction"],
)
async def get_market_trend_predictions(
    days_ahead: int = Query(default=7, ge=1, le=30, description="Number of days into the future to predict"),
    historical_days: int = Query(default=60, ge=7, le=365, description="Number of days of historical data to analyze"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    character_id: Optional[str] = Query(None, description="Filter by character ID"),
    hashtag_limit: int = Query(default=20, ge=1, le=100, description="Maximum number of hashtag predictions"),
    content_type_limit: int = Query(default=10, ge=1, le=50, description="Maximum number of content type predictions"),
    db: AsyncSession = Depends(get_db),
) -> MarketTrendPredictionResponse:
    """
    Predict future market trends for hashtags and content types.
    
    Uses historical data to forecast which hashtags and content types
    are likely to trend in the future based on growth patterns, engagement
    trends, and velocity analysis.
    
    Returns predictions with confidence scores for:
    - Hashtags likely to trend
    - Content types likely to perform well
    """
    try:
        service = MarketTrendPredictionService(db)

        # Parse character_id if provided
        character_id_uuid = None
        if character_id:
            try:
                character_id_uuid = UUID(character_id)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid character_id format: {character_id}"
                )

        predictions = await service.get_market_trend_predictions(
            days_ahead=days_ahead,
            historical_days=historical_days,
            platform=platform,
            character_id=character_id_uuid,
            hashtag_limit=hashtag_limit,
            content_type_limit=content_type_limit,
        )

        return MarketTrendPredictionResponse(**predictions)
    except Exception as e:
        logger.exception("Error getting market trend predictions")
        raise HTTPException(
            status_code=500, detail=f"Error getting predictions: {str(e)}"
        )
