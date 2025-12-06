# API Design & Endpoints

## 📋 Document Metadata

### Purpose
Complete RESTful API specification with all endpoints, request/response formats, authentication, and WebSocket support. This defines the contract between frontend and backend.

### Reading Order
**Read After:** [09-DATABASE-SCHEMA.md](./09-DATABASE-SCHEMA.md), [02-TECHNICAL-ARCHITECTURE.md](./02-TECHNICAL-ARCHITECTURE.md)  
**Read Before:** Implementing backend API endpoints, frontend API integration

### Related Documents
**Prerequisites:**
- [09-DATABASE-SCHEMA.md](./09-DATABASE-SCHEMA.md) - API uses database models
- [02-TECHNICAL-ARCHITECTURE.md](./02-TECHNICAL-ARCHITECTURE.md) - API framework selection

**Used By:**
- Frontend implementation - All API calls follow this spec
- Backend implementation - Endpoints must match this specification
- [08-UI-UX-DESIGN-SYSTEM.md](./08-UI-UX-DESIGN-SYSTEM.md) - UI calls these APIs
- [14-TESTING-STRATEGY.md](./14-TESTING-STRATEGY.md) - API tests use this spec

**Related:**
- [05-AUTOMATION-STRATEGY.md](./05-AUTOMATION-STRATEGY.md) - Platform integrations may need API endpoints
- [16-ENHANCED-FEATURES.md](./16-ENHANCED-FEATURES.md) - New features need API endpoints

---

## API Architecture

### Framework
**FastAPI** (Python 3.11+)
- **Why**: Async support, automatic OpenAPI docs, type safety, high performance
- **Documentation**: Swagger UI at `/docs`, ReDoc at `/redoc`
- **Versioning**: `/api/v1/` prefix

### Authentication
- **JWT Tokens**: For user authentication (if multi-user)
- **API Keys**: For service-to-service communication
- **Rate Limiting**: Per endpoint, configurable

