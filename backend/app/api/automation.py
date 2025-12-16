"""Automation API endpoints for managing automation rules."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.services.automation_rule_service import AutomationRuleService, AutomationRuleServiceError
from app.services.automation_scheduler_service import AutomationSchedulerService, AutomationSchedulerError

logger = get_logger(__name__)

router = APIRouter()


# Request/Response Models

class AutomationRuleCreate(BaseModel):
    """Request model for creating an automation rule."""

    character_id: str
    name: str
    description: str | None = None
    is_enabled: bool = True
    trigger_type: str  # schedule, event, manual
    trigger_config: dict
    action_type: str  # comment, like, follow
    action_config: dict
    platforms: list[str]
    platform_account_id: str | None = None
    max_executions_per_day: int | None = None
    max_executions_per_week: int | None = None
    cooldown_minutes: int = 60


class AutomationRuleUpdate(BaseModel):
    """Request model for updating an automation rule."""

    name: str | None = None
    description: str | None = None
    is_enabled: bool | None = None
    trigger_type: str | None = None
    trigger_config: dict | None = None
    action_type: str | None = None
    action_config: dict | None = None
    platforms: list[str] | None = None
    max_executions_per_day: int | None = None
    max_executions_per_week: int | None = None
    cooldown_minutes: int | None = None


class AutomationRuleResponse(BaseModel):
    """Response model for automation rule."""

    id: str
    character_id: str
    platform_account_id: str | None
    name: str
    description: str | None
    is_enabled: bool
    trigger_type: str
    trigger_config: dict
    action_type: str
    action_config: dict
    platforms: list[str]
    max_executions_per_day: int | None
    max_executions_per_week: int | None
    cooldown_minutes: int
    times_executed: int
    last_executed_at: str | None
    success_count: int
    failure_count: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class AutomationRuleExecuteRequest(BaseModel):
    """Request model for executing an automation rule."""

    platform_account_id: str | None = None


class AutomationRuleExecuteResponse(BaseModel):
    """Response model for automation rule execution."""

    success: bool
    rule_id: str
    action_type: str
    result: dict
    error: str | None = None


# CRUD Endpoints

@router.post("/rules", response_model=AutomationRuleResponse, tags=["automation"])
async def create_automation_rule(
    req: AutomationRuleCreate,
    db: AsyncSession = Depends(get_db),
) -> AutomationRuleResponse:
    """
    Create a new automation rule.

    Args:
        req: Automation rule creation request.
        db: Database session dependency.

    Returns:
        Created automation rule.

    Raises:
        HTTPException: 400 if validation fails, 500 if creation fails.
    """
    try:
        service = AutomationRuleService(db)

        character_uuid = UUID(req.character_id)
        platform_account_uuid = UUID(req.platform_account_id) if req.platform_account_id else None

        rule = await service.create_rule(
            character_id=character_uuid,
            name=req.name,
            description=req.description,
            is_enabled=req.is_enabled,
            trigger_type=req.trigger_type,
            trigger_config=req.trigger_config,
            action_type=req.action_type,
            action_config=req.action_config,
            platforms=req.platforms,
            platform_account_id=platform_account_uuid,
            max_executions_per_day=req.max_executions_per_day,
            max_executions_per_week=req.max_executions_per_week,
            cooldown_minutes=req.cooldown_minutes,
        )

        return AutomationRuleResponse.model_validate(rule)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid UUID format: {exc}")
    except AutomationRuleServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Unexpected error creating automation rule: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")


@router.get("/rules/{rule_id}", response_model=AutomationRuleResponse, tags=["automation"])
async def get_automation_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
) -> AutomationRuleResponse:
    """
    Get an automation rule by ID.

    Args:
        rule_id: Automation rule UUID.
        db: Database session dependency.

    Returns:
        Automation rule.

    Raises:
        HTTPException: 404 if rule not found, 400 if UUID invalid.
    """
    try:
        service = AutomationRuleService(db)
        rule_uuid = UUID(rule_id)
        rule = await service.get_rule(rule_uuid)

        if not rule:
            raise HTTPException(status_code=404, detail=f"Automation rule {rule_id} not found")

        return AutomationRuleResponse.model_validate(rule)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid UUID format: {exc}")
    except Exception as exc:
        logger.error(f"Unexpected error getting automation rule: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")


@router.get("/rules", response_model=list[AutomationRuleResponse], tags=["automation"])
async def list_automation_rules(
    character_id: str | None = Query(default=None, description="Filter by character ID"),
    platform_account_id: str | None = Query(default=None, description="Filter by platform account ID"),
    is_enabled: bool | None = Query(default=None, description="Filter by enabled status"),
    action_type: str | None = Query(default=None, description="Filter by action type"),
    db: AsyncSession = Depends(get_db),
) -> list[AutomationRuleResponse]:
    """
    List automation rules with optional filters.

    Args:
        character_id: Filter by character ID (optional).
        platform_account_id: Filter by platform account ID (optional).
        is_enabled: Filter by enabled status (optional).
        action_type: Filter by action type (optional).
        db: Database session dependency.

    Returns:
        List of automation rules.

    Raises:
        HTTPException: 400 if UUID invalid, 500 if query fails.
    """
    try:
        service = AutomationRuleService(db)

        character_uuid = UUID(character_id) if character_id else None
        platform_account_uuid = UUID(platform_account_id) if platform_account_id else None

        rules = await service.list_rules(
            character_id=character_uuid,
            platform_account_id=platform_account_uuid,
            is_enabled=is_enabled,
            action_type=action_type,
        )

        return [AutomationRuleResponse.model_validate(rule) for rule in rules]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid UUID format: {exc}")
    except Exception as exc:
        logger.error(f"Unexpected error listing automation rules: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")


@router.put("/rules/{rule_id}", response_model=AutomationRuleResponse, tags=["automation"])
async def update_automation_rule(
    rule_id: str,
    req: AutomationRuleUpdate,
    db: AsyncSession = Depends(get_db),
) -> AutomationRuleResponse:
    """
    Update an automation rule.

    Args:
        rule_id: Automation rule UUID.
        req: Automation rule update request.
        db: Database session dependency.

    Returns:
        Updated automation rule.

    Raises:
        HTTPException: 404 if rule not found, 400 if validation fails, 500 if update fails.
    """
    try:
        service = AutomationRuleService(db)
        rule_uuid = UUID(rule_id)

        rule = await service.update_rule(
            rule_id=rule_uuid,
            name=req.name,
            description=req.description,
            is_enabled=req.is_enabled,
            trigger_type=req.trigger_type,
            trigger_config=req.trigger_config,
            action_type=req.action_type,
            action_config=req.action_config,
            platforms=req.platforms,
            max_executions_per_day=req.max_executions_per_day,
            max_executions_per_week=req.max_executions_per_week,
            cooldown_minutes=req.cooldown_minutes,
        )

        return AutomationRuleResponse.model_validate(rule)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid UUID format: {exc}")
    except AutomationRuleServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error(f"Unexpected error updating automation rule: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")


@router.delete("/rules/{rule_id}", tags=["automation"])
async def delete_automation_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Delete an automation rule.

    Args:
        rule_id: Automation rule UUID.
        db: Database session dependency.

    Returns:
        Success message.

    Raises:
        HTTPException: 404 if rule not found, 400 if UUID invalid, 500 if deletion fails.
    """
    try:
        service = AutomationRuleService(db)
        rule_uuid = UUID(rule_id)

        await service.delete_rule(rule_uuid)

        return {"success": True, "message": f"Automation rule {rule_id} deleted"}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid UUID format: {exc}")
    except AutomationRuleServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error(f"Unexpected error deleting automation rule: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")


