"""Payment and subscription database models."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class SubscriptionStatus(str, Enum):
    """Subscription status enumeration."""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Subscription(Base):
    """Subscription model for user subscription management.
    
    Represents a user's subscription to the AInfluencer platform with billing
    information, status, and payment history.
    
    Attributes:
        id: Unique identifier (UUID) for the subscription.
        user_id: Foreign key to the user who owns this subscription.
        stripe_subscription_id: Stripe subscription ID (unique, indexed).
        status: Current subscription status (active, cancelled, etc.).
        plan_name: Name of the subscription plan (e.g., "basic", "pro", "enterprise").
        amount: Subscription amount in cents (e.g., 999 = $9.99).
        currency: Currency code (default: "usd").
        interval: Billing interval ("month", "year").
        current_period_start: Start of current billing period.
        current_period_end: End of current billing period.
        cancel_at_period_end: Whether subscription will cancel at period end.
        cancelled_at: Timestamp when subscription was cancelled (None if active).
        created_at: Timestamp when subscription was created.
        updated_at: Timestamp when subscription was last updated.
        user: Relationship to User model.
        payments: Relationship to Payment model.
    """

    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    stripe_subscription_id = Column(String(255), unique=True, nullable=True, index=True)
    status = Column(String(50), nullable=False, default=SubscriptionStatus.ACTIVE.value)
    plan_name = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)  # Amount in cents
    currency = Column(String(10), default="usd", nullable=False)
    interval = Column(String(20), nullable=False)  # "month" or "year"
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="subscriptions")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, user_id={self.user_id}, status={self.status}, plan={self.plan_name})>"


class Payment(Base):
    """Payment model for tracking payment transactions.
    
    Represents individual payment transactions for subscriptions or one-time payments.
    
    Attributes:
        id: Unique identifier (UUID) for the payment.
        user_id: Foreign key to the user who made the payment.
        subscription_id: Foreign key to the subscription (if payment is for subscription).
        stripe_payment_intent_id: Stripe payment intent ID (unique, indexed).
        stripe_charge_id: Stripe charge ID (if available).
        amount: Payment amount in cents (e.g., 999 = $9.99).
        currency: Currency code (default: "usd").
        status: Payment status (pending, succeeded, failed, etc.).
        description: Payment description or notes.
        metadata: Additional payment metadata (JSON string).
        created_at: Timestamp when payment was created.
        updated_at: Timestamp when payment was last updated.
        user: Relationship to User model.
        subscription: Relationship to Subscription model.
    """

    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=True, index=True)
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=True, index=True)
    stripe_charge_id = Column(String(255), nullable=True)
    amount = Column(Float, nullable=False)  # Amount in cents
    currency = Column(String(10), default="usd", nullable=False)
    status = Column(String(50), nullable=False, default=PaymentStatus.PENDING.value)
    description = Column(Text, nullable=True)
    metadata = Column(Text, nullable=True)  # JSON string for additional data
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="payments")
    subscription = relationship("Subscription", back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status})>"

