# API Design
## Ultra-Realistic AI Media Generator Platform

**Version:** 1.0  
**Date:** January 2025  
**Status:** Active Development  
**Document Owner:** CTO

---

## Overview

This document describes the complete REST API and WebSocket API for the Ultra-Realistic AI Media Generator platform. All endpoints follow RESTful principles and use JSON for request/response bodies.

---

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `http://localhost:8000` (self-hosted)

---

## Authentication

Currently, the API is local-only (no authentication required). Future versions may support:
- API key authentication
- JWT tokens
- OAuth2

---

## Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { ... }
  }
}
```

### Status Codes
- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid request
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service unavailable

---

## Endpoints

### Health Check

#### GET /api/health
Check API health status.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2025-01-01T00:00:00Z",
    "version": "1.0.0"
  }
}
```

---

### Image Generation

#### POST /api/generate/image
Generate an ultra-realistic image.

**Request Body:**
```json
{
  "prompt": "A beautiful woman, professional photography, 8k uhd",
  "negative_prompt": "low quality, worst quality, blurry",
  "character_id": "char_123",
  "settings": {
    "width": 1024,
    "height": 1024,
    "steps": 30,
    "cfg_scale": 7.0,
    "sampler": "dpmpp_2m",
    "seed": -1,
    "model": "realisticVisionV51_v51VAE.safetensors"
  },
  "face_consistency": {
    "enabled": true,
    "method": "ip_adapter",
    "strength": 0.8
  },
  "post_processing": {
    "upscale": true,
    "upscale_factor": 2,
    "face_restoration": true,
    "color_correction": true,
    "remove_metadata": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "job_123",
    "status": "pending",
    "estimated_time": 120
  }
}
```

#### GET /api/generate/image/{job_id}
Get image generation status.

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "job_123",
    "status": "processing",
    "progress": 0.65,
    "media_id": "media_123",
    "error": null
  }
}
```

---

### Video Generation

#### POST /api/generate/video
Generate an ultra-realistic video.

**Request Body:**
```json
{
  "prompt": "A beautiful woman walking, professional videography",
  "negative_prompt": "low quality, worst quality, blurry",
  "character_id": "char_123",
  "image_id": "media_123",
  "settings": {
    "length": 30,
    "fps": 24,
    "width": 1920,
    "height": 1080,
    "motion_strength": 0.8,
    "method": "animatediff"
  },
  "face_consistency": {
    "enabled": true,
    "method": "ip_adapter",
    "strength": 0.8
  },
  "post_processing": {
    "upscale": true,
    "upscale_factor": 2,
    "frame_interpolation": true,
    "color_correction": true,
    "remove_metadata": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "job_456",
    "status": "pending",
    "estimated_time": 300
  }
}
```

#### GET /api/generate/video/{job_id}
Get video generation status.

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "job_456",
    "status": "processing",
    "progress": 0.45,
    "current_frame": 180,
    "total_frames": 720,
    "media_id": "media_456",
    "error": null
  }
}
```

---

### Batch Generation

#### POST /api/generate/batch
Start batch generation.

**Request Body:**
```json
{
  "type": "image",
  "count": 10,
  "prompt_template": "A beautiful woman, {variation}",
  "variations": ["professional photography", "casual photography", "studio photography"],
  "character_id": "char_123",
  "settings": {
    "width": 1024,
    "height": 1024,
    "steps": 30
  },
  "priority": "normal"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "batch_job_id": "batch_123",
    "status": "pending",
    "total_count": 10,
    "estimated_time": 1200
  }
}
```

#### GET /api/generate/batch/{batch_job_id}
Get batch generation status.

**Response:**
```json
{
  "success": true,
  "data": {
    "batch_job_id": "batch_123",
    "status": "processing",
    "total_count": 10,
    "completed_count": 5,
    "failed_count": 0,
    "progress": 0.5,
    "items": [
      {
        "id": "item_1",
        "status": "completed",
        "media_id": "media_1"
      },
      {
        "id": "item_2",
        "status": "processing",
        "progress": 0.8
      }
    ]
  }
}
```

---

### Media Management

#### GET /api/media
List media items.

