# Database Schema & Data Models

**Version:** 2.0  
**Date:** January 2025  
**Last Updated:** January 2025  
**Status:** Production Ready  
**Document Owner:** CPO/CTO/CEO  
**Review Status:** ✅ Approved

---

## 📋 Document Metadata

### Purpose
Complete database schema design with all tables, relationships, indexes, data models, and database operations. This is the data layer foundation that all features depend on.

### Reading Order
**Read After:** [03-TECHNICAL-ARCHITECTURE.md](./03-TECHNICAL-ARCHITECTURE.md), [01-PRD.md](./01-PRD.md)  
**Read Before:** [05-API-DESIGN.md](./05-API-DESIGN.md) - API uses database schema, implementing any backend features

### Related Documents
**Prerequisites:**
- [03-TECHNICAL-ARCHITECTURE.md](./03-TECHNICAL-ARCHITECTURE.md) - Database choice and architecture
- [01-PRD.md](./01-PRD.md) - Functional requirements inform schema design

**Dependencies (Use This Document For):**
- [05-API-DESIGN.md](./05-API-DESIGN.md) - API endpoints use these models
- Backend implementation - All ORM models based on this schema
- [20-DEPLOYMENT-DEVOPS.md](./20-DEPLOYMENT-DEVOPS.md) - Database setup and migrations

**Related:**
- [10-FEATURE-ROADMAP.md](./10-FEATURE-ROADMAP.md) - Features require database changes
- [09-TESTING-STRATEGY.md](./09-TESTING-STRATEGY.md) - Test fixtures use this schema
- [23-SCALING-OPTIMIZATION.md](./23-SCALING-OPTIMIZATION.md) - Database scaling strategies

### Key Sections
1. Database Choice & Rationale
2. Complete Entity Relationship Diagram (ERD)
3. Detailed Schema with Relationships
4. Indexing Strategies
5. Data Integrity Constraints
6. Migration Examples
7. Performance Optimization
8. Backup & Restore Procedures
9. Security Considerations
10. Data Models (SQLAlchemy)

---

## 1. Database Choice & Rationale

### 1.1 PostgreSQL 15+

**Why PostgreSQL:**
- ✅ **Robust & Reliable**: Production-proven, ACID compliant
- ✅ **Open-Source**: Free, no licensing costs
- ✅ **Excellent JSON Support**: JSONB for flexible schemas
- ✅ **Complex Relationships**: Handles complex relational data
- ✅ **Performance**: Excellent query performance with proper indexing
- ✅ **Extensions**: Rich ecosystem of extensions
- ✅ **Community**: Large, active community

**Alternatives Considered:**
- **MySQL**: Less JSON support, fewer advanced features
- **MongoDB**: Less suitable for relational data, consistency concerns
- **SQLite**: Not for production, limited concurrency

**Decision**: PostgreSQL is the best choice for relational data with JSON flexibility.

### 1.2 PostgreSQL Extensions

**Required Extensions:**
```sql
-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Text search (for full-text search)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Encryption (for sensitive data)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

### 1.3 Database Configuration

**Recommended Settings:**
```sql
-- Connection settings
max_connections = 100
shared_buffers = 8GB  -- 25% of RAM
effective_cache_size = 24GB  -- 75% of RAM
work_mem = 256MB
maintenance_work_mem = 2GB

-- Performance
random_page_cost = 1.1  -- For SSD
effective_io_concurrency = 200  -- For SSD

-- Logging
log_statement = 'all'  -- For development
log_duration = on
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
```

---

## 2. Complete Entity Relationship Diagram (ERD)

### 2.1 Full ERD (ASCII)

```
┌─────────────────────────────────────────────────────────────────┐
│                    AInfluencer Database Schema                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────┐
│     characters      │
│─────────────────────│
│ PK id (UUID)        │
│    name             │
│    bio              │
│    age              │
│    location         │
│    timezone         │
│    interests[]      │
│    status           │
│    is_active        │
│    created_at       │
│    updated_at       │
│    deleted_at       │
└──────────┬──────────┘
           │
           │ 1:1
           ├──────────────────────────────────┐
           │                                  │
           │ 1:1                             │ 1:1
           ▼                                  ▼
┌─────────────────────┐          ┌─────────────────────┐
│character_personalities│        │character_appearances│
│─────────────────────│          │─────────────────────│
│ PK id (UUID)        │          │ PK id (UUID)        │
│ FK character_id     │          │ FK character_id     │
│    extroversion     │          │    face_ref_path    │
│    creativity        │          │    face_method      │
│    humor            │          │    hair_color        │
│    communication_style│       │    eye_color        │
│    llm_prompt       │          │    base_model       │
│    temperature      │          │    style_keywords[]  │
└─────────────────────┘          └─────────────────────┘
           │
           │ 1:N
           │
           ▼
┌─────────────────────┐
│      content        │
│─────────────────────│
│ PK id (UUID)        │
│ FK character_id     │
│    content_type     │
│    file_path        │
│    prompt           │
│    quality_score    │
│    is_approved      │
│    times_used       │
└──────────┬──────────┘
           │
           │ 1:N
           ▼
┌─────────────────────┐
│       posts         │
│─────────────────────│
│ PK id (UUID)        │
│ FK character_id     │
│ FK platform_account_id│
│ FK content_id       │
│    platform         │
│    platform_post_id │
│    caption          │
│    likes_count      │
│    status           │
└──────────┬──────────┘
           │
           │ Referenced by
           ▼
┌─────────────────────┐
│  engagement_actions │
│─────────────────────│
│ PK id (UUID)        │
│ FK character_id     │
│ FK platform_account_id│
│    action_type      │
│    target_id        │
│    status           │
└─────────────────────┘

┌─────────────────────┐
│  platform_accounts  │
│─────────────────────│
│ PK id (UUID)        │
│ FK character_id     │
│    platform         │
│    account_username │
│    auth_data (JSONB)│
│    is_connected     │
│    follower_count   │
└──────────┬──────────┘
           │
           │ 1:N
           ├──────────────────┐
           │                  │
           ▼                  ▼
┌─────────────────────┐  ┌─────────────────────┐
│  scheduled_posts    │  │     analytics       │
│─────────────────────│  │─────────────────────│
│ PK id (UUID)        │  │ PK id (UUID)        │
│ FK character_id     │  │ FK character_id     │
│ FK platform_account_id│ │ FK platform_account_id│
│ FK content_id       │  │    metric_date      │
│ FK automation_rule_id│ │    metric_type      │
│    scheduled_at     │  │    metric_value     │
│    status           │  └─────────────────────┘
└──────────┬──────────┘
           │
           │ Referenced by
           ▼