### Response Format
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Error Format
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { ... }
  },
  "timestamp": "2025-01-15T10:30:00Z"
}
```

---

## API Endpoints

### 1. Character Management

#### `GET /api/v1/characters`
Get list of all characters

**Query Parameters:**
- `status` (optional): Filter by status (active, paused, error)
- `limit` (optional, default: 20): Number of results
- `offset` (optional, default: 0): Pagination offset
- `search` (optional): Search by name

**Response:**
```json
{
  "success": true,
  "data": {
    "characters": [
      {
        "id": "uuid",
        "name": "Character Name",
        "bio": "Bio text",
        "status": "active",
        "profile_image_url": "https://...",
        "created_at": "2025-01-15T10:30:00Z"
      }
    ],
    "total": 10,
    "limit": 20,
    "offset": 0
  }
}
```

#### `GET /api/v1/characters/{character_id}`
Get detailed character information

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "Character Name",
    "bio": "Bio text",
    "age": 25,
    "location": "New York",
    "timezone": "America/New_York",
    "interests": ["fitness", "travel"],
    "profile_image_url": "https://...",
    "status": "active",
    "personality": {
      "extroversion": 0.7,
      "creativity": 0.8,
      "communication_style": "casual"
    },
    "appearance": {
      "hair_color": "brown",
      "eye_color": "blue",
      "face_reference_image_url": "https://..."
    },
    "platform_accounts": [...],
    "stats": {
      "total_posts": 150,
      "total_followers": 5000,
      "total_engagement": 25000
    },
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

#### `POST /api/v1/characters`
Create a new character

**Request Body:**
```json
{
  "name": "Character Name",
  "bio": "Bio text",
  "age": 25,
  "location": "New York",
  "timezone": "America/New_York",
  "interests": ["fitness", "travel"],
  "profile_image": "base64_encoded_image_or_url",
  "personality": {
    "extroversion": 0.7,
    "creativity": 0.8,
    "communication_style": "casual",
    "preferred_topics": ["fitness", "lifestyle"]
  },
  "appearance": {
    "face_reference_image": "base64_encoded_image_or_url",
    "hair_color": "brown",
    "eye_color": "blue",
    "style_preferences": ["casual", "sporty"]
  },
  "platforms": ["instagram", "twitter"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "Character Name",
    "status": "active",
    "created_at": "2025-01-15T10:30:00Z"
  },
  "message": "Character created successfully"
}
```

#### `PUT /api/v1/characters/{character_id}`
Update character information

**Request Body:** (Same as POST, all fields optional)

#### `DELETE /api/v1/characters/{character_id}`
Delete (soft delete) a character

**Response:**
```json
{
  "success": true,
  "message": "Character deleted successfully"
}
```

#### `POST /api/v1/characters/{character_id}/pause`
Pause character automation

#### `POST /api/v1/characters/{character_id}/resume`
Resume character automation

---

### 2. Content Generation

#### `POST /api/v1/content/generate`
Generate content (image, video, or text)

**Request Body:**
```json
{
  "character_id": "uuid",
  "content_type": "image", // image, video, text
  "prompt": "A beautiful sunset on the beach",
  "negative_prompt": "blurry, low quality",
  "settings": {
    "steps": 30,
    "cfg_scale": 7.5,
    "width": 1024,
    "height": 1024,
    "seed": null // Optional, for reproducibility
  },
  "category": "post", // post, story, reel, etc.
  "is_nsfw": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "generation_id": "uuid",
    "status": "processing",
    "estimated_completion": "2025-01-15T10:35:00Z"
  },
  "message": "Content generation started"
}
```

#### `GET /api/v1/content/generations/{generation_id}`
Get generation status and results

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "completed", // pending, processing, completed, failed
    "character_id": "uuid",
    "content_type": "image",
    "prompt": "A beautiful sunset...",
    "generated_content_ids": ["uuid1", "uuid2"],
    "success_count": 2,
    "failure_count": 0,
    "started_at": "2025-01-15T10:30:00Z",
    "completed_at": "2025-01-15T10:32:00Z",
    "duration_seconds": 120,
    "error_message": null
  }
}
```

#### `GET /api/v1/content`
Get content library

**Query Parameters:**
- `character_id` (optional): Filter by character
- `content_type` (optional): Filter by type (image, video, text)
- `is_approved` (optional): Filter by approval status
- `is_nsfw` (optional): Filter NSFW content
- `limit`, `offset`: Pagination

**Response:**
```json
{
  "success": true,
  "data": {
    "content": [
      {
        "id": "uuid",
        "character_id": "uuid",
        "character_name": "Character Name",
        "content_type": "image",
        "content_category": "post",
        "file_url": "https://...",
        "thumbnail_url": "https://...",
        "prompt": "A beautiful sunset...",
        "quality_score": 0.85,
        "is_approved": true,
        "times_used": 3,
        "created_at": "2025-01-15T10:30:00Z"
      }
    ],
    "total": 100,
    "limit": 20,
    "offset": 0
  }
}
```

#### `GET /api/v1/content/{content_id}`
Get content details

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "character_id": "uuid",
    "content_type": "image",
    "file_url": "https://...",
    "file_path": "/storage/...",
    "width": 1024,
    "height": 1024,
    "file_size": 2048000,
    "prompt": "A beautiful sunset...",
    "generation_settings": {
      "model": "realistic-vision-v6",
      "steps": 30,
      "cfg_scale": 7.5
    },
    "quality_score": 0.85,
    "is_approved": true,
    "times_used": 3,
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

#### `POST /api/v1/content/{content_id}/approve`
Approve content for use

#### `POST /api/v1/content/{content_id}/reject`
Reject content (with reason)

**Request Body:**
```json
{
  "reason": "Quality too low"
}
```

#### `DELETE /api/v1/content/{content_id}`
Delete content

---

