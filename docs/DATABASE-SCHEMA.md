# Database Schema
## Ultra-Realistic AI Media Generator Platform

**Version:** 1.0  
**Date:** January 2025  
**Status:** Active Development  
**Document Owner:** CTO

---

## Overview

This document describes the complete database schema for the Ultra-Realistic AI Media Generator platform. The schema is designed to support all features outlined in the PRD.

---

## Database Choice

- **Development**: SQLite (simple, file-based)
- **Production**: PostgreSQL (scalable, feature-rich)

Both use the same schema structure, with minor differences in data types.

---

## Schema Design Principles

1. **Normalization**: Properly normalized to avoid redundancy
2. **Extensibility**: Easy to add new features
3. **Performance**: Indexed for fast queries
4. **Data Integrity**: Foreign keys and constraints
5. **Audit Trail**: Timestamps and soft deletes

---

## Tables

### 1. characters

Stores character definitions and metadata.

```sql
CREATE TABLE characters (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    settings JSONB,  -- Character-specific settings
    metadata JSONB   -- Additional metadata
);

CREATE INDEX idx_characters_name ON characters(name);
CREATE INDEX idx_characters_created_at ON characters(created_at);
CREATE INDEX idx_characters_deleted_at ON characters(deleted_at);
```

**Fields**:
- `id`: Unique character identifier
- `name`: Character name
- `description`: Character description
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `deleted_at`: Soft delete timestamp
- `settings`: Character-specific generation settings (JSON)
- `metadata`: Additional metadata (JSON)

---

### 2. face_references

Stores face reference images for characters.

```sql
CREATE TABLE face_references (
    id TEXT PRIMARY KEY,
    character_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    width INTEGER,
    height INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    metadata JSONB,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE INDEX idx_face_references_character_id ON face_references(character_id);
CREATE INDEX idx_face_references_created_at ON face_references(created_at);
```

**Fields**:
- `id`: Unique face reference identifier
- `character_id`: Reference to character
- `file_path`: Path to face reference image
- `file_name`: Original file name
- `file_size`: File size in bytes
- `mime_type`: MIME type (image/png, image/jpeg)
- `width`: Image width in pixels
- `height`: Image height in pixels
- `created_at`: Creation timestamp
- `deleted_at`: Soft delete timestamp
- `metadata`: Additional metadata (JSON)

---

### 3. media_items

Stores all media items (AI-generated and personal).

```sql
CREATE TABLE media_items (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,  -- 'image' or 'video'
    source TEXT NOT NULL,  -- 'ai_generated' or 'personal'
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    width INTEGER,
    height INTEGER,
    duration INTEGER,  -- For videos (seconds)
    thumbnail_path TEXT,
    character_id TEXT,
    generation_job_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    metadata JSONB,
    tags TEXT[],  -- Array of tags
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE SET NULL
);

CREATE INDEX idx_media_items_type ON media_items(type);
CREATE INDEX idx_media_items_source ON media_items(source);
CREATE INDEX idx_media_items_character_id ON media_items(character_id);
CREATE INDEX idx_media_items_generation_job_id ON media_items(generation_job_id);
CREATE INDEX idx_media_items_created_at ON media_items(created_at);
CREATE INDEX idx_media_items_tags ON media_items USING GIN(tags);
```

**Fields**:
- `id`: Unique media item identifier
- `type`: Media type ('image' or 'video')
- `source`: Source type ('ai_generated' or 'personal')
- `file_path`: Path to media file
- `file_name`: Original file name
- `file_size`: File size in bytes
- `mime_type`: MIME type
- `width`: Width in pixels
- `height`: Height in pixels
- `duration`: Duration in seconds (for videos)
- `thumbnail_path`: Path to thumbnail
- `character_id`: Associated character (if any)
- `generation_job_id`: Generation job that created this (if AI-generated)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `deleted_at`: Soft delete timestamp
- `metadata`: Additional metadata (JSON)
- `tags`: Array of tags

---

### 4. generation_jobs

Tracks generation jobs (images and videos).

```sql
CREATE TABLE generation_jobs (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,  -- 'image' or 'video'
    status TEXT NOT NULL,  -- 'pending', 'processing', 'completed', 'failed'
    character_id TEXT,
    prompt TEXT NOT NULL,
    negative_prompt TEXT,
    settings JSONB NOT NULL,  -- Generation settings
    workflow_config JSONB,  -- Workflow configuration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    failed_at TIMESTAMP,
    error_message TEXT,
    progress REAL DEFAULT 0.0,  -- 0.0 to 1.0
    comfyui_prompt_id TEXT,
    metadata JSONB,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE SET NULL
);

CREATE INDEX idx_generation_jobs_status ON generation_jobs(status);
CREATE INDEX idx_generation_jobs_type ON generation_jobs(type);
CREATE INDEX idx_generation_jobs_character_id ON generation_jobs(character_id);
CREATE INDEX idx_generation_jobs_created_at ON generation_jobs(created_at);
CREATE INDEX idx_generation_jobs_comfyui_prompt_id ON generation_jobs(comfyui_prompt_id);
```