┌─────────────────────┐
│  automation_rules   │
│─────────────────────│
│ PK id (UUID)        │
│ FK character_id     │
│    name             │
│    trigger_type     │
│    trigger_config   │
│    is_enabled       │
└─────────────────────┘

┌─────────────────────┐
│ content_generations │
│─────────────────────│
│ PK id (UUID)        │
│ FK character_id     │
│    job_type         │
│    status           │
│    prompt           │
│    generated_content_ids[]│
└─────────────────────┘

┌─────────────────────┐
│   system_logs       │
│─────────────────────│
│ PK id (UUID)        │
│ FK character_id (opt)│
│ FK platform_account_id (opt)│
│ FK content_id (opt) │
│ FK post_id (opt)    │
│    log_level        │
│    component        │
│    message          │
│    metadata (JSONB) │
└─────────────────────┘
```

### 2.2 Relationship Summary

#### One-to-One Relationships
- `characters` → `character_personalities` (1:1)
- `characters` → `character_appearances` (1:1)

#### One-to-Many Relationships
- `characters` → `content` (1:N)
- `characters` → `platform_accounts` (1:N)
- `characters` → `posts` (1:N)
- `characters` → `automation_rules` (1:N)
- `characters` → `engagement_actions` (1:N)
- `characters` → `analytics` (1:N)
- `characters` → `content_generations` (1:N)
- `platform_accounts` → `posts` (1:N)
- `platform_accounts` → `scheduled_posts` (1:N)
- `platform_accounts` → `engagement_actions` (1:N)
- `platform_accounts` → `analytics` (1:N)
- `content` → `posts` (1:N)
- `content` → `scheduled_posts` (1:N)
- `automation_rules` → `scheduled_posts` (1:N)

#### Many-to-Many (via Junction)
- `content` ↔ `posts` (via `content_id` foreign key)
- `content` ↔ `scheduled_posts` (via `content_id` foreign key)

### 2.3 Relationship Details

#### Character → Personality (1:1)
**Relationship Type**: One-to-One  
**Cardinality**: Each character has exactly one personality  
**Cascade**: CASCADE DELETE (if character deleted, personality deleted)  
**Constraint**: UNIQUE constraint on `character_id`

**Usage:**
- Personality affects all content generation
- Personality can be updated independently
- Personality is required for character creation

#### Character → Appearance (1:1)
**Relationship Type**: One-to-One  
**Cardinality**: Each character has exactly one appearance  
**Cascade**: CASCADE DELETE  
**Constraint**: UNIQUE constraint on `character_id`

**Usage:**
- Appearance defines visual characteristics
- Appearance affects image/video generation
- Appearance can be updated independently

#### Character → Content (1:N)
**Relationship Type**: One-to-Many  
**Cardinality**: Each character can have unlimited content  
**Cascade**: CASCADE DELETE  
**Index**: Indexed on `character_id` for fast lookups

**Usage:**
- All generated content belongs to a character
- Content can be filtered by character
- Content library per character

#### Character → Platform Accounts (1:N)
**Relationship Type**: One-to-Many  
**Cardinality**: Each character can have multiple platform accounts (one per platform)  
**Cascade**: CASCADE DELETE  
**Constraint**: UNIQUE constraint on `(character_id, platform)` - one account per platform per character

**Usage:**
- Character can be on multiple platforms
- Each platform has separate account
- Platform accounts managed per character

#### Platform Account → Posts (1:N)
**Relationship Type**: One-to-Many  
**Cardinality**: Each platform account can have unlimited posts  
**Cascade**: CASCADE DELETE  
**Index**: Indexed on `platform_account_id` and `platform`

**Usage:**
- All posts belong to a platform account
- Posts can be filtered by platform
- Platform-specific post management

#### Content → Posts (1:N)
**Relationship Type**: One-to-Many  
**Cardinality**: Content can be posted multiple times (reuse)  
**Cascade**: SET NULL (posts can exist if content deleted)  
**Index**: Indexed on `content_id`

**Usage:**
- Content can be reused across posts
- Track content usage (`times_used`)
- Content performance tracking

---

## 3. Detailed Schema

### 3.1 Characters Table

**Purpose**: Store AI influencer character profiles and basic information.

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
    CONSTRAINT status_check CHECK (status IN ('active', 'paused', 'error', 'deleted')),
    CONSTRAINT name_length_check CHECK (LENGTH(name) >= 1 AND LENGTH(name) <= 255),
    CONSTRAINT age_range_check CHECK (age IS NULL OR (age >= 0 AND age <= 150))
);

-- Indexes
CREATE INDEX idx_characters_status ON characters(status);
CREATE INDEX idx_characters_active ON characters(is_active) WHERE is_active = true;
CREATE INDEX idx_characters_created ON characters(created_at DESC);
CREATE INDEX idx_characters_name ON characters(name); -- For search
CREATE INDEX idx_characters_deleted ON characters(deleted_at) WHERE deleted_at IS NULL; -- For soft delete queries
```

**Field Descriptions:**
- `id`: Unique identifier (UUID)
- `name`: Character name (required, 1-255 chars)
- `bio`: Character biography/description
- `age`: Character age (optional, 0-150)
- `location`: Character location (e.g., "New York, USA")
- `timezone`: Timezone for scheduling (default UTC)
- `interests`: Array of interests (e.g., ["fitness", "travel"])
- `profile_image_url`: URL to profile image (if hosted)
- `profile_image_path`: Local file path to profile image
- `status`: Character status (active, paused, error, deleted)
- `is_active`: Quick active status check (boolean)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp (auto-updated)
- `deleted_at`: Soft delete timestamp (NULL if not deleted)

**Indexing Strategy:**
- `status`: Frequently filtered by status
- `is_active`: Partial index for active characters only
- `created_at`: Sorted by creation date
- `name`: For search functionality
- `deleted_at`: Partial index for non-deleted records

---

### 3.2 Character Personalities Table

**Purpose**: Store personality traits and behavior patterns that affect content generation.

