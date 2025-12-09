# Metadata Column Fix - Complete ✅

## Problem
SQLAlchemy error: `Attribute name 'metadata' is reserved when using the Declarative API`

## Solution
Renamed all `metadata` columns to `meta_data` in all database models to avoid the reserved name conflict.

## Changes Made

### 1. Models Updated (`backend/models.py`)
- ✅ `Character.metadata` → `Character.meta_data`
- ✅ `FaceReference.metadata` → `FaceReference.meta_data`
- ✅ `MediaItem.metadata` → `MediaItem.meta_data`
- ✅ `GenerationJob.metadata` → `GenerationJob.meta_data`
- ✅ `BatchJob.metadata` → `BatchJob.meta_data`
- ✅ `QualityScore.metadata` → `QualityScore.meta_data`
- ✅ `ScheduledPost.metadata` → `ScheduledPost.meta_data`
- ✅ `PlatformAccount.metadata` → `PlatformAccount.meta_data`
- ✅ `PlatformPost.metadata` → `PlatformPost.meta_data`

### 2. Service Files Updated
All service files that reference `.metadata` have been updated to use `.meta_data`:
- ✅ `backend/services/generation_service.py`
- ✅ `backend/services/character_service.py`
- ✅ `backend/services/media_service.py`
- ✅ `backend/services/media_library_service.py`
- ✅ `backend/services/automation_service.py`
- ✅ `backend/services/platform_integration_service.py`
- ✅ `backend/services/enhanced_character_service.py`
- ✅ `backend/services/batch_generation_service.py`
- ✅ `backend/services/automation/content_generation_pipeline.py`
- ✅ `backend/services/automation/auto_poster.py`

### 3. API Endpoints Updated (`backend/main.py`)
- ✅ All API responses that return `metadata` now use `meta_data` internally but still return as `metadata` in JSON for API compatibility

### 4. Migration Script Created
- ✅ `backend/migrate_metadata_column.py` - Automatically migrates existing databases

## Database Migration

If you have an existing database, run:
```powershell
cd backend
python migrate_metadata_column.py
```

This will rename the `metadata` column to `meta_data` in all tables.

For new databases, the migration happens automatically when tables are created.

## API Compatibility

**Important**: The API still returns `metadata` in JSON responses for backward compatibility. Internally, the database column is `meta_data`, but the API layer converts it back to `metadata` in responses.

## Verification

All instances of `metadata = Column` have been removed from models.
All service references to `.metadata` have been updated to `.meta_data`.

## Status

✅ **FIXED** - Backend should now start without SQLAlchemy errors!

The server should restart successfully now. Try running:
```powershell
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
