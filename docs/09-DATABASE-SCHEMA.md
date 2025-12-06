# Database Schema & Data Models

## 📋 Document Metadata

### Purpose
Complete database schema design with all tables, relationships, indexes, and data models. This is the data layer foundation that all features depend on.

### Reading Order
**Read After:** [02-TECHNICAL-ARCHITECTURE.md](./02-TECHNICAL-ARCHITECTURE.md), [PRD.md](./PRD.md)  
**Read Before:** [10-API-DESIGN.md](./10-API-DESIGN.md) (API uses database schema), implementing any backend features

### Related Documents
**Prerequisites:**
- [02-TECHNICAL-ARCHITECTURE.md](./02-TECHNICAL-ARCHITECTURE.md) - Database choice and architecture
- [PRD.md](./PRD.md) - Functional requirements inform schema design

**Used By:**
- [10-API-DESIGN.md](./10-API-DESIGN.md) - API endpoints use these models
- Backend implementation - All ORM models based on this schema
- [15-DEPLOYMENT-DEVOPS.md](./15-DEPLOYMENT-DEVOPS.md) - Database setup and migrations

**Related:**
- [03-FEATURE-ROADMAP.md](./03-FEATURE-ROADMAP.md) - Features require database changes
- [14-TESTING-STRATEGY.md](./14-TESTING-STRATEGY.md) - Test fixtures use this schema

---

## Database Choice

**PostgreSQL 15+**
- **Why**: Robust, open-source, excellent JSON support, ACID compliance
- **Extensions**: `pg_trgm` (text search), `uuid-ossp` (UUID generation)
- **Backup**: pg_dump, automated backups

---

## Schema Overview

### Core Tables
1. `characters` - AI influencer character profiles
2. `character_personalities` - Personality traits and behavior patterns
3. `character_appearances` - Physical attributes and face references
4. `content` - Generated content (images, videos, text)
5. `content_generations` - Generation job records
6. `platform_accounts` - Social media account connections
7. `posts` - Published posts across platforms
8. `scheduled_posts` - Queued posts for future publishing
9. `automation_rules` - Automation configuration
10. `engagement_actions` - Likes, comments, shares, etc.
11. `analytics` - Performance metrics and statistics
12. `system_logs` - Application and error logs
13. `users` - Platform users (if multi-user support needed)

---

## Detailed Schema

### 1. Characters Table

```sql
CREATE TABLE characters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    bio TEXT,
    age INTEGER,
    location VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'UTC',
    interests TEXT[], -- Array of interests
    profile_image_url TEXT,
    profile_image_path TEXT, -- Local storage path
    
    -- Status
    status VARCHAR(20) DEFAULT 'active', -- active, paused, error, deleted
    is_active BOOLEAN DEFAULT true,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT status_check CHECK (status IN ('active', 'paused', 'error', 'deleted'))
);

CREATE INDEX idx_characters_status ON characters(status);
CREATE INDEX idx_characters_active ON characters(is_active) WHERE is_active = true;
CREATE INDEX idx_characters_created ON characters(created_at);
```

### 2. Character Personalities Table

```sql
CREATE TABLE character_personalities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    
    -- Personality Traits (0.0 to 1.0 scale)
    extroversion DECIMAL(3,2) DEFAULT 0.5, -- 0.0 = introverted, 1.0 = extroverted
    creativity DECIMAL(3,2) DEFAULT 0.5,
    humor DECIMAL(3,2) DEFAULT 0.5,
    professionalism DECIMAL(3,2) DEFAULT 0.5,
    authenticity DECIMAL(3,2) DEFAULT 0.5,
    
    -- Communication Style
    communication_style VARCHAR(50), -- casual, professional, friendly, sassy, etc.
    preferred_topics TEXT[], -- Array of topics
    content_tone VARCHAR(50), -- positive, neutral, edgy, etc.
    
    -- LLM Settings
    llm_personality_prompt TEXT, -- Custom prompt for LLM
    temperature DECIMAL(3,2) DEFAULT 0.7, -- LLM temperature
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_character_personality UNIQUE (character_id)
);

CREATE INDEX idx_personalities_character ON character_personalities(character_id);
```

### 3. Character Appearances Table