```sql
CREATE TABLE character_personalities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    
    -- Personality Traits (0.0 to 1.0 scale)
    extroversion DECIMAL(3,2) DEFAULT 0.5 CHECK (extroversion >= 0.0 AND extroversion <= 1.0),
    creativity DECIMAL(3,2) DEFAULT 0.5 CHECK (creativity >= 0.0 AND creativity <= 1.0),
    humor DECIMAL(3,2) DEFAULT 0.5 CHECK (humor >= 0.0 AND humor <= 1.0),
    professionalism DECIMAL(3,2) DEFAULT 0.5 CHECK (professionalism >= 0.0 AND professionalism <= 1.0),
    authenticity DECIMAL(3,2) DEFAULT 0.5 CHECK (authenticity >= 0.0 AND authenticity <= 1.0),
    energy_level DECIMAL(3,2) DEFAULT 0.5 CHECK (energy_level >= 0.0 AND energy_level <= 1.0),
    
    -- Communication Style
    communication_style VARCHAR(50), -- casual, professional, friendly, sassy, etc.
    preferred_topics TEXT[], -- Array of topics
    content_tone VARCHAR(50), -- positive, neutral, edgy, etc.
    emoji_usage VARCHAR(20) DEFAULT 'moderate', -- none, minimal, moderate, heavy
    
    -- LLM Settings
    llm_personality_prompt TEXT, -- Custom prompt for LLM
    temperature DECIMAL(3,2) DEFAULT 0.7 CHECK (temperature >= 0.0 AND temperature <= 2.0),
    
    -- Flirting Settings (if applicable)
    flirtatiousness_level DECIMAL(3,2) DEFAULT 0.0 CHECK (flirtatiousness_level >= 0.0 AND flirtatiousness_level <= 1.0),
    flirting_style VARCHAR(50), -- subtle, playful, romantic, suggestive
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_character_personality UNIQUE (character_id),
    CONSTRAINT communication_style_check CHECK (communication_style IN ('casual', 'professional', 'friendly', 'sassy', 'inspirational', NULL)),
    CONSTRAINT content_tone_check CHECK (content_tone IN ('positive', 'neutral', 'edgy', 'humorous', 'serious', NULL)),
    CONSTRAINT emoji_usage_check CHECK (emoji_usage IN ('none', 'minimal', 'moderate', 'heavy'))
);

-- Indexes
CREATE INDEX idx_personalities_character ON character_personalities(character_id);
CREATE INDEX idx_personalities_style ON character_personalities(communication_style) WHERE communication_style IS NOT NULL;
```

**Field Descriptions:**
- `extroversion`: 0.0 (introverted) to 1.0 (extroverted)
- `creativity`: 0.0 (practical) to 1.0 (creative)
- `humor`: 0.0 (serious) to 1.0 (humorous)
- `professionalism`: 0.0 (casual) to 1.0 (professional)
- `authenticity`: 0.0 (polished) to 1.0 (authentic)
- `energy_level`: 0.0 (calm) to 1.0 (energetic)
- `communication_style`: Overall communication style
- `preferred_topics`: Array of topics character likes
- `content_tone`: Tone of content (positive, neutral, etc.)
- `emoji_usage`: How much emojis are used
- `llm_personality_prompt`: Custom prompt for LLM
- `temperature`: LLM temperature (0.0-2.0)
- `flirtatiousness_level`: Flirting level (0.0-1.0)
- `flirting_style`: Style of flirting

**Data Integrity:**
- All personality traits are constrained to 0.0-1.0 range
- Communication style and tone have CHECK constraints
- One personality per character (UNIQUE constraint)

---

### 3.3 Character Appearances Table

**Purpose**: Store physical attributes and face consistency settings.

```sql
CREATE TABLE character_appearances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    
    -- Face Consistency
    face_reference_image_url TEXT,
    face_reference_image_path TEXT,
    face_consistency_method VARCHAR(50) DEFAULT 'ip-adapter', -- ip-adapter, instantid, faceid, lora
    lora_model_path TEXT, -- If using LoRA
    face_consistency_weight DECIMAL(3,2) DEFAULT 0.7 CHECK (face_consistency_weight >= 0.0 AND face_consistency_weight <= 1.0),
    
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
    
    CONSTRAINT unique_character_appearance UNIQUE (character_id),
    CONSTRAINT face_method_check CHECK (face_consistency_method IN ('ip-adapter', 'instantid', 'faceid', 'lora', 'none'))
);

-- Indexes
CREATE INDEX idx_appearances_character ON character_appearances(character_id);
CREATE INDEX idx_appearances_method ON character_appearances(face_consistency_method);
```

**Field Descriptions:**
- `face_reference_image_path`: Path to face reference image
- `face_consistency_method`: Method used for face consistency
- `lora_model_path`: Path to LoRA model (if using LoRA)
- `face_consistency_weight`: Strength of face consistency (0.0-1.0)
- `base_model`: Stable Diffusion model name
- `negative_prompt`: Default negative prompt
- `default_prompt_prefix`: Prefix added to all generation prompts

---

### 3.4 Content Table

**Purpose**: Store all generated content (images, videos, text, audio).

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
    seed INTEGER, -- For reproducibility
    
    -- Quality & Status
    quality_score DECIMAL(3,2) CHECK (quality_score IS NULL OR (quality_score >= 0.0 AND quality_score <= 1.0)),
    is_approved BOOLEAN DEFAULT false,
    approval_status VARCHAR(20) DEFAULT 'pending', -- pending, approved, rejected
    rejection_reason TEXT,
    
    -- Usage
    times_used INTEGER DEFAULT 0 CHECK (times_used >= 0),
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    -- Tags & Organization
    tags TEXT[], -- User-defined tags
    folder_path TEXT, -- Organization folder
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT content_type_check CHECK (content_type IN ('image', 'video', 'text', 'audio')),
    CONSTRAINT approval_status_check CHECK (approval_status IN ('pending', 'approved', 'rejected')),
    CONSTRAINT file_size_check CHECK (file_size IS NULL OR file_size > 0),
    CONSTRAINT dimensions_check CHECK (
        (content_type IN ('image', 'video') AND width IS NOT NULL AND height IS NOT NULL) OR
        (content_type NOT IN ('image', 'video'))
    )
);