**Query Parameters:**
- `type`: Filter by type (`image` or `video`)
- `source`: Filter by source (`ai_generated` or `personal`)
- `character_id`: Filter by character
- `tags`: Filter by tags (comma-separated)
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 50)
- `sort`: Sort field (default: `created_at`)
- `order`: Sort order (`asc` or `desc`, default: `desc`)

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "media_123",
        "type": "image",
        "source": "ai_generated",
        "file_name": "generated_image.png",
        "file_size": 2048000,
        "width": 2048,
        "height": 2048,
        "thumbnail_path": "/thumbnails/media_123.jpg",
        "character_id": "char_123",
        "character_name": "Elizabeth",
        "tags": ["portrait", "professional"],
        "created_at": "2025-01-01T00:00:00Z",
        "quality_score": 0.95
      }
    ],
    "total": 100,
    "page": 1,
    "limit": 50,
    "total_pages": 2
  }
}
```

#### GET /api/media/{media_id}
Get a specific media item.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "media_123",
    "type": "image",
    "source": "ai_generated",
    "file_path": "/media/media_123.png",
    "file_name": "generated_image.png",
    "file_size": 2048000,
    "width": 2048,
    "height": 2048,
    "mime_type": "image/png",
    "thumbnail_path": "/thumbnails/media_123.jpg",
    "character_id": "char_123",
    "character_name": "Elizabeth",
    "tags": ["portrait", "professional"],
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z",
    "metadata": {
      "generation_job_id": "job_123",
      "prompt": "A beautiful woman...",
      "settings": { ... }
    },
    "quality_score": {
      "overall": 0.95,
      "realism": 0.98,
      "artifact": 0.02,
      "face_quality": 0.96
    }
  }
}
```

#### POST /api/media/upload
Upload personal media.

**Request:** Multipart form data
- `file`: Media file (image or video)
- `character_id`: Optional character ID
- `tags`: Optional tags (comma-separated)

**Response:**
```json
{
  "success": true,
  "data": {
    "media_id": "media_456",
    "file_name": "personal_photo.jpg",
    "file_size": 1024000,
    "width": 1920,
    "height": 1080,
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

#### DELETE /api/media/{media_id}
Delete a media item.

**Response:**
```json
{
  "success": true,
  "data": {
    "media_id": "media_123",
    "deleted": true
  }
}
```

#### POST /api/media/{media_id}/tags
Update media tags.

**Request Body:**
```json
{
  "tags": ["portrait", "professional", "new_tag"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "media_id": "media_123",
    "tags": ["portrait", "professional", "new_tag"]
  }
}
```

#### GET /api/media/{media_id}/download
Download media file.

**Response:** File download

---

### Character Management

#### GET /api/characters
List all characters.

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 50)

**Response:**
```json
{
  "success": true,
  "data": {
    "characters": [
      {
        "id": "char_123",
        "name": "Elizabeth",
        "description": "Professional model character",
        "face_reference_count": 3,
        "media_count": 150,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
      }
    ],
    "total": 10,
    "page": 1,
    "limit": 50
  }
}
```

#### GET /api/characters/{character_id}
Get a specific character.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "char_123",
    "name": "Elizabeth",
    "description": "Professional model character",
    "face_references": [
      {
        "id": "face_1",
        "file_name": "face_ref_1.jpg",
        "width": 512,
        "height": 512,
        "created_at": "2025-01-01T00:00:00Z"
      }
    ],
    "settings": {
      "default_model": "realisticVisionV51_v51VAE.safetensors",
      "default_steps": 30,
      "default_cfg_scale": 7.0
    },
    "statistics": {
      "total_generations": 150,
      "total_images": 120,
      "total_videos": 30,
      "average_quality": 0.94
    },
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
}
```

#### POST /api/characters
Create a new character.

