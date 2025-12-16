"""Content intelligence API endpoints for trending topics, content calendar, posting times, variations, and engagement prediction."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.content_intelligence_service import (
    ContentCalendarEntry,
    ContentIntelligenceService,
    ContentVariation,
    EngagementPrediction,
    OptimalPostingTime,
    TrendingTopic,
    content_intelligence_service,
)

router = APIRouter()


# ===== Request/Response Models =====

class TrendingTopicResponse(BaseModel):
    """Response model for trending topic."""

    keyword: str
    category: str
    trend_score: float
    growth_rate: float
    related_keywords: list[str]
    estimated_reach: int | None = None
    source: str = "manual"


class AddTrendingTopicRequest(BaseModel):
    """Request to add a trending topic."""

    keyword: str
    category: str
    trend_score: float = Field(ge=0.0, le=1.0)
    growth_rate: float
    related_keywords: list[str] = []
    estimated_reach: int | None = None
    source: str = "manual"


class ContentCalendarResponse(BaseModel):
    """Response model for content calendar entry."""

    date: str  # ISO format
    character_id: str | None
    content_type: str
    platform: str
    topic: str | None = None
    caption_template: str | None = None
    scheduled_time: str | None = None  # ISO format
    status: str
    notes: str | None = None


class GenerateCalendarRequest(BaseModel):
    """Request to generate content calendar."""

    start_date: str  # ISO format
    end_date: str  # ISO format
    character_id: str | None = None
    posts_per_day: int = Field(default=2, ge=1, le=10)
    platforms: list[str] | None = None


class OptimalPostingTimeResponse(BaseModel):
    """Response model for optimal posting time."""

    platform: str
    character_id: str | None
    day_of_week: int
    hour: int
    engagement_score: float
    confidence: float
    reasoning: str | None = None


class ContentVariationResponse(BaseModel):
    """Response model for content variation."""

    base_content_id: str
    variation_type: str
    variation_data: dict
    platform: str | None = None


class GenerateVariationsRequest(BaseModel):
    """Request to generate content variations."""

    base_content_id: str
    variation_types: list[str] | None = None
    count: int = Field(default=3, ge=1, le=10)


class EngagementPredictionRequest(BaseModel):
    """Request for engagement prediction."""

    platform: str
    content_type: str
    character_id: str | None = None
    content_metadata: dict | None = None


class EngagementPredictionResponse(BaseModel):
    """Response model for engagement prediction."""

    content_id: str | None
    platform: str
    predicted_likes: int
    predicted_comments: int
    predicted_shares: int
    predicted_reach: int
    confidence: float
    factors: dict


# ===== Trending Topics Endpoints =====

@router.get("/trending-topics", response_model=list[TrendingTopicResponse])
async def get_trending_topics(
    category: str | None = Query(default=None, description="Filter by category"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of topics"),
) -> list[TrendingTopicResponse]:
    """Get trending topics."""
    topics = content_intelligence_service.analyze_trending_topics(category=category, limit=limit)
    return [
        TrendingTopicResponse(
            keyword=t.keyword,
            category=t.category,
            trend_score=t.trend_score,
            growth_rate=t.growth_rate,
            related_keywords=t.related_keywords,
            estimated_reach=t.estimated_reach,
            source=t.source,
        )
        for t in topics
    ]


@router.post("/trending-topics", response_model=TrendingTopicResponse)
async def add_trending_topic(req: AddTrendingTopicRequest) -> TrendingTopicResponse:
    """Add a trending topic."""
    topic = TrendingTopic(
        keyword=req.keyword,
        category=req.category,
        trend_score=req.trend_score,
        growth_rate=req.growth_rate,
        related_keywords=req.related_keywords,
        estimated_reach=req.estimated_reach,
        source=req.source,
    )
    content_intelligence_service.add_trending_topic(topic)
    return TrendingTopicResponse(
        keyword=topic.keyword,
        category=topic.category,
        trend_score=topic.trend_score,
        growth_rate=topic.growth_rate,
        related_keywords=topic.related_keywords,
        estimated_reach=topic.estimated_reach,
        source=topic.source,
    )


@router.get("/trending-topics/character/{character_id}", response_model=list[TrendingTopicResponse])
async def get_trending_topics_for_character(
    character_id: UUID,
    character_interests: list[str] | None = Query(default=None, description="Character interest keywords"),
    limit: int = Query(default=5, ge=1, le=20),
) -> list[TrendingTopicResponse]:
    """Get trending topics relevant to a character's interests."""
    topics = content_intelligence_service.get_trending_topics_for_character(
        character_id=character_id,
        character_interests=character_interests,
        limit=limit,
    )
    return [
        TrendingTopicResponse(
            keyword=t.keyword,
            category=t.category,
            trend_score=t.trend_score,
            growth_rate=t.growth_rate,
            related_keywords=t.related_keywords,
            estimated_reach=t.estimated_reach,
            source=t.source,
        )
        for t in topics
    ]


# ===== Content Calendar Endpoints =====