-- Indexes
CREATE INDEX idx_content_character ON content(character_id);
CREATE INDEX idx_content_type ON content(content_type);
CREATE INDEX idx_content_category ON content(content_category) WHERE content_category IS NOT NULL;
CREATE INDEX idx_content_approved ON content(is_approved) WHERE is_approved = true;
CREATE INDEX idx_content_nsfw ON content(is_nsfw) WHERE is_nsfw = true;
CREATE INDEX idx_content_created ON content(created_at DESC);
CREATE INDEX idx_content_quality ON content(quality_score DESC) WHERE quality_score IS NOT NULL;
CREATE INDEX idx_content_tags ON content USING GIN(tags); -- GIN index for array search
CREATE INDEX idx_content_status ON content(approval_status);
```

**Field Descriptions:**
- `content_type`: Type of content (image, video, text, audio)
- `content_category`: Category (post, story, reel, etc.)
- `is_nsfw`: +18 content flag
- `file_path`: Local storage path (required)
- `generation_settings`: JSONB with model settings (steps, CFG, etc.)
- `quality_score`: Automated quality score (0.0-1.0)
- `times_used`: How many times content has been posted
- `tags`: User-defined tags for organization
- `folder_path`: Organization folder path

**Indexing Strategy:**
- `character_id`: Most common filter
- `content_type`: Filter by type
- `is_approved`: Partial index for approved content
- `tags`: GIN index for array search
- `created_at`: Sorted by date
- `quality_score`: Sorted by quality

---

### 3.5 Content Generations Table

**Purpose**: Track content generation jobs and their results.

```sql
CREATE TABLE content_generations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    
    -- Job Info
    job_type VARCHAR(50) NOT NULL, -- image, video, text, batch
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed, cancelled
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10), -- 1 (highest) to 10 (lowest)
    
    -- Generation Parameters
    prompt TEXT NOT NULL,
    negative_prompt TEXT,
    generation_settings JSONB NOT NULL,
    batch_size INTEGER DEFAULT 1 CHECK (batch_size >= 1 AND batch_size <= 100),
    
    -- Results
    generated_content_ids UUID[], -- Array of content.id
    success_count INTEGER DEFAULT 0 CHECK (success_count >= 0),
    failure_count INTEGER DEFAULT 0 CHECK (failure_count >= 0),
    
    -- Error Handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0 CHECK (retry_count >= 0),
    max_retries INTEGER DEFAULT 3 CHECK (max_retries >= 0 AND max_retries <= 10),
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER CHECK (duration_seconds IS NULL OR duration_seconds >= 0),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT status_check CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    CONSTRAINT job_type_check CHECK (job_type IN ('image', 'video', 'text', 'audio', 'batch')),
    CONSTRAINT timing_check CHECK (
        (started_at IS NULL AND completed_at IS NULL) OR
        (started_at IS NOT NULL AND (completed_at IS NULL OR completed_at >= started_at))
    )
);

-- Indexes
CREATE INDEX idx_generations_character ON content_generations(character_id);
CREATE INDEX idx_generations_status ON content_generations(status);
CREATE INDEX idx_generations_priority ON content_generations(priority ASC, created_at ASC); -- For queue processing
CREATE INDEX idx_generations_job_type ON content_generations(job_type);
CREATE INDEX idx_generations_created ON content_generations(created_at DESC);
CREATE INDEX idx_generations_pending ON content_generations(priority, created_at) WHERE status = 'pending'; -- For queue
```

**Indexing Strategy:**
- `status`: Filter by status
- `priority, created_at`: Composite index for queue processing (process by priority, then FIFO)
- `pending status`: Partial index for pending jobs only

---

### 3.6 Platform Accounts Table

**Purpose**: Store social media platform account connections and credentials.

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
    connection_status VARCHAR(20) DEFAULT 'disconnected', -- connected, disconnected, error, rate_limited, suspended
    
    -- Account Stats (cached)
    follower_count INTEGER DEFAULT 0 CHECK (follower_count >= 0),
    following_count INTEGER DEFAULT 0 CHECK (following_count >= 0),
    post_count INTEGER DEFAULT 0 CHECK (post_count >= 0),
    last_synced_at TIMESTAMP WITH TIME ZONE,
    
    -- Settings
    auto_posting_enabled BOOLEAN DEFAULT true,
    auto_engagement_enabled BOOLEAN DEFAULT true,
    posting_frequency VARCHAR(50), -- daily, weekly, custom
    engagement_frequency VARCHAR(50),
    
    -- Rate Limiting
    rate_limit_remaining INTEGER CHECK (rate_limit_remaining IS NULL OR rate_limit_remaining >= 0),
    rate_limit_reset_at TIMESTAMP WITH TIME ZONE,
    last_rate_limit_hit_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT platform_check CHECK (platform IN ('instagram', 'twitter', 'facebook', 'telegram', 'onlyfans', 'youtube')),
    CONSTRAINT connection_status_check CHECK (connection_status IN ('connected', 'disconnected', 'error', 'rate_limited', 'suspended')),
    CONSTRAINT auth_type_check CHECK (auth_type IN ('api_key', 'oauth', 'browser_session', 'cookie', NULL)),
    CONSTRAINT unique_character_platform UNIQUE (character_id, platform)
);

-- Indexes
CREATE INDEX idx_platform_accounts_character ON platform_accounts(character_id);
CREATE INDEX idx_platform_accounts_platform ON platform_accounts(platform);
CREATE INDEX idx_platform_accounts_connected ON platform_accounts(is_connected) WHERE is_connected = true;
CREATE INDEX idx_platform_accounts_status ON platform_accounts(connection_status);
CREATE INDEX idx_platform_accounts_username ON platform_accounts(account_username) WHERE account_username IS NOT NULL;
```

**Security Considerations:**
- `auth_data` is JSONB and should be encrypted using `pgcrypto`
- Credentials should never be logged
- Use environment variables for encryption keys

---

### 3.7 Posts Table

**Purpose**: Store published posts across all platforms.

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
    content_id UUID REFERENCES content(id) ON DELETE SET NULL, -- Primary content (image/video)
    additional_content_ids UUID[], -- Array of additional content IDs
    
    -- Text Content
    caption TEXT,
    hashtags TEXT[],
    mentions TEXT[],
    
    -- Engagement (cached from platform)
    likes_count INTEGER DEFAULT 0 CHECK (likes_count >= 0),
    comments_count INTEGER DEFAULT 0 CHECK (comments_count >= 0),
    shares_count INTEGER DEFAULT 0 CHECK (shares_count >= 0),
    views_count INTEGER DEFAULT 0 CHECK (views_count >= 0),
    last_engagement_sync_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft', -- draft, scheduled, published, failed, deleted
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Error Handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0 CHECK (retry_count >= 0),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT platform_check CHECK (platform IN ('instagram', 'twitter', 'facebook', 'telegram', 'onlyfans', 'youtube')),
    CONSTRAINT status_check CHECK (status IN ('draft', 'scheduled', 'published', 'failed', 'deleted')),
    CONSTRAINT post_type_check CHECK (post_type IN ('post', 'story', 'reel', 'short', 'tweet', 'message', 'video', NULL)),
    CONSTRAINT platform_post_id_unique UNIQUE (platform, platform_post_id) WHERE platform_post_id IS NOT NULL
);