```sql
CREATE TABLE character_appearances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    
    -- Face Consistency
    face_reference_image_url TEXT,
    face_reference_image_path TEXT,
    face_consistency_method VARCHAR(50) DEFAULT 'ip-adapter', -- ip-adapter, instantid, faceid, lora
    lora_model_path TEXT, -- If using LoRA
    
    -- Physical Attributes
    hair_color VARCHAR(50),
    hair_style VARCHAR(50),
    eye_color VARCHAR(50),
    skin_tone VARCHAR(50),
    body_type VARCHAR(50),
    height VARCHAR(20),
    age_range VARCHAR(20), -- e.g., "25-30"
    
    -- Style Preferences
    clothing_style VARCHAR(100), -- casual, formal, sporty, etc.
    preferred_colors TEXT[], -- Array of colors
    style_keywords TEXT[], -- Array of style descriptors
    
    -- Generation Settings
    base_model VARCHAR(100) DEFAULT 'realistic-vision-v6', -- SD model name
    negative_prompt TEXT, -- Default negative prompt
    default_prompt_prefix TEXT, -- Prefix added to all prompts
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_character_appearance UNIQUE (character_id)
);

CREATE INDEX idx_appearances_character ON character_appearances(character_id);
```

### 4. Content Table

```sql
CREATE TABLE content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    
    -- Content Type
    content_type VARCHAR(20) NOT NULL, -- image, video, text, audio
    content_category VARCHAR(50), -- post, story, reel, short, message, etc.
    is_nsfw BOOLEAN DEFAULT false, -- +18 content flag
    
    -- Storage
    file_url TEXT, -- URL if stored remotely
    file_path TEXT NOT NULL, -- Local storage path
    thumbnail_url TEXT,
    thumbnail_path TEXT,
    
    -- Metadata
    file_size BIGINT, -- Bytes
    width INTEGER, -- For images/videos
    height INTEGER, -- For images/videos
    duration INTEGER, -- Seconds, for videos/audio
    mime_type VARCHAR(100),
    
    -- Generation Info
    prompt TEXT, -- Generation prompt used
    negative_prompt TEXT,
    generation_settings JSONB, -- Model, steps, CFG, etc.
    generation_time_seconds INTEGER,
    
    -- Quality & Status
    quality_score DECIMAL(3,2), -- 0.0 to 1.0, if automated QA
    is_approved BOOLEAN DEFAULT false,
    approval_status VARCHAR(20) DEFAULT 'pending', -- pending, approved, rejected
    rejection_reason TEXT,
    
    -- Usage
    times_used INTEGER DEFAULT 0, -- How many times posted
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT content_type_check CHECK (content_type IN ('image', 'video', 'text', 'audio')),
    CONSTRAINT approval_status_check CHECK (approval_status IN ('pending', 'approved', 'rejected'))
);

CREATE INDEX idx_content_character ON content(character_id);
CREATE INDEX idx_content_type ON content(content_type);
CREATE INDEX idx_content_category ON content(content_category);
CREATE INDEX idx_content_approved ON content(is_approved) WHERE is_approved = true;
CREATE INDEX idx_content_nsfw ON content(is_nsfw) WHERE is_nsfw = true;
CREATE INDEX idx_content_created ON content(created_at);
```

### 5. Content Generations Table

```sql
CREATE TABLE content_generations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    
    -- Job Info
    job_type VARCHAR(50) NOT NULL, -- image, video, text, batch
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    priority INTEGER DEFAULT 5, -- 1 (highest) to 10 (lowest)
    
    -- Generation Parameters
    prompt TEXT NOT NULL,
    negative_prompt TEXT,
    generation_settings JSONB NOT NULL,
    batch_size INTEGER DEFAULT 1, -- For batch generations
    
    -- Results
    generated_content_ids UUID[], -- Array of content.id
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    
    -- Error Handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT status_check CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled'))
);

CREATE INDEX idx_generations_character ON content_generations(character_id);
CREATE INDEX idx_generations_status ON content_generations(status);
CREATE INDEX idx_generations_priority ON content_generations(priority, created_at);
```

### 6. Platform Accounts Table

