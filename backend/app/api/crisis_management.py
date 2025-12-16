"""Crisis management API endpoints for handling content takedowns."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.services.crisis_management_service import CrisisManagementService

logger = get_logger(__name__)

router = APIRouter()


class TakedownReportRequest(BaseModel):
    """Request model for reporting a content takedown."""

    post_id: str = Field(..., description="Post ID that was taken down")
    platform: str = Field(..., description="Platform name (instagram, twitter, facebook, etc.)")
    reason: str = Field(..., description="Reason for takedown (copyright, community_guidelines, etc.)")
    takedown_type: str = Field(
        default="platform",
        description="Type of takedown (platform, dmca, user_report, etc.)"
    )
    notified_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp when takedown was notified (defaults to now)"
    )


class BatchTakedownReportRequest(BaseModel):
    """Request model for batch reporting content takedowns."""

    post_ids: list[str] = Field(..., description="List of post IDs that were taken down")
    platform: str = Field(..., description="Platform name")
    reason: str = Field(..., description="Reason for takedown")
    takedown_type: str = Field(
        default="platform",
        description="Type of takedown"
    )


class TakedownReportResponse(BaseModel):
    """Response model for takedown report."""

    ok: bool
    post_id: str
    status: str
    message: str


class BatchTakedownReportResponse(BaseModel):
    """Response model for batch takedown report."""

    ok: bool
    successful: int
    failed: int
    message: str


class TakedownStatisticsResponse(BaseModel):
    """Response model for takedown statistics."""

    total_takedowns: int
    by_platform: dict[str, int]
    by_reason: dict[str, int]
    period: dict[str, Optional[str]]


@router.post("/takedown", response_model=TakedownReportResponse)
async def report_takedown(
    req: TakedownReportRequest,
    db: AsyncSession = Depends(get_db),
) -> TakedownReportResponse:
    """
    Report a content takedown from a platform.
    
    Updates the post status to "deleted" and logs the takedown event.
    This endpoint should be called when content is removed by a platform
    due to policy violations, copyright issues, or other compliance reasons.
    
    Args:
        req: Takedown report request with post ID, platform, and reason
        db: Database session dependency
        
    Returns:
        TakedownReportResponse with updated post status
        
    Raises:
        HTTPException: 400 if validation fails, 404 if post not found
    """
    try:
        post_uuid = UUID(req.post_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid post_id format. Must be UUID.")

    try:
        notified_at = None
        if req.notified_at:
            notified_at = datetime.fromisoformat(req.notified_at.replace("Z", "+00:00"))

        service = CrisisManagementService(db)
        post = await service.report_takedown(
            post_id=post_uuid,
            platform=req.platform,
            reason=req.reason,
            takedown_type=req.takedown_type,
            notified_at=notified_at,
        )

        await db.commit()

        return TakedownReportResponse(
            ok=True,
            post_id=str(post.id),
            status=post.status,
            message=f"Takedown reported successfully for post {req.post_id}"
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error reporting takedown: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to report takedown: {str(e)}")


@router.post("/takedown/batch", response_model=BatchTakedownReportResponse)
async def batch_report_takedowns(
    req: BatchTakedownReportRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchTakedownReportResponse:
    """
    Batch report multiple content takedowns.
    
    Reports multiple posts as taken down in a single operation.
    Useful for handling bulk takedown notifications from platforms.
    
    Args:
        req: Batch takedown report request with list of post IDs
        db: Database session dependency
        
    Returns:
        BatchTakedownReportResponse with success/failure counts
        
    Raises:
        HTTPException: 400 if validation fails
    """
    try:
        post_uuids = [UUID(pid) for pid in req.post_ids]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid post_id format: {e}")

    try:
        service = CrisisManagementService(db)
        successful, failed = await service.batch_report_takedowns(
            post_ids=post_uuids,
            platform=req.platform,
            reason=req.reason,
            takedown_type=req.takedown_type,
        )

        await db.commit()

        return BatchTakedownReportResponse(
            ok=True,
            successful=successful,
            failed=failed,
            message=f"Batch takedown report: {successful} successful, {failed} failed"
        )

    except Exception as e:
        logger.error(f"Error in batch takedown report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to report batch takedowns: {str(e)}")


@router.get("/statistics", response_model=TakedownStatisticsResponse)
async def get_takedown_statistics(
    character_id: Optional[str] = Query(default=None, description="Filter by character ID"),
    platform: Optional[str] = Query(default=None, description="Filter by platform"),
    start_date: Optional[str] = Query(default=None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(default=None, description="End date (ISO format)"),
    db: AsyncSession = Depends(get_db),
) -> TakedownStatisticsResponse:
    """
    Get takedown statistics.
    
    Returns aggregated statistics about content takedowns including:
    - Total takedowns
    - Takedowns by platform
    - Takedowns by reason
    
    Args:
        character_id: Optional character ID to filter by
        platform: Optional platform to filter by
        start_date: Optional start date for date range (ISO format)
        end_date: Optional end date for date range (ISO format)
        db: Database session dependency
        
    Returns:
        TakedownStatisticsResponse with aggregated statistics
    """
    try:
        char_uuid = UUID(character_id) if character_id else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid character_id format. Must be UUID.")

    try:
        start_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))

        end_dt = None
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        service = CrisisManagementService(db)
        stats = await service.get_takedown_statistics(
            character_id=char_uuid,
            platform=platform,
            start_date=start_dt,
            end_date=end_dt,
        )

        return TakedownStatisticsResponse(**stats)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Error getting takedown statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.post("/content/{content_id}/review")
async def mark_content_for_review(
    content_id: str,
    review_reason: str = Query(..., description="Reason for review"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Mark content for manual review due to potential issues.
    
    Marks content as rejected and requires manual review before it can be
    used again. Useful for flagging content that may violate policies.
    
    Args:
        content_id: UUID of the content to mark
        review_reason: Reason for review
        db: Database session dependency
        
    Returns:
        Response with updated content status
        
    Raises:
        HTTPException: 400 if validation fails, 404 if content not found
    """
    try:
        content_uuid = UUID(content_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid content_id format. Must be UUID.")

    try:
        service = CrisisManagementService(db)
        content = await service.mark_content_for_review(
            content_id=content_uuid,
            review_reason=review_reason,
        )

        await db.commit()

        return {
            "ok": True,
            "content_id": str(content.id),
            "approval_status": content.approval_status,
            "message": f"Content {content_id} marked for review: {review_reason}"
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error marking content for review: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to mark content for review: {str(e)}")