-- Indexes
CREATE INDEX idx_posts_character ON posts(character_id);
CREATE INDEX idx_posts_platform_account ON posts(platform_account_id);
CREATE INDEX idx_posts_platform ON posts(platform);
CREATE INDEX idx_posts_status ON posts(status);
CREATE INDEX idx_posts_published ON posts(published_at DESC);
CREATE INDEX idx_posts_platform_post_id ON posts(platform, platform_post_id) WHERE platform_post_id IS NOT NULL;
CREATE INDEX idx_posts_content ON posts(content_id) WHERE content_id IS NOT NULL;
CREATE INDEX idx_posts_hashtags ON posts USING GIN(hashtags); -- GIN index for array search
CREATE INDEX idx_posts_engagement ON posts(likes_count DESC, comments_count DESC) WHERE status = 'published';
```

**Indexing Strategy:**
- `character_id`: Filter by character
- `platform`: Filter by platform
- `published_at`: Sorted by publication date
- `hashtags`: GIN index for array search
- `engagement`: Composite index for top-performing posts

---

### 3.8 Scheduled Posts Table

**Purpose**: Queue posts for future publishing.

```sql
CREATE TABLE scheduled_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    platform_account_id UUID NOT NULL REFERENCES platform_accounts(id) ON DELETE CASCADE,
    
    -- Scheduling
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Post Content
    content_id UUID REFERENCES content(id) ON DELETE SET NULL,
    additional_content_ids UUID[],
    caption TEXT,
    hashtags TEXT[],
    post_type VARCHAR(50),
    
    -- Status
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, processing, published, failed, cancelled
    
    -- Automation Rule (if from rule)
    automation_rule_id UUID, -- References automation_rules(id) ON DELETE SET NULL
    
    -- Error Handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0 CHECK (retry_count >= 0),
    max_retries INTEGER DEFAULT 3 CHECK (max_retries >= 0 AND max_retries <= 10),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT status_check CHECK (status IN ('scheduled', 'processing', 'published', 'failed', 'cancelled')),
    CONSTRAINT scheduled_at_future CHECK (scheduled_at > created_at OR scheduled_at = created_at)
);

-- Indexes
CREATE INDEX idx_scheduled_posts_character ON scheduled_posts(character_id);
CREATE INDEX idx_scheduled_posts_scheduled_at ON scheduled_posts(scheduled_at ASC) WHERE status = 'scheduled'; -- For scheduler
CREATE INDEX idx_scheduled_posts_status ON scheduled_posts(status);
CREATE INDEX idx_scheduled_posts_platform ON scheduled_posts(platform_account_id);
CREATE INDEX idx_scheduled_posts_rule ON scheduled_posts(automation_rule_id) WHERE automation_rule_id IS NOT NULL;
```

**Critical Index:**
- `scheduled_at` with `status = 'scheduled'` partial index is critical for the scheduler to efficiently find posts ready to publish.

---

### 3.9 Automation Rules Table

**Purpose**: Store automation rule configurations.

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
    platforms TEXT[] NOT NULL CHECK (array_length(platforms, 1) > 0), -- At least one platform
    content_type VARCHAR(20), -- image, video, text, mixed
    content_category VARCHAR(50), -- post, story, reel, etc.
    
    -- Content Generation
    prompt_template TEXT,
    generation_settings JSONB,
    min_content_quality DECIMAL(3,2) DEFAULT 0.7 CHECK (min_content_quality >= 0.0 AND min_content_quality <= 1.0),
    
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
    max_posts_per_day INTEGER CHECK (max_posts_per_day IS NULL OR max_posts_per_day > 0),
    max_posts_per_week INTEGER CHECK (max_posts_per_week IS NULL OR max_posts_per_week > 0),
    cooldown_minutes INTEGER DEFAULT 60 CHECK (cooldown_minutes >= 0),
    
    -- Statistics
    times_executed INTEGER DEFAULT 0 CHECK (times_executed >= 0),
    last_executed_at TIMESTAMP WITH TIME ZONE,
    success_count INTEGER DEFAULT 0 CHECK (success_count >= 0),
    failure_count INTEGER DEFAULT 0 CHECK (failure_count >= 0),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT trigger_type_check CHECK (trigger_type IN ('schedule', 'event', 'manual')),
    CONSTRAINT content_type_check CHECK (content_type IN ('image', 'video', 'text', 'mixed', NULL)),
    CONSTRAINT hashtag_strategy_check CHECK (hashtag_strategy IN ('auto', 'template', 'none', NULL))
);

-- Indexes
CREATE INDEX idx_automation_rules_character ON automation_rules(character_id);
CREATE INDEX idx_automation_rules_enabled ON automation_rules(is_enabled) WHERE is_enabled = true;
CREATE INDEX idx_automation_rules_trigger ON automation_rules(trigger_type);
CREATE INDEX idx_automation_rules_platforms ON automation_rules USING GIN(platforms); -- GIN index for array search
```

---

### 3.10 Engagement Actions Table

**Purpose**: Track all engagement actions (likes, comments, follows, etc.).

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
    retry_count INTEGER DEFAULT 0 CHECK (retry_count >= 0),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT platform_check CHECK (platform IN ('instagram', 'twitter', 'facebook', 'telegram', 'onlyfans', 'youtube')),
    CONSTRAINT action_type_check CHECK (action_type IN ('like', 'comment', 'share', 'follow', 'unfollow', 'message', 'reply')),
    CONSTRAINT status_check CHECK (status IN ('pending', 'completed', 'failed', 'cancelled'))
);

-- Indexes
CREATE INDEX idx_engagement_character ON engagement_actions(character_id);
CREATE INDEX idx_engagement_platform_account ON engagement_actions(platform_account_id);
CREATE INDEX idx_engagement_status ON engagement_actions(status);
CREATE INDEX idx_engagement_created ON engagement_actions(created_at DESC);
CREATE INDEX idx_engagement_type ON engagement_actions(action_type);
CREATE INDEX idx_engagement_platform ON engagement_actions(platform);
CREATE INDEX idx_engagement_pending ON engagement_actions(created_at ASC) WHERE status = 'pending'; -- For queue processing
```

---

### 3.11 Analytics Table

**Purpose**: Store performance metrics and statistics.

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
    CONSTRAINT metric_type_check CHECK (metric_type IN (
        'follower_count', 'following_count', 'post_count',
        'engagement_rate', 'likes_count', 'comments_count',
        'shares_count', 'views_count', 'reach', 'impressions'
    )),
    CONSTRAINT unique_metric UNIQUE (character_id, platform_account_id, metric_date, metric_type)
);

-- Indexes
CREATE INDEX idx_analytics_character ON analytics(character_id);
CREATE INDEX idx_analytics_date ON analytics(metric_date DESC);
CREATE INDEX idx_analytics_platform ON analytics(platform) WHERE platform IS NOT NULL;
CREATE INDEX idx_analytics_type ON analytics(metric_type);
CREATE INDEX idx_analytics_character_date ON analytics(character_id, metric_date DESC);
CREATE INDEX idx_analytics_character_platform_date ON analytics(character_id, platform, metric_date DESC) WHERE platform IS NOT NULL;
```