```sql
CREATE TABLE platform_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    
    -- Platform Info
    platform VARCHAR(50) NOT NULL, -- instagram, twitter, facebook, telegram, onlyfans, youtube
    account_username VARCHAR(255),
    account_id VARCHAR(255), -- Platform's user ID
    account_url TEXT,
    
    -- Authentication
    auth_type VARCHAR(50), -- api_key, oauth, browser_session, cookie
    auth_data JSONB, -- Encrypted credentials (API keys, tokens, etc.)
    is_connected BOOLEAN DEFAULT false,
    connection_status VARCHAR(20) DEFAULT 'disconnected', -- connected, disconnected, error, rate_limited
    
    -- Account Stats (cached)
    follower_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    post_count INTEGER DEFAULT 0,
    last_synced_at TIMESTAMP WITH TIME ZONE,
    
    -- Settings
    auto_posting_enabled BOOLEAN DEFAULT true,
    auto_engagement_enabled BOOLEAN DEFAULT true,
    posting_frequency VARCHAR(50), -- daily, weekly, custom
    engagement_frequency VARCHAR(50),
    
    -- Rate Limiting
    rate_limit_remaining INTEGER,
    rate_limit_reset_at TIMESTAMP WITH TIME ZONE,
    last_rate_limit_hit_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT platform_check CHECK (platform IN ('instagram', 'twitter', 'facebook', 'telegram', 'onlyfans', 'youtube')),
    CONSTRAINT connection_status_check CHECK (connection_status IN ('connected', 'disconnected', 'error', 'rate_limited', 'suspended'))
);

CREATE INDEX idx_platform_accounts_character ON platform_accounts(character_id);
CREATE INDEX idx_platform_accounts_platform ON platform_accounts(platform);
CREATE INDEX idx_platform_accounts_connected ON platform_accounts(is_connected) WHERE is_connected = true;
CREATE UNIQUE INDEX idx_platform_accounts_unique ON platform_accounts(character_id, platform);
```

### 7. Posts Table

```sql
CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    platform_account_id UUID NOT NULL REFERENCES platform_accounts(id) ON DELETE CASCADE,
    
    -- Post Info
    platform VARCHAR(50) NOT NULL,
    post_type VARCHAR(50), -- post, story, reel, short, tweet, message, etc.
    platform_post_id VARCHAR(255), -- ID returned by platform
    platform_post_url TEXT,
    
    -- Content
    content_id UUID REFERENCES content(id), -- Primary content (image/video)
    additional_content_ids UUID[], -- Array of additional content IDs
    caption TEXT,
    hashtags TEXT[],
    mentions TEXT[],
    
    -- Engagement (cached from platform)
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    views_count INTEGER DEFAULT 0,
    last_engagement_sync_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft', -- draft, scheduled, published, failed, deleted
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Error Handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT platform_check CHECK (platform IN ('instagram', 'twitter', 'facebook', 'telegram', 'onlyfans', 'youtube')),
    CONSTRAINT status_check CHECK (status IN ('draft', 'scheduled', 'published', 'failed', 'deleted'))
);

CREATE INDEX idx_posts_character ON posts(character_id);
CREATE INDEX idx_posts_platform_account ON posts(platform_account_id);
CREATE INDEX idx_posts_platform ON posts(platform);
CREATE INDEX idx_posts_status ON posts(status);
CREATE INDEX idx_posts_published ON posts(published_at);
CREATE INDEX idx_posts_platform_post_id ON posts(platform, platform_post_id);
```

### 8. Scheduled Posts Table

```sql
CREATE TABLE scheduled_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    platform_account_id UUID NOT NULL REFERENCES platform_accounts(id) ON DELETE CASCADE,
    
    -- Scheduling
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Post Content
    content_id UUID REFERENCES content(id),
    additional_content_ids UUID[],
    caption TEXT,
    hashtags TEXT[],
    post_type VARCHAR(50),
    
    -- Status
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, processing, published, failed, cancelled
    
    -- Automation Rule (if from rule)
    automation_rule_id UUID, -- References automation_rules(id)
    
    -- Error Handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT status_check CHECK (status IN ('scheduled', 'processing', 'published', 'failed', 'cancelled'))
);

CREATE INDEX idx_scheduled_posts_character ON scheduled_posts(character_id);
CREATE INDEX idx_scheduled_posts_scheduled_at ON scheduled_posts(scheduled_at) WHERE status = 'scheduled';
CREATE INDEX idx_scheduled_posts_status ON scheduled_posts(status);
```

### 9. Automation Rules Table