**Request Body:**
```json
{
  "name": "Elizabeth",
  "description": "Professional model character",
  "settings": {
    "default_model": "realisticVisionV51_v51VAE.safetensors",
    "default_steps": 30,
    "default_cfg_scale": 7.0
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "character_id": "char_123",
    "name": "Elizabeth",
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

#### PUT /api/characters/{character_id}
Update a character.

**Request Body:**
```json
{
  "name": "Elizabeth Updated",
  "description": "Updated description",
  "settings": {
    "default_model": "realisticVisionV51_v51VAE.safetensors"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "character_id": "char_123",
    "updated_at": "2025-01-01T00:00:00Z"
  }
}
```

#### DELETE /api/characters/{character_id}
Delete a character.

**Response:**
```json
{
  "success": true,
  "data": {
    "character_id": "char_123",
    "deleted": true
  }
}
```

#### POST /api/characters/{character_id}/face-references
Upload a face reference image.

**Request:** Multipart form data
- `file`: Face reference image file

**Response:**
```json
{
  "success": true,
  "data": {
    "face_reference_id": "face_1",
    "file_name": "face_ref_1.jpg",
    "width": 512,
    "height": 512,
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

#### DELETE /api/characters/{character_id}/face-references/{face_reference_id}
Delete a face reference.

**Response:**
```json
{
  "success": true,
  "data": {
    "face_reference_id": "face_1",
    "deleted": true
  }
}
```

---

### Generation History

#### GET /api/generate/history
Get generation history.

**Query Parameters:**
- `type`: Filter by type (`image` or `video`)
- `character_id`: Filter by character
- `status`: Filter by status
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 50)

**Response:**
```json
{
  "success": true,
  "data": {
    "jobs": [
      {
        "id": "job_123",
        "type": "image",
        "status": "completed",
        "prompt": "A beautiful woman...",
        "character_id": "char_123",
        "character_name": "Elizabeth",
        "result_media_id": "media_123",
        "created_at": "2025-01-01T00:00:00Z",
        "completed_at": "2025-01-01T00:02:00Z",
        "duration": 120
      }
    ],
    "total": 100,
    "page": 1,
    "limit": 50
  }
}
```

---

### Settings

#### GET /api/settings
Get all settings.

**Query Parameters:**
- `category`: Filter by category

**Response:**
```json
{
  "success": true,
  "data": {
    "settings": [
      {
        "id": "setting_1",
        "category": "generation",
        "key": "default_model",
        "value": "realisticVisionV51_v51VAE.safetensors",
        "description": "Default generation model"
      }
    ]
  }
}
```

#### GET /api/settings/{category}/{key}
Get a specific setting.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "setting_1",
    "category": "generation",
    "key": "default_model",
    "value": "realisticVisionV51_v51VAE.safetensors",
    "description": "Default generation model"
  }
}
```

#### PUT /api/settings/{category}/{key}
Update a setting.

**Request Body:**
```json
{
  "value": "new_model.safetensors"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "setting_1",
    "updated_at": "2025-01-01T00:00:00Z"
  }
}
```

---

### System Information

#### GET /api/system/stats
Get system statistics.

**Response:**
```json
{
  "success": true,
  "data": {
    "comfyui": {
      "connected": true,
      "version": "1.0.0"
    },
    "gpu": {
      "available": true,
      "name": "NVIDIA GeForce RTX 4090",
      "memory_total": 24576,
      "memory_used": 8192,
      "memory_free": 16384
    },
    "storage": {
      "total": 1000000000,
      "used": 500000000,
      "free": 500000000
    },
    "queue": {
      "pending": 5,
      "processing": 2,
      "completed_today": 150
    }
  }
}
```

---

## WebSocket API

### Connection

**URL:** `ws://localhost:8000/ws`

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

### Messages

#### Subscribe to Job Updates

**Send:**
```json
{
  "type": "subscribe",
  "job_id": "job_123"
}
```

**Receive:**
```json
{
  "type": "job_update",
  "job_id": "job_123",
  "status": "processing",
  "progress": 0.65,
  "message": "Generating image..."
}
```

#### Subscribe to Batch Updates

**Send:**
```json
{
  "type": "subscribe_batch",
  "batch_job_id": "batch_123"
}
```

**Receive:**
```json
{
  "type": "batch_update",
  "batch_job_id": "batch_123",
  "status": "processing",
  "completed_count": 5,
  "total_count": 10,
  "progress": 0.5
}
```

#### Unsubscribe

**Send:**
```json
{
  "type": "unsubscribe",
  "job_id": "job_123"
}
```

---

## Rate Limiting

Currently no rate limiting (local-only). Future versions may implement:
- Per-endpoint rate limits
- Per-user rate limits
- Queue-based throttling

---

## Error Codes

- `VALIDATION_ERROR`: Invalid request data
- `NOT_FOUND`: Resource not found
- `GENERATION_ERROR`: Generation failed
- `SERVICE_UNAVAILABLE`: Service unavailable
- `STORAGE_ERROR`: Storage operation failed
- `DATABASE_ERROR`: Database operation failed

---

**Last Updated:** January 2025  
**Next Review:** Weekly  
**Status:** Active Development