### 3. Platform Integration

#### `GET /api/v1/platforms/accounts`
Get all platform accounts

**Query Parameters:**
- `character_id` (optional): Filter by character
- `platform` (optional): Filter by platform
- `is_connected` (optional): Filter by connection status

**Response:**
```json
{
  "success": true,
  "data": {
    "accounts": [
      {
        "id": "uuid",
        "character_id": "uuid",
        "character_name": "Character Name",
        "platform": "instagram",
        "account_username": "username",
        "account_url": "https://instagram.com/username",
        "is_connected": true,
        "connection_status": "connected",
        "follower_count": 5000,
        "last_synced_at": "2025-01-15T10:00:00Z"
      }
    ]
  }
}
```

#### `POST /api/v1/platforms/{platform}/connect`
Connect a platform account

**Request Body:**
```json
{
  "character_id": "uuid",
  "auth_data": {
    "username": "username",
    "password": "password", // Or API key, OAuth token, etc.
    "auth_type": "browser_session" // api_key, oauth, browser_session
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "account_id": "uuid",
    "platform": "instagram",
    "connection_status": "connected",
    "account_username": "username"
  },
  "message": "Platform connected successfully"
}
```

#### `POST /api/v1/platforms/accounts/{account_id}/disconnect`
Disconnect a platform account

#### `GET /api/v1/platforms/accounts/{account_id}/status`
Get account connection status and stats

#### `POST /api/v1/platforms/accounts/{account_id}/sync`
Manually sync account stats from platform

---

### 4. Posts & Publishing

#### `GET /api/v1/posts`
Get all posts

**Query Parameters:**
- `character_id` (optional): Filter by character
- `platform` (optional): Filter by platform
- `status` (optional): Filter by status (draft, published, failed)
- `limit`, `offset`: Pagination

**Response:**
```json
{
  "success": true,
  "data": {
    "posts": [
      {
        "id": "uuid",
        "character_id": "uuid",
        "character_name": "Character Name",
        "platform": "instagram",
        "post_type": "post",
        "platform_post_id": "123456",
        "platform_post_url": "https://instagram.com/p/...",
        "content_id": "uuid",
        "content_url": "https://...",
        "caption": "Beautiful sunset! #sunset #beach",
        "hashtags": ["sunset", "beach"],
        "likes_count": 150,
        "comments_count": 10,
        "shares_count": 5,
        "status": "published",
        "published_at": "2025-01-15T10:00:00Z",
        "created_at": "2025-01-15T09:55:00Z"
      }
    ],
    "total": 50,
    "limit": 20,
    "offset": 0
  }
}
```

#### `POST /api/v1/posts`
Create and publish a post

**Request Body:**
```json
{
  "character_id": "uuid",
  "platform_account_id": "uuid",
  "content_id": "uuid", // Or content_ids array for multiple
  "additional_content_ids": ["uuid2"], // Optional
  "caption": "Beautiful sunset! #sunset #beach",
  "hashtags": ["sunset", "beach"],
  "mentions": ["@user1"],
  "post_type": "post", // post, story, reel, etc.
  "publish_immediately": true // Or false to schedule
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "post_id": "uuid",
    "status": "published",
    "platform_post_id": "123456",
    "platform_post_url": "https://instagram.com/p/...",
    "published_at": "2025-01-15T10:00:00Z"
  },
  "message": "Post published successfully"
}
```

#### `GET /api/v1/posts/{post_id}`
Get post details

#### `DELETE /api/v1/posts/{post_id}`
Delete a post (from platform and database)

#### `POST /api/v1/posts/{post_id}/sync`
Sync engagement metrics from platform

---

### 5. Scheduling & Automation

#### `GET /api/v1/scheduled-posts`
Get scheduled posts

**Query Parameters:**
- `character_id` (optional): Filter by character
- `status` (optional): Filter by status
- `from_date`, `to_date` (optional): Date range
- `limit`, `offset`: Pagination