```sql
CREATE TABLE automation_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    
    -- Rule Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_enabled BOOLEAN DEFAULT true,
    
    -- Trigger
    trigger_type VARCHAR(50) NOT NULL, -- schedule, event, manual
    trigger_config JSONB NOT NULL, -- Schedule cron, event conditions, etc.
    
    -- Actions
    platforms TEXT[] NOT NULL, -- Array of platforms
    content_type VARCHAR(20), -- image, video, text, mixed
    content_category VARCHAR(50), -- post, story, reel, etc.
    
    -- Content Generation
    prompt_template TEXT,
    generation_settings JSONB,
    min_content_quality DECIMAL(3,2) DEFAULT 0.7, -- Minimum quality score
    
    -- Posting Settings
    caption_template TEXT,
    hashtag_strategy VARCHAR(50), -- auto, template, none
    mention_strategy VARCHAR(50),
    
    -- Engagement Settings (if applicable)
    auto_like BOOLEAN DEFAULT false,
    auto_comment BOOLEAN DEFAULT false,
    auto_follow BOOLEAN DEFAULT false,
    engagement_frequency VARCHAR(50),
    
    -- Limits
    max_posts_per_day INTEGER,
    max_posts_per_week INTEGER,
    cooldown_minutes INTEGER DEFAULT 60, -- Minimum time between posts
    
    -- Statistics
    times_executed INTEGER DEFAULT 0,
    last_executed_at TIMESTAMP WITH TIME ZONE,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT trigger_type_check CHECK (trigger_type IN ('schedule', 'event', 'manual')),
    CONSTRAINT content_type_check CHECK (content_type IN ('image', 'video', 'text', 'mixed', NULL))
);

CREATE INDEX idx_automation_rules_character ON automation_rules(character_id);
CREATE INDEX idx_automation_rules_enabled ON automation_rules(is_enabled) WHERE is_enabled = true;
```

### 10. Engagement Actions Table

```sql
CREATE TABLE engagement_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    platform_account_id UUID NOT NULL REFERENCES platform_accounts(id) ON DELETE CASCADE,
    
    -- Action Info
    platform VARCHAR(50) NOT NULL,
    action_type VARCHAR(50) NOT NULL, -- like, comment, share, follow, unfollow, message
    target_type VARCHAR(50), -- post, user, story, etc.
    target_id VARCHAR(255), -- Platform ID of target
    target_url TEXT,
    
    -- Action Content
    comment_text TEXT, -- If action_type = 'comment'
    message_text TEXT, -- If action_type = 'message'
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- pending, completed, failed
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Error Handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT platform_check CHECK (platform IN ('instagram', 'twitter', 'facebook', 'telegram', 'onlyfans', 'youtube')),
    CONSTRAINT action_type_check CHECK (action_type IN ('like', 'comment', 'share', 'follow', 'unfollow', 'message', 'reply')),
    CONSTRAINT status_check CHECK (status IN ('pending', 'completed', 'failed', 'cancelled'))
);

CREATE INDEX idx_engagement_character ON engagement_actions(character_id);
CREATE INDEX idx_engagement_platform_account ON engagement_actions(platform_account_id);
CREATE INDEX idx_engagement_status ON engagement_actions(status);
CREATE INDEX idx_engagement_created ON engagement_actions(created_at);
```

### 11. Analytics Table

```sql
CREATE TABLE analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    platform_account_id UUID REFERENCES platform_accounts(id) ON DELETE CASCADE,
    
    -- Metrics
    metric_date DATE NOT NULL,
    platform VARCHAR(50),
    metric_type VARCHAR(50) NOT NULL, -- follower_count, engagement_rate, post_count, etc.
    metric_value DECIMAL(12,2) NOT NULL,
    
    -- Additional Data
    metadata JSONB, -- Additional context
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT platform_check CHECK (platform IN ('instagram', 'twitter', 'facebook', 'telegram', 'onlyfans', 'youtube', NULL)),
    CONSTRAINT unique_metric UNIQUE (character_id, platform_account_id, metric_date, metric_type)
);

CREATE INDEX idx_analytics_character ON analytics(character_id);
CREATE INDEX idx_analytics_date ON analytics(metric_date);
CREATE INDEX idx_analytics_platform ON analytics(platform);
CREATE INDEX idx_analytics_type ON analytics(metric_type);
```

### 12. System Logs Table