**Partitioning Strategy (Future):**
- Partition by `metric_date` (monthly partitions)
- Improves query performance for date-range queries
- Easier to archive old data

---

### 3.12 System Logs Table

**Purpose**: Store application and error logs.

```sql
CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Log Info
    log_level VARCHAR(20) NOT NULL, -- debug, info, warning, error, critical
    component VARCHAR(100), -- service name, module name
    message TEXT NOT NULL,
    
    -- Context
    character_id UUID REFERENCES characters(id) ON DELETE SET NULL,
    platform_account_id UUID REFERENCES platform_accounts(id) ON DELETE SET NULL,
    content_id UUID REFERENCES content(id) ON DELETE SET NULL,
    post_id UUID REFERENCES posts(id) ON DELETE SET NULL,
    
    -- Additional Data
    metadata JSONB, -- Stack traces, request data, etc.
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT log_level_check CHECK (log_level IN ('debug', 'info', 'warning', 'error', 'critical'))
);

-- Indexes
CREATE INDEX idx_logs_level ON system_logs(log_level);
CREATE INDEX idx_logs_component ON system_logs(component) WHERE component IS NOT NULL;
CREATE INDEX idx_logs_character ON system_logs(character_id) WHERE character_id IS NOT NULL;
CREATE INDEX idx_logs_created ON system_logs(created_at DESC);
CREATE INDEX idx_logs_created_level ON system_logs(created_at DESC, log_level);
CREATE INDEX idx_logs_error ON system_logs(created_at DESC) WHERE log_level IN ('error', 'critical');
```

**Partitioning Strategy (Future):**
- Partition by `created_at` (weekly partitions)
- Improves query performance
- Easier log retention and cleanup

---

## 4. Indexing Strategies

### 4.1 Index Types Used

#### B-Tree Indexes (Default)
**Use Cases:**
- Equality and range queries
- Sorting operations
- Foreign keys
- Frequently filtered columns

**Examples:**
- `idx_characters_status` - Filter by status
- `idx_posts_published` - Sort by publication date
- `idx_content_character` - Filter by character

#### Partial Indexes
**Use Cases:**
- Index subset of rows
- Reduce index size
- Improve query performance for specific conditions

**Examples:**
- `idx_characters_active` - Only index active characters
- `idx_content_approved` - Only index approved content
- `idx_scheduled_posts_scheduled_at` - Only index scheduled (not published) posts

#### GIN Indexes (Generalized Inverted Index)
**Use Cases:**
- Array columns
- JSONB columns
- Full-text search

**Examples:**
- `idx_content_tags` - Search by tags array
- `idx_posts_hashtags` - Search by hashtags array
- `idx_automation_rules_platforms` - Search by platforms array

#### Composite Indexes
**Use Cases:**
- Multiple column queries
- Query optimization
- Covering indexes

**Examples:**
- `idx_generations_priority` - (priority, created_at) for queue processing
- `idx_analytics_character_date` - (character_id, metric_date) for analytics queries

### 4.2 Index Maintenance

#### Index Monitoring
```sql
-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Check index sizes
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;
```

#### Index Optimization
- **Unused Indexes**: Remove indexes that are never used
- **Duplicate Indexes**: Remove redundant indexes
- **Index Bloat**: Rebuild indexes periodically
- **Covering Indexes**: Add columns to indexes to avoid table lookups

---

## 5. Data Integrity Constraints

### 5.1 Primary Key Constraints
- All tables use UUID primary keys
- UUIDs generated using `uuid_generate_v4()`
- Ensures uniqueness across distributed systems

### 5.2 Foreign Key Constraints
- All foreign keys have `ON DELETE CASCADE` or `ON DELETE SET NULL`
- Ensures referential integrity
- Prevents orphaned records

### 5.3 Check Constraints

#### Status Constraints
```sql
-- Character status
CONSTRAINT status_check CHECK (status IN ('active', 'paused', 'error', 'deleted'))

-- Post status
CONSTRAINT status_check CHECK (status IN ('draft', 'scheduled', 'published', 'failed', 'deleted'))

-- Generation status
CONSTRAINT status_check CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled'))
```

#### Range Constraints
```sql
-- Personality traits (0.0-1.0)
CONSTRAINT extroversion_check CHECK (extroversion >= 0.0 AND extroversion <= 1.0)

-- Age range
CONSTRAINT age_range_check CHECK (age IS NULL OR (age >= 0 AND age <= 150))

-- File size
CONSTRAINT file_size_check CHECK (file_size IS NULL OR file_size > 0)
```

#### Array Constraints
```sql
-- At least one platform required
CONSTRAINT platforms_check CHECK (array_length(platforms, 1) > 0)
```

### 5.4 Unique Constraints

#### Single Column Unique
```sql
-- One personality per character
CONSTRAINT unique_character_personality UNIQUE (character_id)

-- One appearance per character
CONSTRAINT unique_character_appearance UNIQUE (character_id)
```

#### Composite Unique
```sql
-- One platform account per platform per character
CONSTRAINT unique_character_platform UNIQUE (character_id, platform)

-- One metric per character/platform/date/type
CONSTRAINT unique_metric UNIQUE (character_id, platform_account_id, metric_date, metric_type)

-- One platform post ID per platform
CONSTRAINT platform_post_id_unique UNIQUE (platform, platform_post_id) WHERE platform_post_id IS NOT NULL
```

---

## 6. Migration Examples

### 6.1 Initial Schema Migration

**Alembic Migration Example:**

```python
# alembic/versions/001_initial_schema.py
"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    
    # Create characters table
    op.create_table(
        'characters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('bio', sa.Text()),
        sa.Column('age', sa.Integer()),
        sa.Column('location', sa.String(255)),
        sa.Column('timezone', sa.String(50), server_default='UTC'),
        sa.Column('interests', postgresql.ARRAY(sa.String())),
        sa.Column('profile_image_url', sa.Text()),
        sa.Column('profile_image_path', sa.Text()),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('active', 'paused', 'error', 'deleted')", name='status_check')
    )
    
    # Create indexes
    op.create_index('idx_characters_status', 'characters', ['status'])
    op.create_index('idx_characters_active', 'characters', ['is_active'], postgresql_where=sa.text('is_active = true'))
    op.create_index('idx_characters_created', 'characters', ['created_at'])
    
    # Create other tables...
    # (Similar pattern for all tables)

def downgrade():
    # Drop tables in reverse order
    op.drop_table('system_logs')
    op.drop_table('analytics')
    op.drop_table('engagement_actions')
    op.drop_table('automation_rules')
    op.drop_table('scheduled_posts')
    op.drop_table('posts')
    op.drop_table('platform_accounts')
    op.drop_table('content_generations')
    op.drop_table('content')
    op.drop_table('character_appearances')
    op.drop_table('character_personalities')
    op.drop_table('characters')
    
    # Drop extensions
    op.execute('DROP EXTENSION IF EXISTS "pgcrypto"')
    op.execute('DROP EXTENSION IF EXISTS "pg_trgm"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
```

