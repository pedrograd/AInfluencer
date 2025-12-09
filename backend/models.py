"""
Database models
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid
from datetime import datetime

def generate_id():
    """Generate a unique ID"""
    return str(uuid.uuid4())

class Character(Base):
    __tablename__ = "characters"
    
    id = Column(String, primary_key=True, default=generate_id)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    # Character components as per Character Management System
    # Persona: personality, voice, behavior, interests, values
    persona = Column(JSON, default=dict)  # {personality: {traits: [], voice: "", tone: ""}, interests: [], values: []}
    
    # Appearance: physical characteristics, face, body, hair
    appearance = Column(JSON, default=dict)  # {face: {}, hair: {}, body: {}}
    
    # Style: visual style, aesthetic, brand
    style = Column(JSON, default=dict)  # {photography: "", color_palette: {}, lighting: "", composition: "", mood: ""}
    
    # Content preferences: content types, topics, themes
    content_preferences = Column(JSON, default=dict)  # {image_types: [], video_types: [], topics: [], themes: []}
    
    # Consistency rules: face, style, persona consistency
    consistency_rules = Column(JSON, default=dict)  # {face: {}, style: {}, persona: {}}
    
    # Legacy fields for backward compatibility
    settings = Column(JSON, default=dict)
    meta_data = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved in SQLAlchemy)
    
    # Relationships
    face_references = relationship("FaceReference", back_populates="character", cascade="all, delete-orphan")
    media_items = relationship("MediaItem", back_populates="character")
    generation_jobs = relationship("GenerationJob", back_populates="character")

class FaceReference(Base):
    __tablename__ = "face_references"
    
    id = Column(String, primary_key=True, default=generate_id)
    character_id = Column(String, ForeignKey("characters.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String)
    width = Column(Integer)
    height = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    meta_data = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved in SQLAlchemy)
    
    # Relationships
    character = relationship("Character", back_populates="face_references")

class MediaItem(Base):
    __tablename__ = "media_items"
    
    id = Column(String, primary_key=True, default=generate_id)
    type = Column(String, nullable=False)  # 'image' or 'video'
    source = Column(String, nullable=False)  # 'ai_generated' or 'personal'
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String)
    width = Column(Integer)
    height = Column(Integer)
    duration = Column(Integer)  # For videos (seconds)
    thumbnail_path = Column(String)
    character_id = Column(String, ForeignKey("characters.id", ondelete="SET NULL"), nullable=True)
    generation_job_id = Column(String, ForeignKey("generation_jobs.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    meta_data = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved in SQLAlchemy)
    tags = Column(JSON, default=list)  # Array of tags (stored as JSON in SQLite)
    
    # Relationships
    character = relationship("Character", back_populates="media_items")
    generation_job = relationship("GenerationJob", back_populates="result_media")
    quality_scores = relationship("QualityScore", back_populates="media_item", cascade="all, delete-orphan")

class GenerationJob(Base):
    __tablename__ = "generation_jobs"
    
    id = Column(String, primary_key=True, default=generate_id)
    type = Column(String, nullable=False)  # 'image' or 'video'
    status = Column(String, nullable=False, default="pending")  # 'pending', 'processing', 'completed', 'failed'
    character_id = Column(String, ForeignKey("characters.id", ondelete="SET NULL"), nullable=True)
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text)
    settings = Column(JSON, nullable=False, default=dict)
    workflow_config = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    error_message = Column(Text)
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    comfyui_prompt_id = Column(String)
    meta_data = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved in SQLAlchemy)
    
    # Relationships
    character = relationship("Character", back_populates="generation_jobs")
    result_media = relationship("MediaItem", back_populates="generation_job", uselist=False)
    history = relationship("GenerationHistory", back_populates="job", cascade="all, delete-orphan")

class GenerationHistory(Base):
    __tablename__ = "generation_history"
    
    id = Column(String, primary_key=True, default=generate_id)
    job_id = Column(String, ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False)
    user_action = Column(String)  # 'generate', 'regenerate', 'variation'
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text)
    settings = Column(JSON)
    result_media_id = Column(String, ForeignKey("media_items.id", ondelete="SET NULL"), nullable=True)
    quality_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("GenerationJob", back_populates="history")

class BatchJob(Base):
    __tablename__ = "batch_jobs"
    
    id = Column(String, primary_key=True, default=generate_id)
    type = Column(String, nullable=False)  # 'image' or 'video'
    status = Column(String, nullable=False, default="pending")
    total_count = Column(Integer, nullable=False)
    completed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    character_id = Column(String, ForeignKey("characters.id", ondelete="SET NULL"), nullable=True)
    prompt_template = Column(Text)
    settings_template = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    meta_data = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved in SQLAlchemy)
    
    # Relationships
    character = relationship("Character")
    items = relationship("BatchJobItem", back_populates="batch_job", cascade="all, delete-orphan")

class BatchJobItem(Base):
    __tablename__ = "batch_job_items"
    
    id = Column(String, primary_key=True, default=generate_id)
    batch_job_id = Column(String, ForeignKey("batch_jobs.id", ondelete="CASCADE"), nullable=False)
    generation_job_id = Column(String, ForeignKey("generation_jobs.id", ondelete="SET NULL"), nullable=True)
    index = Column(Integer, nullable=False)
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text)
    settings = Column(JSON)
    status = Column(String, nullable=False, default="pending")
    result_media_id = Column(String, ForeignKey("media_items.id", ondelete="SET NULL"), nullable=True)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    batch_job = relationship("BatchJob", back_populates="items")
    generation_job = relationship("GenerationJob")

class QualityScore(Base):
    __tablename__ = "quality_scores"
    
    id = Column(String, primary_key=True, default=generate_id)
    media_id = Column(String, ForeignKey("media_items.id", ondelete="CASCADE"), nullable=False)
    overall_score = Column(Float, nullable=False)  # 0.0 to 1.0 (stored as 0-1, displayed as 0-10)
    realism_score = Column(Float)
    artifact_score = Column(Float)  # Lower is better
    face_quality_score = Column(Float)
    technical_score = Column(Float)  # Technical quality score
    face_consistency_score = Column(Float)
    passed = Column(Boolean, default=False)  # Whether it passed quality thresholds
    auto_approved = Column(Boolean, default=False)  # Whether it was auto-approved
    created_at = Column(DateTime, default=datetime.utcnow)
    meta_data = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved in SQLAlchemy)
    
    # Relationships
    media_item = relationship("MediaItem", back_populates="quality_scores")

class Setting(Base):
    __tablename__ = "settings"
    
    id = Column(String, primary_key=True, default=generate_id)
    category = Column(String, nullable=False)
    key = Column(String, nullable=False)
    value = Column(JSON, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )

class DetectionTest(Base):
    __tablename__ = "detection_tests"
    
    id = Column(String, primary_key=True, default=generate_id)
    media_id = Column(String, ForeignKey("media_items.id", ondelete="CASCADE"), nullable=False)
    test_type = Column(String, nullable=False)  # 'pre_publication', 'manual', 'automated'
    threshold = Column(Float, default=0.3)
    average_score = Column(Float, nullable=False)
    passed = Column(Boolean, nullable=False)
    results = Column(JSON, default=dict)  # Detailed results from each tool
    recommendations = Column(JSON, default=list)
    metadata_check = Column(JSON, default=dict)
    quality_check = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    media_item = relationship("MediaItem", backref="detection_tests")

class DetectionToolConfig(Base):
    __tablename__ = "detection_tool_configs"
    
    id = Column(String, primary_key=True, default=generate_id)
    tool_name = Column(String, nullable=False, unique=True)
    api_key = Column(String)  # Encrypted in production
    enabled = Column(Boolean, default=True)
    threshold = Column(Float, default=0.3)
    config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class QualityReview(Base):
    """Manual quality review records"""
    __tablename__ = "quality_reviews"
    
    id = Column(String, primary_key=True, default=generate_id)
    media_id = Column(String, ForeignKey("media_items.id", ondelete="CASCADE"), nullable=False)
    reviewer_id = Column(String)  # User/reviewer identifier
    review_type = Column(String, nullable=False)  # 'manual', 'automated', 'borderline'
    quality_score = Column(Float)  # Overall quality score from reviewer
    face_score = Column(Float)
    technical_score = Column(Float)
    realism_score = Column(Float)
    decision = Column(String, nullable=False)  # 'approve', 'reject', 'improve'
    notes = Column(Text)
    checklist_scores = Column(JSON, default=dict)  # Individual checklist item scores
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    media_item = relationship("MediaItem", backref="quality_reviews")


class RejectionLog(Base):
    """Log of rejected content with reasons"""
    __tablename__ = "rejection_logs"
    
    id = Column(String, primary_key=True, default=generate_id)
    media_id = Column(String, ForeignKey("media_items.id", ondelete="CASCADE"), nullable=False)
    rejection_reason = Column(String, nullable=False)  # 'quality', 'detection', 'technical'
    rejection_category = Column(String)  # More specific category
    quality_score = Column(Float)  # Score at time of rejection
    detection_score = Column(Float)  # Detection score if applicable
    details = Column(JSON, default=dict)  # Additional details
    action_taken = Column(String)  # 'retry', 'improve', 'discard'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    media_item = relationship("MediaItem", backref="rejection_logs")

class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"
    
    id = Column(String, primary_key=True, default=generate_id)
    media_id = Column(String, ForeignKey("media_items.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String, nullable=False)  # 'instagram', 'twitter', 'onlyfans', etc.
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String, nullable=False, default="scheduled")  # 'scheduled', 'posted', 'failed', 'cancelled'
    caption = Column(Text)
    meta_data = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved in SQLAlchemy)
    created_at = Column(DateTime, default=datetime.utcnow)
    posted_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    error_message = Column(Text)
    
    # Relationships
    media_item = relationship("MediaItem", backref="scheduled_posts")

class ContentApproval(Base):
    __tablename__ = "content_approvals"
    
    id = Column(String, primary_key=True, default=generate_id)
    media_id = Column(String, ForeignKey("media_items.id", ondelete="CASCADE"), nullable=False)
    approved = Column(Boolean, nullable=False)
    method = Column(String, nullable=False)  # 'auto', 'manual'
    quality_score = Column(Float)
    threshold = Column(Float)
    reviewer_id = Column(String, nullable=True)  # User ID if manual review
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    media_item = relationship("MediaItem", backref="approvals")

class PlatformAccount(Base):
    __tablename__ = "platform_accounts"
    
    id = Column(String, primary_key=True, default=generate_id)
    platform = Column(String, nullable=False)  # 'instagram', 'twitter', 'facebook', 'telegram', 'onlyfans', 'youtube'
    username = Column(String, nullable=False)
    account_id = Column(String)  # Platform-specific account ID
    display_name = Column(String)
    auth_type = Column(String, nullable=False)  # 'oauth', 'session', 'api_key', 'browser'
    credentials = Column(JSON, nullable=False)  # Encrypted credentials
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    rate_limit_info = Column(JSON, default=dict)  # Track rate limits per platform
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    meta_data = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved in SQLAlchemy)
    
    # Relationships
    posts = relationship("PlatformPost", back_populates="account", cascade="all, delete-orphan")

class PlatformPost(Base):
    __tablename__ = "platform_posts"
    
    id = Column(String, primary_key=True, default=generate_id)
    account_id = Column(String, ForeignKey("platform_accounts.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String, nullable=False)
    media_id = Column(String, ForeignKey("media_items.id", ondelete="SET NULL"), nullable=True)
    post_type = Column(String, nullable=False)  # 'image', 'video', 'reel', 'story', 'tweet', etc.
    caption = Column(Text)
    platform_post_id = Column(String)  # ID returned by platform
    status = Column(String, nullable=False, default="pending")  # 'pending', 'scheduled', 'published', 'failed'
    scheduled_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    meta_data = Column(JSON, default=dict)  # Platform-specific metadata (likes, views, etc.) - Renamed from 'metadata' (reserved in SQLAlchemy)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    account = relationship("PlatformAccount", back_populates="posts")
    media_item = relationship("MediaItem", backref="platform_posts")
