"""A/B testing API endpoints for managing experiments."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.ab_test import ABTest, ABTestStatus
from app.services.ab_testing_service import ABTestingService

logger = get_logger(__name__)

router = APIRouter()


class CreateABTestRequest(BaseModel):
    """Request model for creating an A/B test."""

    character_id: UUID = Field(..., description="Character ID for the test")
    name: str = Field(..., description="Test name", min_length=1, max_length=255)
    test_type: str = Field(
        ...,
        description="Type of test (content, caption, hashtags, posting_time, image_style, engagement_strategy)",
    )
    variant_a_name: str = Field(default="Variant A", description="Name for variant A", max_length=100)
    variant_b_name: str = Field(default="Variant B", description="Name for variant B", max_length=100)
    variant_a_config: Optional[dict[str, Any]] = Field(None, description="Configuration for variant A")
    variant_b_config: Optional[dict[str, Any]] = Field(None, description="Configuration for variant B")
    description: Optional[str] = Field(None, description="Test description")
    start_date: Optional[datetime] = Field(None, description="Test start date")
    end_date: Optional[datetime] = Field(None, description="Test end date")
    target_sample_size: Optional[int] = Field(None, description="Target sample size per variant", ge=1)
    significance_level: Decimal = Field(default=Decimal("0.05"), description="Statistical significance level", ge=0, le=1)


class ABTestResponse(BaseModel):
    """Response model for A/B test."""

    id: UUID
    character_id: UUID
    name: str
    description: Optional[str]
    test_type: str
    status: str
    variant_a_name: str
    variant_b_name: str
    variant_a_config: Optional[dict[str, Any]]
    variant_b_config: Optional[dict[str, Any]]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    target_sample_size: Optional[int]
    significance_level: Decimal
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm(cls, test: ABTest) -> "ABTestResponse":
        """Create response from ORM model."""
        return cls(
            id=test.id,
            character_id=test.character_id,
            name=test.name,
            description=test.description,
            test_type=test.test_type,
            status=test.status,
            variant_a_name=test.variant_a_name,
            variant_b_name=test.variant_b_name,
            variant_a_config=test.variant_a_config,
            variant_b_config=test.variant_b_config,
            start_date=test.start_date,
            end_date=test.end_date,
            target_sample_size=test.target_sample_size,
            significance_level=test.significance_level,
            created_at=test.created_at,
            updated_at=test.updated_at,
        )


class AssignVariantRequest(BaseModel):
    """Request model for assigning a post to a variant."""

    post_id: UUID = Field(..., description="Post ID to assign")
    variant_name: str = Field(..., description="Variant name (variant_a_name or variant_b_name)")
    content_id: Optional[UUID] = Field(None, description="Optional content ID if testing content variations")


@router.post("/ab-tests", response_model=ABTestResponse, status_code=201)
async def create_ab_test(
    request: CreateABTestRequest,
    db: AsyncSession = Depends(get_db),
) -> ABTestResponse:
    """Create a new A/B test.
    
    Creates a new A/B test for experimenting with different content strategies,
    captions, hashtags, posting times, or other variables.
    """
    try:
        service = ABTestingService(db)
        test = await service.create_test(
            character_id=request.character_id,
            name=request.name,
            test_type=request.test_type,
            variant_a_name=request.variant_a_name,
            variant_b_name=request.variant_b_name,
            variant_a_config=request.variant_a_config,
            variant_b_config=request.variant_b_config,
            description=request.description,
            start_date=request.start_date,
            end_date=request.end_date,
            target_sample_size=request.target_sample_size,
            significance_level=request.significance_level,
        )
        return ABTestResponse.from_orm(test)
    except Exception as e:
        logger.error(f"Error creating A/B test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ab-tests/{test_id}", response_model=ABTestResponse)
async def get_ab_test(
    test_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ABTestResponse:
    """Get an A/B test by ID."""
    service = ABTestingService(db)
    test = await service.get_test(test_id)
    if not test:
        raise HTTPException(status_code=404, detail=f"A/B test {test_id} not found")
    return ABTestResponse.from_orm(test)


@router.get("/ab-tests", response_model=list[ABTestResponse])
async def list_ab_tests(
    character_id: Optional[UUID] = Query(None, description="Filter by character ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    test_type: Optional[str] = Query(None, description="Filter by test type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
) -> list[ABTestResponse]:
    """List A/B tests with optional filters."""
    service = ABTestingService(db)
    tests = await service.list_tests(
        character_id=character_id,
        status=status,
        test_type=test_type,
        limit=limit,
        offset=offset,
    )
    return [ABTestResponse.from_orm(test) for test in tests]


@router.post("/ab-tests/{test_id}/start", response_model=ABTestResponse)
async def start_ab_test(
    test_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ABTestResponse:
    """Start an A/B test."""
    try:
        service = ABTestingService(db)
        test = await service.start_test(test_id)
        return ABTestResponse.from_orm(test)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting A/B test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ab-tests/{test_id}/pause", response_model=ABTestResponse)
async def pause_ab_test(
    test_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ABTestResponse:
    """Pause a running A/B test."""
    try:
        service = ABTestingService(db)
        test = await service.pause_test(test_id)
        return ABTestResponse.from_orm(test)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error pausing A/B test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ab-tests/{test_id}/resume", response_model=ABTestResponse)
async def resume_ab_test(
    test_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ABTestResponse:
    """Resume a paused A/B test."""
    try:
        service = ABTestingService(db)
        test = await service.resume_test(test_id)
        return ABTestResponse.from_orm(test)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error resuming A/B test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ab-tests/{test_id}/complete", response_model=ABTestResponse)
async def complete_ab_test(
    test_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ABTestResponse:
    """Complete an A/B test."""
    try:
        service = ABTestingService(db)
        test = await service.complete_test(test_id)
        return ABTestResponse.from_orm(test)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing A/B test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ab-tests/{test_id}/assign", status_code=201)
async def assign_variant(
    test_id: UUID,
    request: AssignVariantRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Assign a post to a test variant."""
    try:
        service = ABTestingService(db)
        variant = await service.assign_variant(
            test_id=test_id,
            post_id=request.post_id,
            variant_name=request.variant_name,
            content_id=request.content_id,
        )
        return {
            "id": str(variant.id),
            "test_id": str(variant.test_id),
            "variant_name": variant.variant_name,
            "post_id": str(variant.post_id) if variant.post_id else None,
            "content_id": str(variant.content_id) if variant.content_id else None,
            "assigned_at": variant.assigned_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error assigning variant: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ab-tests/{test_id}/results")
async def get_test_results(
    test_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get statistical results for an A/B test."""
    try:
        service = ABTestingService(db)
        results = await service.get_test_results(test_id)
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting test results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