# Execution Endpoints

@router.post("/rules/{rule_id}/execute", response_model=AutomationRuleExecuteResponse, tags=["automation"])
async def execute_automation_rule(
    rule_id: str,
    req: AutomationRuleExecuteRequest,
    db: AsyncSession = Depends(get_db),
) -> AutomationRuleExecuteResponse:
    """
    Execute an automation rule.

    Args:
        rule_id: Automation rule UUID.
        req: Execution request (optional platform_account_id override).
        db: Database session dependency.

    Returns:
        Execution result.

    Raises:
        HTTPException: 404 if rule not found, 400 if execution fails, 500 if unexpected error.
    """
    try:
        scheduler = AutomationSchedulerService(db)
        rule_uuid = UUID(rule_id)
        platform_account_uuid = UUID(req.platform_account_id) if req.platform_account_id else None

        result = await scheduler.execute_rule(rule_uuid, platform_account_uuid)

        return AutomationRuleExecuteResponse(
            success=True,
            rule_id=result["rule_id"],
            action_type=result["action_type"],
            result=result["result"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid UUID format: {exc}")
    except AutomationSchedulerError as exc:
        return AutomationRuleExecuteResponse(
            success=False,
            rule_id=rule_id,
            action_type="unknown",
            result={},
            error=str(exc),
        )
    except Exception as exc:
        logger.error(f"Unexpected error executing automation rule: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")