```sql
CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Log Info
    log_level VARCHAR(20) NOT NULL, -- debug, info, warning, error, critical
    component VARCHAR(100), -- service name, module name
    message TEXT NOT NULL,
    
    -- Context
    character_id UUID REFERENCES characters(id),
    platform_account_id UUID REFERENCES platform_accounts(id),
    content_id UUID REFERENCES content(id),
    post_id UUID REFERENCES posts(id),
    
    -- Additional Data
    metadata JSONB, -- Stack traces, request data, etc.
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT log_level_check CHECK (log_level IN ('debug', 'info', 'warning', 'error', 'critical'))
);

CREATE INDEX idx_logs_level ON system_logs(log_level);
CREATE INDEX idx_logs_component ON system_logs(component);
CREATE INDEX idx_logs_character ON system_logs(character_id);
CREATE INDEX idx_logs_created ON system_logs(created_at);
CREATE INDEX idx_logs_created_level ON system_logs(created_at, log_level);
```

---

## Data Relationships

### Entity Relationship Diagram (Simplified)

```
characters (1) ──< (N) character_personalities
characters (1) ──< (N) character_appearances
characters (1) ──< (N) content
characters (1) ──< (N) content_generations
characters (1) ──< (N) platform_accounts
characters (1) ──< (N) posts
characters (1) ──< (N) scheduled_posts
characters (1) ──< (N) automation_rules
characters (1) ──< (N) engagement_actions
characters (1) ──< (N) analytics

platform_accounts (1) ──< (N) posts
platform_accounts (1) ──< (N) scheduled_posts
platform_accounts (1) ──< (N) engagement_actions
platform_accounts (1) ──< (N) analytics

content (1) ──< (N) posts
content (1) ──< (N) scheduled_posts

automation_rules (1) ──< (N) scheduled_posts
```

---

## Data Models (Python/SQLAlchemy)

### Example: Character Model

```python
from sqlalchemy import Column, String, Integer, Boolean, Text, ARRAY, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

class Character(Base):
    __tablename__ = 'characters'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    bio = Column(Text)
    age = Column(Integer)
    location = Column(String(255))
    timezone = Column(String(50), default='UTC')
    interests = Column(ARRAY(String))
    profile_image_url = Column(Text)
    profile_image_path = Column(Text)
    
    status = Column(String(20), default='active')
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    personality = relationship("CharacterPersonality", back_populates="character", uselist=False)
    appearance = relationship("CharacterAppearance", back_populates="character", uselist=False)
    content_items = relationship("Content", back_populates="character")
    platform_accounts = relationship("PlatformAccount", back_populates="character")
    posts = relationship("Post", back_populates="character")
    
    __table_args__ = (
        CheckConstraint("status IN ('active', 'paused', 'error', 'deleted')", name='status_check'),
    )
```

---

## Database Migrations

### Strategy
- Use **Alembic** (SQLAlchemy migration tool)
- Version control all schema changes
- Test migrations on staging before production

### Initial Migration
```bash
# Initialize Alembic
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

---

## Backup & Recovery

### Backup Strategy
1. **Daily Full Backups**: pg_dump at 2 AM
2. **Hourly Incremental**: WAL archiving (if enabled)
3. **Retention**: 30 days daily, 7 days hourly
4. **Storage**: Local + remote (encrypted)

### Recovery Plan
1. Test restore procedures monthly
2. Document recovery steps
3. Keep backup verification logs

---

## Performance Optimization

### Indexes
- All foreign keys indexed
- Frequently queried columns indexed
- Composite indexes for common query patterns

### Partitioning (Future)
- `analytics` table by date (monthly partitions)
- `system_logs` table by date (weekly partitions)

### Query Optimization
- Use EXPLAIN ANALYZE for slow queries
- Avoid N+1 queries (use eager loading)
- Use connection pooling (SQLAlchemy pool)

---

## Security Considerations

### Data Encryption
- Encrypt sensitive fields (auth_data in platform_accounts)
- Use PostgreSQL's `pgcrypto` extension
- Encrypt backups

### Access Control
- Use database roles and permissions
- Application uses dedicated database user
- No direct database access for end users

### Audit Trail
- `system_logs` table for all critical actions
- Track who/what/when for sensitive operations

---

## Next Steps

1. **Set Up Database**: Install PostgreSQL, create database
2. **Initialize Alembic**: Set up migration system
3. **Create Models**: Define SQLAlchemy models
4. **Run Migrations**: Create initial schema
5. **Seed Data**: Add test characters and data
6. **Test Queries**: Verify performance and correctness
