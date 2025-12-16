"""Payment service for handling Stripe payment processing."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import stripe

from app.core.config import settings
from app.core.logging import get_logger
from app.models.payment import Payment, PaymentStatus, Subscription, SubscriptionStatus

logger = get_logger(__name__)

# Initialize Stripe client
stripe.api_key = getattr(settings, "stripe_secret_key", None)


class PaymentServiceError(RuntimeError):
    """Error raised when payment operations fail."""
    pass


class PaymentService:
    """Service for handling payment processing with Stripe."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize payment service.

        Args:
            db: Database session for accessing payment and subscription data.
        """
        self.db = db
        if not stripe.api_key:
            logger.warning("Stripe API key not configured. Payment operations will fail.")

    async def create_subscription(
        self,
        user_id: UUID,
        plan_name: str,
        amount: float,
        interval: str = "month",
        currency: str = "usd",
    ) -> Subscription:
        """
        Create a new subscription for a user.

        Args:
            user_id: User ID to create subscription for.
            plan_name: Name of the subscription plan.
            amount: Subscription amount in cents.
            interval: Billing interval ("month" or "year").
            currency: Currency code (default: "usd").

        Returns:
            Created Subscription object.

        Raises:
            PaymentServiceError: If subscription creation fails.
        """
        if not stripe.api_key:
            raise PaymentServiceError("Stripe API key not configured")

        try:
            # Create Stripe subscription (if Stripe is configured)
            # For now, create subscription in database only
            # In production, integrate with Stripe API to create actual subscription

            subscription = Subscription(
                user_id=user_id,
                plan_name=plan_name,
                amount=amount,
                currency=currency,
                interval=interval,
                status=SubscriptionStatus.ACTIVE.value,
                current_period_start=datetime.utcnow(),
                # Set period end based on interval
                current_period_end=self._calculate_period_end(interval),
            )

            self.db.add(subscription)
            await self.db.commit()
            await self.db.refresh(subscription)

            logger.info(f"Created subscription {subscription.id} for user {user_id}")
            return subscription

        except Exception as exc:
            await self.db.rollback()
            error_msg = f"Failed to create subscription: {exc}"
            logger.error(error_msg)
            raise PaymentServiceError(error_msg) from exc

    def _calculate_period_end(self, interval: str) -> datetime:
        """
        Calculate period end date based on interval.

        Args:
            interval: Billing interval ("month" or "year").

        Returns:
            Period end datetime.
        """
        from dateutil.relativedelta import relativedelta

        now = datetime.utcnow()
        if interval == "year":
            return now + relativedelta(years=1)
        else:  # month (default)
            return now + relativedelta(months=1)

    async def create_payment_intent(
        self,
        user_id: UUID,
        amount: float,
        currency: str = "usd",
        description: str | None = None,
        subscription_id: UUID | None = None,
    ) -> dict[str, Any]:
        """
        Create a Stripe payment intent for a payment.

        Args:
            user_id: User ID making the payment.
            amount: Payment amount in cents.
            currency: Currency code (default: "usd").
            description: Payment description.
            subscription_id: Optional subscription ID if payment is for subscription.

        Returns:
            Payment intent dictionary with client_secret and payment_intent_id.

        Raises:
            PaymentServiceError: If payment intent creation fails.
        """
        if not stripe.api_key:
            raise PaymentServiceError("Stripe API key not configured")

        try:
            # Create Stripe payment intent
            intent_data = {
                "amount": int(amount),  # Stripe expects integer cents
                "currency": currency,
                "metadata": {
                    "user_id": str(user_id),
                },
            }

            if description:
                intent_data["description"] = description

            if subscription_id:
                intent_data["metadata"]["subscription_id"] = str(subscription_id)

            payment_intent = stripe.PaymentIntent.create(**intent_data)

            # Create payment record in database
            payment = Payment(
                user_id=user_id,
                subscription_id=subscription_id,
                stripe_payment_intent_id=payment_intent.id,
                amount=amount,
                currency=currency,
                status=PaymentStatus.PENDING.value,
                description=description,
            )

            self.db.add(payment)
            await self.db.commit()
            await self.db.refresh(payment)

            logger.info(f"Created payment intent {payment_intent.id} for user {user_id}")

            return {
                "payment_intent_id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "payment_id": str(payment.id),
            }

        except stripe.error.StripeError as exc:
            await self.db.rollback()
            error_msg = f"Stripe error creating payment intent: {exc}"
            logger.error(error_msg)
            raise PaymentServiceError(error_msg) from exc
        except Exception as exc:
            await self.db.rollback()
            error_msg = f"Failed to create payment intent: {exc}"
            logger.error(error_msg)
            raise PaymentServiceError(error_msg) from exc

    async def confirm_payment(self, payment_intent_id: str) -> Payment:
        """
        Confirm a payment after successful Stripe payment.

        Args:
            payment_intent_id: Stripe payment intent ID.

        Returns:
            Updated Payment object.

        Raises:
            PaymentServiceError: If payment confirmation fails.
        """
        if not stripe.api_key:
            raise PaymentServiceError("Stripe API key not configured")

        try:
            # Retrieve payment intent from Stripe
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            # Find payment in database
            result = await self.db.execute(
                select(Payment).where(Payment.stripe_payment_intent_id == payment_intent_id)
            )
            payment = result.scalar_one_or_none()

            if not payment:
                raise PaymentServiceError(f"Payment not found for intent {payment_intent_id}")

            # Update payment status based on Stripe status
            if payment_intent.status == "succeeded":
                payment.status = PaymentStatus.SUCCEEDED.value
                if payment_intent.charges.data:
                    payment.stripe_charge_id = payment_intent.charges.data[0].id
            elif payment_intent.status == "canceled":
                payment.status = PaymentStatus.CANCELLED.value
            else:
                payment.status = PaymentStatus.PENDING.value

            payment.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(payment)

            logger.info(f"Confirmed payment {payment.id} with status {payment.status}")
            return payment

        except stripe.error.StripeError as exc:
            error_msg = f"Stripe error confirming payment: {exc}"
            logger.error(error_msg)
            raise PaymentServiceError(error_msg) from exc
        except Exception as exc:
            await self.db.rollback()
            error_msg = f"Failed to confirm payment: {exc}"
            logger.error(error_msg)
            raise PaymentServiceError(error_msg) from exc

    async def get_user_subscription(self, user_id: UUID) -> Subscription | None:
        """
        Get active subscription for a user.

        Args:
            user_id: User ID to get subscription for.

        Returns:
            Active Subscription object or None if no active subscription.
        """
        result = await self.db.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .where(Subscription.status == SubscriptionStatus.ACTIVE.value)
            .order_by(Subscription.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def cancel_subscription(self, subscription_id: UUID) -> Subscription:
        """
        Cancel a subscription.

        Args:
            subscription_id: Subscription ID to cancel.

        Returns:
            Updated Subscription object.

        Raises:
            PaymentServiceError: If subscription cancellation fails.
        """
        result = await self.db.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise PaymentServiceError(f"Subscription {subscription_id} not found")

        try:
            # Cancel Stripe subscription if exists
            if subscription.stripe_subscription_id and stripe.api_key:
                try:
                    stripe.Subscription.modify(
                        subscription.stripe_subscription_id,
                        cancel_at_period_end=True,
                    )
                except stripe.error.StripeError as exc:
                    logger.warning(f"Failed to cancel Stripe subscription: {exc}")

            # Update subscription in database
            subscription.status = SubscriptionStatus.CANCELLED.value
            subscription.cancel_at_period_end = True
            subscription.cancelled_at = datetime.utcnow()
            subscription.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(subscription)

            logger.info(f"Cancelled subscription {subscription_id}")
            return subscription

        except Exception as exc:
            await self.db.rollback()
            error_msg = f"Failed to cancel subscription: {exc}"
            logger.error(error_msg)
            raise PaymentServiceError(error_msg) from exc

    async def get_user_payments(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Payment]:
        """
        Get payment history for a user.

        Args:
            user_id: User ID to get payments for.
            limit: Maximum number of payments to return.
            offset: Number of payments to skip.

        Returns:
            List of Payment objects.
        """
        result = await self.db.execute(
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