@router.post("/content-calendar/generate", response_model=list[ContentCalendarResponse])
async def generate_content_calendar(req: GenerateCalendarRequest) -> list[ContentCalendarResponse]:
    """Generate a content calendar for a date range."""
    try:
        start_date = datetime.fromisoformat(req.start_date.replace("Z", "+00:00"))
        end_date = datetime.fromisoformat(req.end_date.replace("Z", "+00:00"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")

    character_id = UUID(req.character_id) if req.character_id else None

    calendar = content_intelligence_service.generate_content_calendar(
        start_date=start_date,
        end_date=end_date,
        character_id=character_id,
        posts_per_day=req.posts_per_day,
        platforms=req.platforms,
    )

    return [
        ContentCalendarResponse(
            date=e.date.isoformat(),
            character_id=str(e.character_id) if e.character_id else None,
            content_type=e.content_type,
            platform=e.platform,
            topic=e.topic,
            caption_template=e.caption_template,
            scheduled_time=e.scheduled_time.isoformat() if e.scheduled_time else None,
            status=e.status,
            notes=e.notes,
        )
        for e in calendar
    ]


@router.get("/content-calendar", response_model=list[ContentCalendarResponse])
async def get_content_calendar(
    start_date: str | None = Query(default=None, description="Start date (ISO format)"),
    end_date: str | None = Query(default=None, description="End date (ISO format)"),
    character_id: UUID | None = Query(default=None, description="Character ID filter"),
    platform: str | None = Query(default=None, description="Platform filter"),
) -> list[ContentCalendarResponse]:
    """Get content calendar entries with optional filters."""
    start = datetime.fromisoformat(start_date.replace("Z", "+00:00")) if start_date else None
    end = datetime.fromisoformat(end_date.replace("Z", "+00:00")) if end_date else None

    entries = content_intelligence_service.get_content_calendar(
        start_date=start,
        end_date=end,
        character_id=character_id,
        platform=platform,
    )

    return [
        ContentCalendarResponse(
            date=e.date.isoformat(),
            character_id=str(e.character_id) if e.character_id else None,
            content_type=e.content_type,
            platform=e.platform,
            topic=e.topic,
            caption_template=e.caption_template,
            scheduled_time=e.scheduled_time.isoformat() if e.scheduled_time else None,
            status=e.status,
            notes=e.notes,
        )
        for e in entries
    ]


# ===== Optimal Posting Time Endpoints =====

@router.get("/optimal-posting-time/{platform}", response_model=OptimalPostingTimeResponse)
async def get_optimal_posting_time(
    platform: str,
    character_id: UUID | None = Query(default=None, description="Character ID for personalized recommendations"),
    day_of_week: int | None = Query(default=None, ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)"),
) -> OptimalPostingTimeResponse:
    """Calculate optimal posting time for a platform."""
    posting_time = content_intelligence_service.calculate_optimal_posting_time(
        platform=platform,
        character_id=character_id,
        day_of_week=day_of_week,
    )

    return OptimalPostingTimeResponse(
        platform=posting_time.platform,
        character_id=str(posting_time.character_id) if posting_time.character_id else None,
        day_of_week=posting_time.day_of_week,
        hour=posting_time.hour,
        engagement_score=posting_time.engagement_score,
        confidence=posting_time.confidence,
        reasoning=posting_time.reasoning,
    )


@router.post("/optimal-posting-time/record")
async def record_posting_time_performance(
    platform: str,
    posting_time: str,  # ISO format
    engagement_metrics: dict[str, int],
    character_id: UUID | None = None,
) -> dict[str, str]:
    """Record posting time performance for learning."""
    try:
        post_time = datetime.fromisoformat(posting_time.replace("Z", "+00:00"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")

    content_intelligence_service.record_posting_time_performance(
        platform=platform,
        posting_time=post_time,
        engagement_metrics=engagement_metrics,
        character_id=character_id,
    )

    return {"ok": True, "message": "Posting time performance recorded"}


# ===== Content Variation Endpoints =====

@router.post("/content-variations/generate", response_model=list[ContentVariationResponse])
async def generate_content_variations(req: GenerateVariationsRequest) -> list[ContentVariationResponse]:
    """Generate variations of content."""
    try:
        base_id = UUID(req.base_content_id) if req.base_content_id else req.base_content_id
    except ValueError:
        base_id = req.base_content_id  # Keep as string if not valid UUID

    variations = content_intelligence_service.generate_content_variations(
        base_content_id=base_id,
        variation_types=req.variation_types,
        count=req.count,
    )

    return [
        ContentVariationResponse(
            base_content_id=str(v.base_content_id),
            variation_type=v.variation_type,
            variation_data=v.variation_data,
            platform=v.platform,
        )
        for v in variations
    ]


@router.get("/content-variations/platform/{base_content_id}", response_model=ContentVariationResponse)
async def get_platform_variation(
    base_content_id: str,
    platform: str = Query(..., description="Target platform"),
) -> ContentVariationResponse:
    """Get platform-optimized variation of content."""
    try:
        base_id = UUID(base_content_id) if base_content_id else base_content_id
    except ValueError:
        base_id = base_content_id  # Keep as string if not valid UUID

    variation = content_intelligence_service.get_variation_for_platform(
        base_content_id=base_id,
        platform=platform,
    )

    if not variation:
        raise HTTPException(status_code=404, detail="Variation not found")

    return ContentVariationResponse(
        base_content_id=str(variation.base_content_id),
        variation_type=variation.variation_type,
        variation_data=variation.variation_data,
        platform=variation.platform,
    )


# ===== Engagement Prediction Endpoints =====

@router.post("/engagement-prediction", response_model=EngagementPredictionResponse)
async def predict_engagement(req: EngagementPredictionRequest) -> EngagementPredictionResponse:
    """Predict engagement for content."""
    character_id = UUID(req.character_id) if req.character_id else None

    prediction = content_intelligence_service.predict_engagement(
        platform=req.platform,
        content_type=req.content_type,
        character_id=character_id,
        content_metadata=req.content_metadata,
    )

    return EngagementPredictionResponse(
        content_id=str(prediction.content_id) if prediction.content_id else None,
        platform=prediction.platform,
        predicted_likes=prediction.predicted_likes,
        predicted_comments=prediction.predicted_comments,
        predicted_shares=prediction.predicted_shares,
        predicted_reach=prediction.predicted_reach,
        confidence=prediction.confidence,
        factors=prediction.factors,
    )


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "content_intelligence"}