**Fields**:
- `id`: Unique job identifier
- `type`: Job type ('image' or 'video')
- `status`: Job status ('pending', 'processing', 'completed', 'failed')
- `character_id`: Associated character (if any)
- `prompt`: Generation prompt
- `negative_prompt`: Negative prompt
- `settings`: Generation settings (JSON)
- `workflow_config`: Workflow configuration (JSON)
- `created_at`: Creation timestamp
- `started_at`: Start timestamp
- `completed_at`: Completion timestamp
- `failed_at`: Failure timestamp
- `error_message`: Error message (if failed)
- `progress`: Progress (0.0 to 1.0)
- `comfyui_prompt_id`: ComfyUI prompt ID
- `metadata`: Additional metadata (JSON)

---

### 5. generation_history

Stores generation history for analytics and replay.

```sql
CREATE TABLE generation_history (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    user_action TEXT,  -- 'generate', 'regenerate', 'variation'
    prompt TEXT NOT NULL,
    negative_prompt TEXT,
    settings JSONB,
    result_media_id TEXT,
    quality_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES generation_jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (result_media_id) REFERENCES media_items(id) ON DELETE SET NULL
);

CREATE INDEX idx_generation_history_job_id ON generation_history(job_id);
CREATE INDEX idx_generation_history_created_at ON generation_history(created_at);
CREATE INDEX idx_generation_history_result_media_id ON generation_history(result_media_id);
```

**Fields**:
- `id`: Unique history entry identifier
- `job_id`: Reference to generation job
- `user_action`: User action type
- `prompt`: Prompt used
- `negative_prompt`: Negative prompt used
- `settings`: Settings used
- `result_media_id`: Resulting media item
- `quality_score`: Quality score (if available)
- `created_at`: Creation timestamp

---

### 6. batch_jobs

Tracks batch generation jobs.

```sql
CREATE TABLE batch_jobs (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,  -- 'image' or 'video'
    status TEXT NOT NULL,  -- 'pending', 'processing', 'completed', 'failed'
    total_count INTEGER NOT NULL,
    completed_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    character_id TEXT,
    prompt_template TEXT,
    settings_template JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    metadata JSONB,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE SET NULL
);

CREATE INDEX idx_batch_jobs_status ON batch_jobs(status);
CREATE INDEX idx_batch_jobs_type ON batch_jobs(type);
CREATE INDEX idx_batch_jobs_character_id ON batch_jobs(character_id);
CREATE INDEX idx_batch_jobs_created_at ON batch_jobs(created_at);
```

**Fields**:
- `id`: Unique batch job identifier
- `type`: Batch type ('image' or 'video')
- `status`: Batch status
- `total_count`: Total items to generate
- `completed_count`: Completed items count
- `failed_count`: Failed items count
- `character_id`: Associated character
- `prompt_template`: Prompt template
- `settings_template`: Settings template (JSON)
- `created_at`: Creation timestamp
- `started_at`: Start timestamp
- `completed_at`: Completion timestamp
- `metadata`: Additional metadata (JSON)

---

### 7. batch_job_items

Individual items in a batch job.

```sql
CREATE TABLE batch_job_items (
    id TEXT PRIMARY KEY,
    batch_job_id TEXT NOT NULL,
    generation_job_id TEXT,
    index INTEGER NOT NULL,
    prompt TEXT NOT NULL,
    negative_prompt TEXT,
    settings JSONB,
    status TEXT NOT NULL,  -- 'pending', 'processing', 'completed', 'failed'
    result_media_id TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_job_id) REFERENCES batch_jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (generation_job_id) REFERENCES generation_jobs(id) ON DELETE SET NULL,
    FOREIGN KEY (result_media_id) REFERENCES media_items(id) ON DELETE SET NULL
);

CREATE INDEX idx_batch_job_items_batch_job_id ON batch_job_items(batch_job_id);
CREATE INDEX idx_batch_job_items_generation_job_id ON batch_job_items(generation_job_id);
CREATE INDEX idx_batch_job_items_status ON batch_job_items(status);
```

**Fields**:
- `id`: Unique batch item identifier
- `batch_job_id`: Reference to batch job
- `generation_job_id`: Reference to generation job
- `index`: Item index in batch
- `prompt`: Prompt for this item
- `negative_prompt`: Negative prompt
- `settings`: Settings for this item (JSON)
- `status`: Item status
- `result_media_id`: Resulting media item
- `error_message`: Error message (if failed)
- `created_at`: Creation timestamp

