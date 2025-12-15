"""Content scheduling API endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.content import ScheduledPost
from app.models.character import Character

router = APIRouter()


class ScheduledPostCreate(BaseModel):
    """Request model for creating a scheduled post."""

    character_id: str = Field(..., description="Character ID")
    content_id: Optional[str] = Field(default=None, description="Content ID (optional)")
    scheduled_time: datetime = Field(..., description="When to post (ISO 8601 datetime)")
    timezone: Optional[str] = Field(default=None, description="Timezone (e.g., 'America/New_York')")
    platform: Optional[str] = Field(default=None, description="Platform (instagram, twitter, facebook, etc.)")
    caption: Optional[str] = Field(default=None, description="Post caption/text")
    post_settings: Optional[dict] = Field(default=None, description="Platform-specific settings")


class ScheduledPostUpdate(BaseModel):
    """Request model for updating a scheduled post."""

    scheduled_time: Optional[datetime] = Field(default=None, description="New scheduled time")
    timezone: Optional[str] = Field(default=None, description="Timezone")
    platform: Optional[str] = Field(default=None, description="Platform")
    caption: Optional[str] = Field(default=None, description="Post caption/text")
    post_settings: Optional[dict] = Field(default=None, description="Platform-specific settings")
    status: Optional[str] = Field(default=None, pattern="^(pending|posted|cancelled|failed)$", description="Status")


class ScheduledPostResponse(BaseModel):
    """Response model for scheduled post."""

    id: str
    character_id: str
    content_id: Optional[str]
    scheduled_time: datetime
    timezone: Optional[str]
    status: str
    platform: Optional[str]
    caption: Optional[str]
    post_settings: Optional[dict]
    posted_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("", response_model=ScheduledPostResponse)
async def create_scheduled_post(
    req: ScheduledPostCreate,
    db: AsyncSession = Depends(get_db),
) -> ScheduledPostResponse:
    """
    Create a new scheduled post.

    Schedules content to be posted at a future time. Content ID is optional
    (can schedule posts for content that will be generated later).
    """
    # Verify character exists
    character_result = await db.execute(select(Character).where(Character.id == UUID(req.character_id)))
    character = character_result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # Create scheduled post
    scheduled_post = ScheduledPost(
        character_id=UUID(req.character_id),
        content_id=UUID(req.content_id) if req.content_id else None,
        scheduled_time=req.scheduled_time,
        timezone=req.timezone,
        platform=req.platform,
        caption=req.caption,
        post_settings=req.post_settings,
        status="pending",
    )

    db.add(scheduled_post)
    await db.commit()
    await db.refresh(scheduled_post)

    return ScheduledPostResponse.model_validate(scheduled_post)


@router.get("", response_model=dict)
async def list_scheduled_posts(
    character_id: Optional[str] = Query(default=None, description="Filter by character ID"),
    status: Optional[str] = Query(default=None, pattern="^(pending|posted|cancelled|failed)$", description="Filter by status"),
    platform: Optional[str] = Query(default=None, description="Filter by platform"),
    start_date: Optional[datetime] = Query(default=None, description="Filter by start date (ISO 8601)"),
    end_date: Optional[datetime] = Query(default=None, description="Filter by end date (ISO 8601)"),
    limit: int = Query(default=50, ge=1, le=500, description="Limit results"),
    offset: int = Query(default=0, ge=0, description="Offset results"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    List scheduled posts with optional filters.

    Supports filtering by character, status, platform, and date range.
    """
    query = select(ScheduledPost).options(selectinload(ScheduledPost.character), selectinload(ScheduledPost.content))

    # Apply filters
    conditions = []
    if character_id:
        conditions.append(ScheduledPost.character_id == UUID(character_id))
    if status:
        conditions.append(ScheduledPost.status == status)
    if platform:
        conditions.append(ScheduledPost.platform == platform)
    if start_date:
        conditions.append(ScheduledPost.scheduled_time >= start_date)
    if end_date:
        conditions.append(ScheduledPost.scheduled_time <= end_date)

    if conditions:
        query = query.where(and_(*conditions))

    # Order by scheduled_time
    query = query.order_by(ScheduledPost.scheduled_time.asc())

    # Get total count
    count_query = select(func.count()).select_from(ScheduledPost)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.limit(limit).offset(offset)

    # Execute query
    result = await db.execute(query)
    posts = result.scalars().all()

    return {
        "ok": True,
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [ScheduledPostResponse.model_validate(post) for post in posts],
    }


@router.get("/{scheduled_post_id}", response_model=ScheduledPostResponse)
async def get_scheduled_post(
    scheduled_post_id: str,
    db: AsyncSession = Depends(get_db),
) -> ScheduledPostResponse:
    """Get a specific scheduled post by ID."""
    result = await db.execute(
        select(ScheduledPost)
        .options(selectinload(ScheduledPost.character), selectinload(ScheduledPost.content))
        .where(ScheduledPost.id == UUID(scheduled_post_id))
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Scheduled post not found")

    return ScheduledPostResponse.model_validate(post)


@router.put("/{scheduled_post_id}", response_model=ScheduledPostResponse)
async def update_scheduled_post(
    scheduled_post_id: str,
    req: ScheduledPostUpdate,
    db: AsyncSession = Depends(get_db),
) -> ScheduledPostResponse:
    """
    Update a scheduled post.

    Only pending posts can be updated. Posted, cancelled, or failed posts
    cannot be modified (except status can be changed to cancelled).
    """
    result = await db.execute(select(ScheduledPost).where(ScheduledPost.id == UUID(scheduled_post_id)))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Scheduled post not found")

    # Only allow updates to pending posts (or allow cancelling any post)
    if post.status != "pending" and req.status != "cancelled":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot update scheduled post with status '{post.status}'. Only pending posts can be updated, or you can cancel any post.",
        )

    # Update fields
    if req.scheduled_time is not None:
        post.scheduled_time = req.scheduled_time
    if req.timezone is not None:
        post.timezone = req.timezone
    if req.platform is not None:
        post.platform = req.platform
    if req.caption is not None:
        post.caption = req.caption
    if req.post_settings is not None:
        post.post_settings = req.post_settings
    if req.status is not None:
        post.status = req.status
        if req.status == "posted":
            post.posted_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(post)

    return ScheduledPostResponse.model_validate(post)


@router.delete("/{scheduled_post_id}", response_model=dict)
async def delete_scheduled_post(
    scheduled_post_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Delete a scheduled post.

    Only pending posts can be deleted. Other posts should be cancelled instead.
    """
    result = await db.execute(select(ScheduledPost).where(ScheduledPost.id == UUID(scheduled_post_id)))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Scheduled post not found")

    if post.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete scheduled post with status '{post.status}'. Only pending posts can be deleted.",
        )

    await db.delete(post)
    await db.commit()

    return {"ok": True, "message": "Scheduled post deleted"}


@router.post("/{scheduled_post_id}/cancel", response_model=ScheduledPostResponse)
async def cancel_scheduled_post(
    scheduled_post_id: str,
    db: AsyncSession = Depends(get_db),
) -> ScheduledPostResponse:
    """Cancel a scheduled post (sets status to 'cancelled')."""
    result = await db.execute(select(ScheduledPost).where(ScheduledPost.id == UUID(scheduled_post_id)))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Scheduled post not found")

    if post.status in ("posted", "cancelled"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel scheduled post with status '{post.status}'.",
        )

    post.status = "cancelled"
    await db.commit()
    await db.refresh(post)

    return ScheduledPostResponse.model_validate(post)