**Response:**
```json
{
  "success": true,
  "data": {
    "scheduled_posts": [
      {
        "id": "uuid",
        "character_id": "uuid",
        "character_name": "Character Name",
        "platform": "instagram",
        "scheduled_at": "2025-01-16T14:00:00Z",
        "content_id": "uuid",
        "caption": "Scheduled post caption",
        "status": "scheduled",
        "created_at": "2025-01-15T10:00:00Z"
      }
    ],
    "total": 10
  }
}
```

#### `POST /api/v1/scheduled-posts`
Schedule a post

**Request Body:**
```json
{
  "character_id": "uuid",
  "platform_account_id": "uuid",
  "scheduled_at": "2025-01-16T14:00:00Z",
  "timezone": "America/New_York",
  "content_id": "uuid",
  "caption": "Scheduled post caption",
  "hashtags": ["tag1", "tag2"],
  "post_type": "post"
}
```

#### `PUT /api/v1/scheduled-posts/{scheduled_post_id}`
Update scheduled post

#### `DELETE /api/v1/scheduled-posts/{scheduled_post_id}`
Cancel scheduled post

#### `GET /api/v1/automation-rules`
Get automation rules

**Query Parameters:**
- `character_id` (optional): Filter by character
- `is_enabled` (optional): Filter by enabled status

#### `POST /api/v1/automation-rules`
Create automation rule

**Request Body:**
```json
{
  "character_id": "uuid",
  "name": "Daily Instagram Posts",
  "description": "Post once daily on Instagram",
  "trigger_type": "schedule",
  "trigger_config": {
    "cron": "0 14 * * *", // 2 PM daily
    "timezone": "America/New_York"
  },
  "platforms": ["instagram"],
  "content_type": "image",
  "content_category": "post",
  "prompt_template": "A beautiful {topic} scene",
  "caption_template": "Check out this {topic}! #lifestyle",
  "hashtag_strategy": "auto",
  "max_posts_per_day": 1,
  "cooldown_minutes": 60
}
```

#### `PUT /api/v1/automation-rules/{rule_id}`
Update automation rule

#### `DELETE /api/v1/automation-rules/{rule_id}`
Delete automation rule

#### `POST /api/v1/automation-rules/{rule_id}/enable`
Enable automation rule

#### `POST /api/v1/automation-rules/{rule_id}/disable`
Disable automation rule

---

### 6. Engagement

#### `GET /api/v1/engagement/actions`
Get engagement actions (likes, comments, etc.)

**Query Parameters:**
- `character_id` (optional): Filter by character
- `platform` (optional): Filter by platform
- `action_type` (optional): Filter by action type
- `status` (optional): Filter by status
- `limit`, `offset`: Pagination

#### `POST /api/v1/engagement/like`
Like a post

**Request Body:**
```json
{
  "character_id": "uuid",
  "platform_account_id": "uuid",
  "target_type": "post",
  "target_id": "platform_post_id",
  "target_url": "https://..."
}
```

#### `POST /api/v1/engagement/comment`
Comment on a post

**Request Body:**
```json
{
  "character_id": "uuid",
  "platform_account_id": "uuid",
  "target_type": "post",
  "target_id": "platform_post_id",
  "comment_text": "Great post! 😊"
}
```

#### `POST /api/v1/engagement/follow`
Follow a user

**Request Body:**
```json
{
  "character_id": "uuid",
  "platform_account_id": "uuid",
  "target_type": "user",
  "target_id": "platform_user_id"
}
```

---

### 7. Analytics

#### `GET /api/v1/analytics/overview`
Get analytics overview

**Query Parameters:**
- `character_id` (optional): Filter by character
- `platform` (optional): Filter by platform
- `from_date`, `to_date` (optional): Date range