### 6.2 Adding New Column Migration

**Example: Adding `flirtatiousness_level` to personalities:**

```python
# alembic/versions/002_add_flirting_to_personalities.py
"""Add flirting settings to personalities

Revision ID: 002
Revises: 001
Create Date: 2025-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('character_personalities', 
        sa.Column('flirtatiousness_level', sa.Numeric(3, 2), server_default='0.0')
    )
    op.add_column('character_personalities',
        sa.Column('flirting_style', sa.String(50), nullable=True)
    )
    op.create_check_constraint(
        'flirtatiousness_level_check',
        'character_personalities',
        'flirtatiousness_level >= 0.0 AND flirtatiousness_level <= 1.0'
    )

def downgrade():
    op.drop_constraint('flirtatiousness_level_check', 'character_personalities')
    op.drop_column('character_personalities', 'flirting_style')
    op.drop_column('character_personalities', 'flirtatiousness_level')
```

### 6.3 Data Migration Example

**Example: Migrating existing data:**

```python
# alembic/versions/003_migrate_old_data.py
"""Migrate old data format

Revision ID: 003
Revises: 002
Create Date: 2025-01-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade():
    # Update existing records
    op.execute("""
        UPDATE characters 
        SET status = 'active' 
        WHERE status IS NULL
    """)
    
    # Set default timezone for existing records
    op.execute("""
        UPDATE characters 
        SET timezone = 'UTC' 
        WHERE timezone IS NULL
    """)

def downgrade():
    # Revert changes if needed
    pass
```

---

## 7. Performance Optimization

### 7.1 Query Optimization

#### Common Query Patterns

**Pattern 1: Get Character with Related Data**
```sql
-- Optimized: Use JOINs instead of N+1 queries
SELECT 
    c.*,
    cp.*,
    ca.*,
    COUNT(DISTINCT p.id) as post_count,
    COUNT(DISTINCT pa.id) as platform_count
FROM characters c
LEFT JOIN character_personalities cp ON c.id = cp.character_id
LEFT JOIN character_appearances ca ON c.id = ca.character_id
LEFT JOIN posts p ON c.id = p.character_id
LEFT JOIN platform_accounts pa ON c.id = pa.character_id
WHERE c.id = $1
GROUP BY c.id, cp.id, ca.id;
```

**Pattern 2: Get Scheduled Posts Ready to Publish**
```sql
-- Optimized: Use partial index on scheduled_at
SELECT *
FROM scheduled_posts
WHERE status = 'scheduled'
  AND scheduled_at <= NOW()
ORDER BY scheduled_at ASC
LIMIT 100;
```

**Pattern 3: Get Content by Character with Filters**
```sql
-- Optimized: Use composite index
SELECT *
FROM content
WHERE character_id = $1
  AND content_type = $2
  AND is_approved = true
ORDER BY created_at DESC
LIMIT 20;
```

### 7.2 Connection Pooling

**SQLAlchemy Pool Configuration:**
```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  # Number of connections to maintain
    max_overflow=20,  # Additional connections allowed
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False  # Set to True for SQL logging
)
```

### 7.3 Query Caching

**Redis Caching Strategy:**
```python
# Cache character data for 5 minutes
cache_key = f"character:{character_id}"
cached_data = redis.get(cache_key)
if not cached_data:
    data = db.query(Character).filter(Character.id == character_id).first()
    redis.setex(cache_key, 300, json.dumps(data))  # 5 min TTL
else:
    data = json.loads(cached_data)
```

### 7.4 Database Tuning

**PostgreSQL Configuration:**
```sql
-- For 32GB RAM system
shared_buffers = 8GB  -- 25% of RAM
effective_cache_size = 24GB  -- 75% of RAM
work_mem = 256MB
maintenance_work_mem = 2GB
random_page_cost = 1.1  -- For SSD
effective_io_concurrency = 200  -- For SSD
```

---

## 8. Backup & Restore Procedures

### 8.1 Backup Strategy

#### Daily Full Backups
```bash
#!/bin/bash
# /opt/AInfluencer/scripts/backup-db.sh

BACKUP_DIR="/backups/ainfluencer"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/db_backup_$DATE.sql"

mkdir -p $BACKUP_DIR

# Full backup
pg_dump -U ainfluencer_user -d ainfluencer \
    --format=custom \
    --compress=9 \
    --file="$BACKUP_FILE"

# Compress (if not using custom format)
# gzip "$BACKUP_FILE"

# Keep only last 30 days
find $BACKUP_DIR -name "db_backup_*.sql*" -mtime +30 -delete

# Verify backup
pg_restore --list "$BACKUP_FILE" > /dev/null && echo "Backup verified" || echo "Backup failed"
```

#### WAL Archiving (Continuous Backup)
```sql
-- postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /backups/wal_archive/%f'
```

### 8.2 Restore Procedures

#### Full Database Restore
```bash
#!/bin/bash
# /opt/AInfluencer/scripts/restore-db.sh

BACKUP_FILE=$1  # Path to backup file

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: restore-db.sh <backup_file>"
    exit 1
fi

# Stop application
systemctl stop ainfluencer-backend
systemctl stop ainfluencer-worker

# Drop existing database (CAUTION: Destructive)
dropdb -U ainfluencer_user ainfluencer

# Create new database
createdb -U ainfluencer_user ainfluencer

# Restore from backup
pg_restore -U ainfluencer_user -d ainfluencer --clean --if-exists "$BACKUP_FILE"

# Restart application
systemctl start ainfluencer-backend
systemctl start ainfluencer-worker

echo "Database restored successfully"
```

#### Point-in-Time Recovery (PITR)
```bash
# Restore to specific point in time
pg_basebackup -D /var/lib/postgresql/restore -Ft -z -P
# Then use WAL archives to recover to specific time
```

### 8.3 Backup Verification

```bash
#!/bin/bash
# Verify backup integrity
BACKUP_FILE=$1

# List contents (verifies backup is readable)
pg_restore --list "$BACKUP_FILE" > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ Backup is valid"
    exit 0
else
    echo "❌ Backup is corrupted"
    exit 1
fi
```