---

### 8. quality_scores

Stores quality scores for media items.

```sql
CREATE TABLE quality_scores (
    id TEXT PRIMARY KEY,
    media_id TEXT NOT NULL,
    overall_score REAL NOT NULL,  -- 0.0 to 1.0
    realism_score REAL,
    artifact_score REAL,  -- Lower is better (0.0 = no artifacts)
    face_quality_score REAL,
    face_consistency_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    FOREIGN KEY (media_id) REFERENCES media_items(id) ON DELETE CASCADE
);

CREATE INDEX idx_quality_scores_media_id ON quality_scores(media_id);
CREATE INDEX idx_quality_scores_overall_score ON quality_scores(overall_score);
CREATE INDEX idx_quality_scores_created_at ON quality_scores(created_at);
```

**Fields**:
- `id`: Unique quality score identifier
- `media_id`: Reference to media item
- `overall_score`: Overall quality score (0.0 to 1.0)
- `realism_score`: Realism score
- `artifact_score`: Artifact score (lower is better)
- `face_quality_score`: Face quality score
- `face_consistency_score`: Face consistency score
- `created_at`: Creation timestamp
- `metadata`: Additional metadata (JSON)

---

### 9. settings

User and system settings.

```sql
CREATE TABLE settings (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,  -- 'user', 'system', 'generation', 'ui'
    key TEXT NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, key)
);

CREATE INDEX idx_settings_category ON settings(category);
CREATE INDEX idx_settings_category_key ON settings(category, key);
```

**Fields**:
- `id`: Unique setting identifier
- `category`: Setting category
- `key`: Setting key
- `value`: Setting value (JSON)
- `description`: Setting description
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

---

### 10. workflows

Stores workflow templates and configurations.

```sql
CREATE TABLE workflows (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    type TEXT NOT NULL,  -- 'image' or 'video'
    workflow_config JSONB NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_workflows_type ON workflows(type);
CREATE INDEX idx_workflows_is_default ON workflows(is_default);
CREATE INDEX idx_workflows_created_at ON workflows(created_at);
```

**Fields**:
- `id`: Unique workflow identifier
- `name`: Workflow name
- `description`: Workflow description
- `type`: Workflow type ('image' or 'video')
- `workflow_config`: Workflow configuration (JSON)
- `is_default`: Is default workflow
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `deleted_at`: Soft delete timestamp
- `metadata`: Additional metadata (JSON)

---

## Relationships

```
characters
  ├── face_references (1:N)
  ├── media_items (1:N)
  └── generation_jobs (1:N)

generation_jobs
  ├── generation_history (1:N)
  ├── batch_job_items (1:1)
  └── media_items (1:N)

batch_jobs
  └── batch_job_items (1:N)

media_items
  ├── quality_scores (1:N)
  └── generation_history (1:N)
```

---

## Data Types

### SQLite
- `TEXT`: String
- `INTEGER`: Integer
- `REAL`: Float
- `TIMESTAMP`: Text (ISO 8601)
- `JSONB`: Text (JSON stored as text)

### PostgreSQL
- `TEXT`: Text
- `INTEGER`: Integer
- `REAL`: Double precision
- `TIMESTAMP`: Timestamp
- `JSONB`: JSONB (native JSON support)
- `TEXT[]`: Array of text

---

## Indexes

All foreign keys are indexed for performance. Additional indexes:
- Timestamp fields for sorting
- Status fields for filtering
- Search fields (name, tags)
- JSONB fields (GIN indexes in PostgreSQL)

---

## Migrations

Use Alembic for database migrations:
- `alembic init alembic`
- `alembic revision --autogenerate -m "Initial schema"`
- `alembic upgrade head`

---

## Sample Queries

### Get all characters with face references
```sql
SELECT c.*, COUNT(fr.id) as face_reference_count
FROM characters c
LEFT JOIN face_references fr ON c.id = fr.character_id
WHERE c.deleted_at IS NULL
GROUP BY c.id;
```

### Get recent media items
```sql
SELECT m.*, c.name as character_name
FROM media_items m
LEFT JOIN characters c ON m.character_id = c.id
WHERE m.deleted_at IS NULL
ORDER BY m.created_at DESC
LIMIT 50;
```

### Get generation statistics
```sql
SELECT 
    COUNT(*) as total_jobs,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
    AVG(progress) as avg_progress
FROM generation_jobs
WHERE created_at >= NOW() - INTERVAL '7 days';
```

---

**Last Updated:** January 2025  
**Next Review:** Weekly  
**Status:** Active Development