**Response:**
```json
{
  "success": true,
  "data": {
    "total_posts": 150,
    "total_engagement": 25000,
    "total_followers": 5000,
    "engagement_rate": 0.05,
    "follower_growth": 500,
    "top_performing_posts": [...],
    "platform_breakdown": {
      "instagram": { "posts": 100, "engagement": 20000 },
      "twitter": { "posts": 50, "engagement": 5000 }
    },
    "trends": {
      "follower_growth": [100, 150, 200, ...],
      "engagement": [1000, 1500, 2000, ...]
    }
  }
}
```

#### `GET /api/v1/analytics/characters/{character_id}`
Get character-specific analytics

#### `GET /api/v1/analytics/posts/{post_id}`
Get post-specific analytics

---

### 8. System & Settings

#### `GET /api/v1/system/health`
Health check endpoint

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "services": {
      "database": "connected",
      "redis": "connected",
      "stable_diffusion": "available",
      "ollama": "available"
    },
    "uptime_seconds": 86400
  }
}
```

#### `GET /api/v1/system/stats`
System statistics

**Response:**
```json
{
  "success": true,
  "data": {
    "total_characters": 10,
    "active_characters": 8,
    "total_content": 1000,
    "total_posts": 500,
    "storage_used_gb": 50,
    "storage_available_gb": 950
  }
}
```

#### `GET /api/v1/settings`
Get system settings

#### `PUT /api/v1/settings`
Update system settings

**Request Body:**
```json
{
  "stable_diffusion": {
    "base_url": "http://localhost:7860",
    "default_model": "realistic-vision-v6"
  },
  "ollama": {
    "base_url": "http://localhost:11434",
    "default_model": "llama3:8b"
  },
  "storage": {
    "type": "local",
    "path": "/storage"
  }
}
```

---

## WebSocket Endpoints

### Real-Time Updates

#### `WS /api/v1/ws/updates`
WebSocket connection for real-time updates

**Message Format:**
```json
{
  "type": "post_published",
  "data": {
    "character_id": "uuid",
    "post_id": "uuid",
    "platform": "instagram",
    "status": "published"
  },
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Event Types:**
- `post_published`
- `content_generated`
- `generation_completed`
- `generation_failed`
- `engagement_action_completed`
- `account_connected`
- `account_disconnected`
- `error_occurred`

---

## Rate Limiting

### Limits
- **General API**: 100 requests/minute per IP
- **Content Generation**: 10 requests/minute per user
- **Post Publishing**: 5 requests/minute per character
- **Engagement Actions**: 20 requests/minute per character

### Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

---

## Error Codes

### Standard HTTP Status Codes
- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid request
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### Custom Error Codes
- `CHARACTER_NOT_FOUND`
- `CONTENT_GENERATION_FAILED`
- `PLATFORM_CONNECTION_FAILED`
- `RATE_LIMIT_EXCEEDED`
- `INVALID_CONTENT_TYPE`
- `STORAGE_ERROR`

---

## API Documentation

### OpenAPI/Swagger
- Auto-generated from FastAPI
- Available at `/docs` (Swagger UI)
- Available at `/redoc` (ReDoc)

### Postman Collection
- Export OpenAPI spec
- Import into Postman
- Share with team

---

## Testing

### Test Strategy
1. **Unit Tests**: Individual endpoint functions
2. **Integration Tests**: Full request/response cycles
3. **E2E Tests**: Complete user workflows

### Test Tools
- **pytest**: Testing framework
- **httpx**: Async HTTP client for testing
- **pytest-asyncio**: Async test support

---

## Next Steps

1. **Set Up FastAPI Project**: Initialize project structure
2. **Create Endpoint Stubs**: Define all endpoints with basic responses
3. **Implement Authentication**: JWT or API key system
4. **Connect to Database**: SQLAlchemy models and queries
5. **Add Validation**: Pydantic models for request/response
6. **Write Tests**: Unit and integration tests
7. **Document APIs**: Ensure OpenAPI docs are complete
8. **Set Up Rate Limiting**: Implement rate limiting middleware