---

## 9. Security Considerations

### 9.1 Data Encryption

#### Encrypting Sensitive Fields
```sql
-- Enable pgcrypto extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Encrypt auth_data in platform_accounts
-- Application layer handles encryption/decryption
-- Store encrypted JSONB in auth_data column

-- Example encryption (in application):
-- encrypted_data = pgcrypto.encrypt(data, encryption_key, 'aes')
```

#### Encryption Key Management
- Store encryption keys in environment variables
- Never commit keys to version control
- Rotate keys periodically
- Use different keys for different environments

### 9.2 Access Control

#### Database Roles
```sql
-- Create application user
CREATE USER ainfluencer_app WITH PASSWORD 'secure_password';

-- Grant permissions
GRANT CONNECT ON DATABASE ainfluencer TO ainfluencer_app;
GRANT USAGE ON SCHEMA public TO ainfluencer_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ainfluencer_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ainfluencer_app;

-- Create read-only user for analytics
CREATE USER ainfluencer_readonly WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE ainfluencer TO ainfluencer_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ainfluencer_readonly;
```

### 9.3 SQL Injection Prevention

**Best Practices:**
- Use parameterized queries (SQLAlchemy ORM)
- Never use string formatting for SQL
- Validate all inputs
- Use ORM methods instead of raw SQL

**Example (Safe):**
```python
# ✅ Safe: Parameterized query
character = db.query(Character).filter(Character.id == character_id).first()

# ❌ Unsafe: String formatting
# db.execute(f"SELECT * FROM characters WHERE id = '{character_id}'")
```

### 9.4 Audit Trail

**Logging Critical Operations:**
```python
# Log all character deletions
def delete_character(character_id, user_id):
    character = db.query(Character).filter(Character.id == character_id).first()
    
    # Log before deletion
    log_event(
        level='info',
        component='character_service',
        message=f'Character deleted: {character.name}',
        character_id=character_id,
        metadata={'deleted_by': user_id}
    )
    
    # Soft delete
    character.deleted_at = datetime.utcnow()
    db.commit()
```

---

## 10. Data Models (SQLAlchemy)

### 10.1 Complete Character Model

```python
from sqlalchemy import Column, String, Integer, Boolean, Text, ARRAY, DateTime, CheckConstraint, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
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
    personality = relationship("CharacterPersonality", back_populates="character", uselist=False, cascade="all, delete-orphan")
    appearance = relationship("CharacterAppearance", back_populates="character", uselist=False, cascade="all, delete-orphan")
    content_items = relationship("Content", back_populates="character", cascade="all, delete-orphan")
    platform_accounts = relationship("PlatformAccount", back_populates="character", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="character", cascade="all, delete-orphan")
    automation_rules = relationship("AutomationRule", back_populates="character", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("status IN ('active', 'paused', 'error', 'deleted')", name='status_check'),
        CheckConstraint("LENGTH(name) >= 1 AND LENGTH(name) <= 255", name='name_length_check'),
        CheckConstraint("age IS NULL OR (age >= 0 AND age <= 150)", name='age_range_check'),
    )
    
    def __repr__(self):
        return f"<Character(id={self.id}, name='{self.name}', status='{self.status}')>"
```

### 10.2 Content Model

```python
class Content(Base):
    __tablename__ = 'content'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey('characters.id', ondelete='CASCADE'), nullable=False)
    
    content_type = Column(String(20), nullable=False)
    content_category = Column(String(50))
    is_nsfw = Column(Boolean, default=False)
    
    file_url = Column(Text)
    file_path = Column(Text, nullable=False)
    thumbnail_url = Column(Text)
    thumbnail_path = Column(Text)
    
    file_size = Column(BigInteger)
    width = Column(Integer)
    height = Column(Integer)
    duration = Column(Integer)
    mime_type = Column(String(100))
    
    prompt = Column(Text)
    negative_prompt = Column(Text)
    generation_settings = Column(JSONB)
    generation_time_seconds = Column(Integer)
    seed = Column(Integer)
    
    quality_score = Column(Numeric(3, 2))
    is_approved = Column(Boolean, default=False)
    approval_status = Column(String(20), default='pending')
    rejection_reason = Column(Text)
    
    times_used = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))
    
    tags = Column(ARRAY(String))
    folder_path = Column(Text)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    character = relationship("Character", back_populates="content_items")
    posts = relationship("Post", back_populates="content")
    
    __table_args__ = (
        CheckConstraint("content_type IN ('image', 'video', 'text', 'audio')", name='content_type_check'),
        CheckConstraint("approval_status IN ('pending', 'approved', 'rejected')", name='approval_status_check'),
    )
```

---

## 11. Database Maintenance

### 11.1 Regular Maintenance Tasks

#### Vacuum and Analyze
```sql
-- Vacuum (reclaim space, update statistics)
VACUUM ANALYZE;

-- Vacuum specific table
VACUUM ANALYZE characters;

-- Full vacuum (locks table, more thorough)
VACUUM FULL characters;
```

#### Index Maintenance
```sql
-- Rebuild index
REINDEX INDEX idx_characters_status;

-- Rebuild all indexes
REINDEX DATABASE ainfluencer;
```

#### Statistics Update
```sql
-- Update query planner statistics
ANALYZE;

-- Analyze specific table
ANALYZE characters;
```

### 11.2 Monitoring Queries

#### Check Table Sizes
```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### Check Slow Queries
```sql
-- Enable query logging in postgresql.conf
-- log_min_duration_statement = 1000  -- Log queries > 1 second

-- View slow queries from logs
SELECT * FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

#### Check Index Usage
```sql
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan ASC;  -- Unused indexes first
```

---

## 12. Next Steps

### Immediate Actions
1. ✅ Review and approve this schema
2. ⏳ Set up PostgreSQL database
3. ⏳ Initialize Alembic for migrations
4. ⏳ Create SQLAlchemy models based on this schema
5. ⏳ Run initial migration
6. ⏳ Seed test data

### Implementation Steps
1. Install PostgreSQL 15+
2. Create database and user
3. Enable required extensions
4. Run Alembic migrations
5. Verify schema creation
6. Test relationships and constraints

---

**Document Status**: ✅ Complete - Production Ready

**Related Documents:**
- [05-API-DESIGN.md](./05-API-DESIGN.md) - API uses these models
- [20-DEPLOYMENT-DEVOPS.md](./20-DEPLOYMENT-DEVOPS.md) - Database setup
- [23-SCALING-OPTIMIZATION.md](./23-SCALING-OPTIMIZATION.md) - Database scaling
- [24-SECURITY-HARDENING.md](./24-SECURITY-HARDENING.md) - Database security
