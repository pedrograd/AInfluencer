"""A/B testing database models for managing experiments and variants."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ABTestStatus(str, Enum):
    """Status of an A/B test."""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ABTest(Base):
    """A/B test model for managing experiments.
    
    Stores test configuration, variants, and metadata for A/B testing
    of content, captions, hashtags, posting times, and other strategies.
    
    Attributes:
        id: Unique identifier (UUID) for the test.
        character_id: Foreign key to the Character this test belongs to.
        name: Test name/description.
        description: Detailed test description.
        test_type: Type of test (content, caption, hashtags, posting_time, etc.).
        status: Test status (draft, running, paused, completed, cancelled).
        variant_a_name: Name for variant A (e.g., "Control").
        variant_b_name: Name for variant B (e.g., "Treatment").
        variant_a_config: JSON configuration for variant A.
        variant_b_config: JSON configuration for variant B.
        start_date: When the test started.
        end_date: When the test ended or is scheduled to end.
        target_sample_size: Target number of participants per variant.
        significance_level: Statistical significance level (default: 0.05).
        created_at: Timestamp when test was created.
        updated_at: Timestamp when test was last updated.
    """

    __tablename__ = "ab_tests"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    character_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Test Info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    test_type = Column(String(50), nullable=False)  # content, caption, hashtags, posting_time, etc.
    status = Column(String(20), default=ABTestStatus.DRAFT.value, nullable=False)

    # Variants
    variant_a_name = Column(String(100), nullable=False, default="Variant A")
    variant_b_name = Column(String(100), nullable=False, default="Variant B")
    variant_a_config = Column(JSONB, nullable=True)  # Configuration for variant A
    variant_b_config = Column(JSONB, nullable=True)  # Configuration for variant B

    # Test Schedule
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)

    # Test Parameters
    target_sample_size = Column(Integer, nullable=True)  # Target participants per variant
    significance_level = Column(Numeric(5, 4), default=Decimal("0.05"), nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    variants = relationship("ABTestVariant", back_populates="test", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'running', 'paused', 'completed', 'cancelled')",
            name="ab_test_status_check",
        ),
        CheckConstraint(
            "test_type IN ('content', 'caption', 'hashtags', 'posting_time', 'image_style', 'engagement_strategy')",
            name="ab_test_type_check",
        ),
        Index("idx_ab_tests_character", "character_id"),
        Index("idx_ab_tests_status", "status"),
        Index("idx_ab_tests_type", "test_type"),
    )

    def __repr__(self) -> str:
        return f"<ABTest(id={self.id}, name={self.name}, status={self.status})>"


class ABTestVariant(Base):
    """A/B test variant model for tracking individual test participants.
    
    Links posts or other entities to specific test variants and tracks
    their performance metrics.
    
    Attributes:
        id: Unique identifier (UUID) for the variant assignment.
        test_id: Foreign key to the ABTest.
        variant_name: Which variant this is (variant_a_name or variant_b_name).
        post_id: Foreign key to the Post assigned to this variant.
        content_id: Optional foreign key to Content if testing content variations.
        assigned_at: When this assignment was made.
        metrics: JSONB object with tracked metrics (likes, comments, views, etc.).
        created_at: Timestamp when variant was created.
    """

    __tablename__ = "ab_test_variants"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    test_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("ab_tests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variant_name = Column(String(100), nullable=False)  # variant_a_name or variant_b_name
    post_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    content_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("content.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metrics = Column(JSONB, nullable=True)  # Tracked metrics: likes, comments, views, engagement_rate, etc.

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    test = relationship("ABTest", back_populates="variants")

    # Constraints
    __table_args__ = (
        Index("idx_ab_test_variants_test", "test_id"),
        Index("idx_ab_test_variants_post", "post_id"),
        Index("idx_ab_test_variants_variant", "test_id", "variant_name"),
    )

    def __repr__(self) -> str:
        return f"<ABTestVariant(id={self.id}, test_id={self.test_id}, variant_name={self.variant_name})>"
