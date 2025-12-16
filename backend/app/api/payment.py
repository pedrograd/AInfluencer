"""Payment API endpoints for Stripe payment processing."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.payment import PaymentStatus, SubscriptionStatus
from app.services.payment_service import PaymentService, PaymentServiceError

logger = get_logger(__name__)

router = APIRouter()


class CreateSubscriptionRequest(BaseModel):
    """Request model for creating a subscription."""
    plan_name: str
    amount: float  # Amount in cents
    interval: str = "month"  # "month" or "year"
    currency: str = "usd"


class CreateSubscriptionResponse(BaseModel):
    """Response model for subscription creation."""
    subscription_id: str
    plan_name: str
    amount: float
    status: str
    current_period_end: str | None = None


class CreatePaymentIntentRequest(BaseModel):
    """Request model for creating a payment intent."""
    amount: float  # Amount in cents
    currency: str = "usd"
    description: str | None = None
    subscription_id: str | None = None


class CreatePaymentIntentResponse(BaseModel):
    """Response model for payment intent creation."""
    payment_intent_id: str
    client_secret: str
    payment_id: str


class ConfirmPaymentRequest(BaseModel):
    """Request model for confirming a payment."""
    payment_intent_id: str


class PaymentResponse(BaseModel):
    """Response model for payment information."""
    payment_id: str
    amount: float
    currency: str
    status: str
    description: str | None = None
    created_at: str


class SubscriptionResponse(BaseModel):
    """Response model for subscription information."""
    subscription_id: str
    plan_name: str
    amount: float
    currency: str
    interval: str
    status: str
    current_period_start: str | None = None
    current_period_end: str | None = None
    cancel_at_period_end: bool


@router.post("/create-subscription", response_model=CreateSubscriptionResponse)
async def create_subscription(
    request: CreateSubscriptionRequest,
    user_id: UUID,  # TODO: Get from authenticated user token
    db: AsyncSession = Depends(get_db),
) -> CreateSubscriptionResponse:
    """Create a new subscription for the current user.
    
    Args:
        request: Subscription creation request.
        user_id: User ID (TODO: get from auth token).
        db: Database session.
        
    Returns:
        Created subscription information.
        
    Raises:
        HTTPException: If subscription creation fails.
    """
    try:
        service = PaymentService(db)
        subscription = await service.create_subscription(
            user_id=user_id,
            plan_name=request.plan_name,
            amount=request.amount,
            interval=request.interval,
            currency=request.currency,
        )

        return CreateSubscriptionResponse(
            subscription_id=str(subscription.id),
            plan_name=subscription.plan_name,
            amount=subscription.amount,
            status=subscription.status,
            current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
        )
    except PaymentServiceError as exc:
        logger.error(f"Payment service error: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Unexpected error creating subscription: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to create subscription: {exc}") from exc


@router.post("/create-payment-intent", response_model=CreatePaymentIntentResponse)
async def create_payment_intent(
    request: CreatePaymentIntentRequest,
    user_id: UUID,  # TODO: Get from authenticated user token
    db: AsyncSession = Depends(get_db),
) -> CreatePaymentIntentResponse:
    """Create a Stripe payment intent for a payment.
    
    Args:
        request: Payment intent creation request.
        user_id: User ID (TODO: get from auth token).
        db: Database session.
        
    Returns:
        Payment intent information with client_secret for frontend.
        
    Raises:
        HTTPException: If payment intent creation fails.
    """
    try:
        service = PaymentService(db)
        subscription_id = UUID(request.subscription_id) if request.subscription_id else None
        
        result = await service.create_payment_intent(
            user_id=user_id,
            amount=request.amount,
            currency=request.currency,
            description=request.description,
            subscription_id=subscription_id,
        )

        return CreatePaymentIntentResponse(**result)
    except PaymentServiceError as exc:
        logger.error(f"Payment service error: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        logger.error(f"Invalid UUID: {exc}")
        raise HTTPException(status_code=400, detail=f"Invalid subscription_id: {exc}") from exc
    except Exception as exc:
        logger.error(f"Unexpected error creating payment intent: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to create payment intent: {exc}") from exc


@router.post("/confirm-payment", response_model=PaymentResponse)
async def confirm_payment(
    request: ConfirmPaymentRequest,
    db: AsyncSession = Depends(get_db),
) -> PaymentResponse:
    """Confirm a payment after successful Stripe payment.
    
    Args:
        request: Payment confirmation request with payment_intent_id.
        db: Database session.
        
    Returns:
        Confirmed payment information.
        
    Raises:
        HTTPException: If payment confirmation fails.
    """
    try:
        service = PaymentService(db)
        payment = await service.confirm_payment(request.payment_intent_id)

        return PaymentResponse(
            payment_id=str(payment.id),
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            description=payment.description,
            created_at=payment.created_at.isoformat(),
        )
    except PaymentServiceError as exc:
        logger.error(f"Payment service error: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Unexpected error confirming payment: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to confirm payment: {exc}") from exc


@router.get("/subscription", response_model=SubscriptionResponse | None)
async def get_subscription(
    user_id: UUID,  # TODO: Get from authenticated user token
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse | None:
    """Get active subscription for the current user.
    
    Args:
        user_id: User ID (TODO: get from auth token).
        db: Database session.
        
    Returns:
        Active subscription information or None if no active subscription.
    """
    try:
        service = PaymentService(db)
        subscription = await service.get_user_subscription(user_id)

        if not subscription:
            return None

        return SubscriptionResponse(
            subscription_id=str(subscription.id),
            plan_name=subscription.plan_name,
            amount=subscription.amount,
            currency=subscription.currency,
            interval=subscription.interval,
            status=subscription.status,
            current_period_start=subscription.current_period_start.isoformat() if subscription.current_period_start else None,
            current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            cancel_at_period_end=subscription.cancel_at_period_end,
        )
    except Exception as exc:
        logger.error(f"Unexpected error getting subscription: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to get subscription: {exc}") from exc


@router.post("/cancel-subscription", response_model=SubscriptionResponse)
async def cancel_subscription(
    subscription_id: str,
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    """Cancel a subscription.
    
    Args:
        subscription_id: Subscription ID to cancel.
        db: Database session.
        
    Returns:
        Cancelled subscription information.
        
    Raises:
        HTTPException: If subscription cancellation fails.
    """
    try:
        service = PaymentService(db)
        subscription = await service.cancel_subscription(UUID(subscription_id))

        return SubscriptionResponse(
            subscription_id=str(subscription.id),
            plan_name=subscription.plan_name,
            amount=subscription.amount,
            currency=subscription.currency,
            interval=subscription.interval,
            status=subscription.status,
            current_period_start=subscription.current_period_start.isoformat() if subscription.current_period_start else None,
            current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            cancel_at_period_end=subscription.cancel_at_period_end,
        )
    except PaymentServiceError as exc:
        logger.error(f"Payment service error: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        logger.error(f"Invalid UUID: {exc}")
        raise HTTPException(status_code=400, detail=f"Invalid subscription_id: {exc}") from exc
    except Exception as exc:
        logger.error(f"Unexpected error cancelling subscription: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel subscription: {exc}") from exc


@router.get("/payments", response_model=list[PaymentResponse])
async def get_payments(
    user_id: UUID,  # TODO: Get from authenticated user token
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> list[PaymentResponse]:
    """Get payment history for the current user.
    
    Args:
        user_id: User ID (TODO: get from auth token).
        limit: Maximum number of payments to return.
        offset: Number of payments to skip.
        db: Database session.
        
    Returns:
        List of payment information.
    """
    try:
        service = PaymentService(db)
        payments = await service.get_user_payments(user_id, limit=limit, offset=offset)

        return [
            PaymentResponse(
                payment_id=str(payment.id),
                amount=payment.amount,
                currency=payment.currency,
                status=payment.status,
                description=payment.description,
                created_at=payment.created_at.isoformat(),
            )
            for payment in payments
        ]
    except Exception as exc:
        logger.error(f"Unexpected error getting payments: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to get payments: {exc}") from exc

