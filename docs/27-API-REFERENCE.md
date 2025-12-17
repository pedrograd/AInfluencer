# Complete API Reference

## 📋 Document Metadata

### Purpose
Complete reference documentation for all AInfluencer Backend API endpoints. This document provides detailed information about every available endpoint, including request/response formats, authentication requirements, and usage examples.

### Reading Order
**Read After:** [10-API-DESIGN.md](./10-API-DESIGN.md) - API design patterns and architecture  
**Read Before:** Implementing frontend API integration, testing API endpoints

### Related Documents
**Prerequisites:**
- [10-API-DESIGN.md](./10-API-DESIGN.md) - API architecture and design patterns
- [09-DATABASE-SCHEMA.md](./09-DATABASE-SCHEMA.md) - Data models used in API responses

**Used By:**
- Frontend developers - All API integration code
- Backend developers - Endpoint implementation reference
- QA/Testing - API test case development
- API consumers - Third-party integrations

---

## API Overview

### Base URL
- **Development:** `http://localhost:8000`
- **Production:** (configured per environment)

### API Version
- **Current Version:** v1 (implicit, no version prefix)
- **Base Path:** `/api`

### Interactive Documentation
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

### Authentication
Currently, the API operates without authentication for MVP development. Future versions will support:
- JWT tokens for user authentication
- API keys for service-to-service communication

### Response Format
All endpoints return JSON responses in the following format:

**Success Response:**
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional success message",
  "timestamp": "2025-12-17T15:00:00Z"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { ... }
  },
  "timestamp": "2025-12-17T15:00:00Z"
}
```

### Rate Limiting
Rate limiting is configured per endpoint. When exceeded, the API returns:
- **Status Code:** `429 Too Many Requests`
- **Error Code:** `rate_limit_exceeded`

---

## API Endpoints by Category

### System Endpoints

#### Health & Status

**GET `/api/health`**
- **Description:** Health check endpoint for service monitoring
- **Tags:** `system`
- **Response:**
  ```json
  {
    "status": "ok",
    "redis": "connected"
  }
  ```

**GET `/api/status`**
- **Description:** Get system status and service information
- **Tags:** `system`
- **Response:** System status including service health, uptime, and configuration

**GET `/api`**
- **Description:** API root endpoint with basic information
- **Tags:** `system`
- **Response:**
  ```json
  {
    "name": "AInfluencer Backend API",
    "version": "0.0.1",
    "docs": "/docs",
    "health": "/api/health",
    "status": "/api/status"
  }
  ```

#### Logs & Monitoring

**GET `/api/logs`**
- **Description:** Retrieve application logs
- **Tags:** `system`
- **Query Parameters:**
  - `level` (optional): Filter by log level (info, warning, error)
  - `service` (optional): Filter by service name
  - `limit` (optional, default: 100): Number of log entries
  - `offset` (optional, default: 0): Pagination offset

**GET `/api/monitoring/metrics`**
- **Description:** Get system metrics
- **Tags:** `monitoring`

**GET `/api/monitoring/performance`**
- **Description:** Get performance metrics
- **Tags:** `monitoring`

#### Error Handling

**GET `/api/errors`**
- **Description:** List recent errors
- **Tags:** `system`

**GET `/api/errors/{error_id}`**
- **Description:** Get error details
- **Tags:** `system`

---

### Character Management

**Base Path:** `/api/characters`

#### Character CRUD

**POST `/api/characters`**
- **Description:** Create a new character
- **Tags:** `characters`
- **Request Body:**
  ```json
  {
    "name": "Character Name",
    "bio": "Character biography",
    "age": 25,
    "location": "New York, NY",
    "timezone": "America/New_York",
    "interests": ["photography", "travel"],
    "personality": {
      "extroversion": 0.7,
      "creativity": 0.8,
      "humor": 0.6,
      "professionalism": 0.5,
      "authenticity": 0.9,
      "communication_style": "casual",
      "preferred_topics": ["tech", "lifestyle"],
      "content_tone": "friendly",
      "temperature": 0.7
    },
    "appearance": {
      "face_reference_image_url": "https://...",
      "hair_color": "brown",
      "eye_color": "blue",
      "style_keywords": ["modern", "casual"]
    }
  }
  ```
- **Response:** Created character with ID and status

**GET `/api/characters`**
- **Description:** List all characters with filtering and pagination
- **Tags:** `characters`
- **Query Parameters:**
  - `status` (optional): Filter by status (active, paused, error)
  - `limit` (optional, default: 20): Number of results
  - `offset` (optional, default: 0): Pagination offset
  - `search` (optional): Search by name or bio
- **Response:**
  ```json
  {
    "success": true,
    "data": {
      "characters": [...],
      "total": 10,
      "limit": 20,
      "offset": 0
    }
  }
  ```

**GET `/api/characters/{character_id}`**
- **Description:** Get character details by ID
- **Tags:** `characters`
- **Response:** Complete character information including personality, appearance, and styles

**PUT `/api/characters/{character_id}`**
- **Description:** Update character information
- **Tags:** `characters`
- **Request Body:** Partial character update (all fields optional)
- **Response:** Updated character data

**DELETE `/api/characters/{character_id}`**
- **Description:** Delete a character
- **Tags:** `characters`
- **Response:** Success confirmation

#### Character Content Generation

**POST `/api/characters/{character_id}/generate/image`**
- **Description:** Generate an image for a character
- **Tags:** `characters`
- **Request Body:**
  ```json
  {
    "prompt": "A photo of the character in a coffee shop",
    "style_id": "uuid-optional",
    "negative_prompt": "blurry, low quality",
    "width": 1024,
    "height": 1024,
    "steps": 30,
    "cfg_scale": 7.0
  }
  ```
- **Response:** Generation job information

**POST `/api/characters/{character_id}/generate/content`**
- **Description:** Generate content (text, captions) for a character
- **Tags:** `characters`
- **Request Body:**
  ```json
  {
    "content_type": "caption",
    "context": "Instagram post about morning routine",
    "tone": "casual",
    "max_length": 220
  }
  ```
- **Response:** Generated content

#### Character Voice

**POST `/api/characters/{character_id}/voice/clone`**
- **Description:** Clone voice for a character
- **Tags:** `characters`
- **Request Body:**
  ```json
  {
    "audio_url": "https://...",
    "audio_path": "/path/to/audio.wav",
    "name": "Voice name"
  }
  ```
- **Response:** Voice clone job information

**POST `/api/characters/{character_id}/voice/generate`**
- **Description:** Generate speech using character voice
- **Tags:** `characters`
- **Request Body:**
  ```json
  {
    "text": "Hello, this is a test message",
    "voice_id": "uuid",
    "speed": 1.0,
    "pitch": 1.0
  }
  ```
- **Response:** Generated audio information

**GET `/api/characters/{character_id}/voice/list`**
- **Description:** List all voices for a character
- **Tags:** `characters`
- **Response:** List of voice clones

**DELETE `/api/characters/{character_id}/voice/{voice_id}`**
- **Description:** Delete a voice clone
- **Tags:** `characters`
- **Response:** Success confirmation

#### Character Styles

**POST `/api/characters/{character_id}/styles`**
- **Description:** Create a new image style for a character
- **Tags:** `characters`
- **Request Body:**
  ```json
  {
    "name": "Casual Style",
    "description": "Everyday casual look",
    "prompt_prefix": "casual outfit, natural lighting",
    "negative_prompt": "formal, professional",
    "is_default": false
  }
  ```
- **Response:** Created style information

**GET `/api/characters/{character_id}/styles`**
- **Description:** List all styles for a character
- **Tags:** `characters`
- **Response:** List of image styles

**GET `/api/characters/{character_id}/styles/{style_id}`**
- **Description:** Get style details
- **Tags:** `characters`
- **Response:** Style information

**PUT `/api/characters/{character_id}/styles/{style_id}`**
- **Description:** Update a style
- **Tags:** `characters`
- **Request Body:** Partial style update
- **Response:** Updated style information

**DELETE `/api/characters/{character_id}/styles/{style_id}`**
- **Description:** Delete a style
- **Tags:** `characters`
- **Response:** Success confirmation

---

### Content Generation

**Base Path:** `/api/generate`

#### Image Generation

**POST `/api/generate/image`**
- **Description:** Generate an image using ComfyUI
- **Tags:** `generate`
- **Request Body:**
  ```json
  {
    "prompt": "A beautiful landscape",
    "negative_prompt": "blurry, low quality",
    "width": 1024,
    "height": 1024,
    "steps": 30,
    "cfg_scale": 7.0,
    "sampler_name": "euler",
    "scheduler": "normal",
    "seed": -1,
    "character_id": "uuid-optional",
    "face_consistency_method": "ip-adapter",
    "face_embedding_id": "uuid-optional"
  }
  ```
- **Response:** Generation job information with job_id

**GET `/api/generate/image/{job_id}`**
- **Description:** Get image generation job status and result
- **Tags:** `generate`
- **Response:**
  ```json
  {
    "job_id": "uuid",
    "status": "completed",
    "result": {
      "image_url": "/content/image.png",
      "image_path": "/path/to/image.png",
      "metadata": {...}
    },
    "error": null
  }
  ```

**GET `/api/generate/image/{job_id}/rank`**
- **Description:** Get image ranking/quality score
- **Tags:** `generate`

**GET `/api/generate/image/stats`**
- **Description:** Get image generation statistics
- **Tags:** `generate`

**GET `/api/generate/image/jobs`**
- **Description:** List all image generation jobs
- **Tags:** `generate`
- **Query Parameters:**
  - `status` (optional): Filter by status
  - `limit` (optional): Number of results
  - `offset` (optional): Pagination offset

**GET `/api/generate/image/batch/queue`**
- **Description:** Get batch generation queue status
- **Tags:** `generate`

**GET `/api/generate/image/batch/{job_id}/summary`**
- **Description:** Get batch generation summary
- **Tags:** `generate`

**POST `/api/generate/image/{job_id}/cancel`**
- **Description:** Cancel a running image generation job
- **Tags:** `generate`

**GET `/api/generate/image/{job_id}/download`**
- **Description:** Download generated image
- **Tags:** `generate`
- **Response:** File download

**DELETE `/api/generate/image/{job_id}`**
- **Description:** Delete a generation job and its result
- **Tags:** `generate`

**POST `/api/generate/clear`**
- **Description:** Clear generation cache/storage
- **Tags:** `generate`

#### Text Generation

**POST `/api/generate/text`**
- **Description:** Generate text using Ollama
- **Tags:** `generate`
- **Request Body:**
  ```json
  {
    "prompt": "Write a short Instagram caption",
    "model": "llama3",
    "character_id": "uuid-optional",
    "max_tokens": 200,
    "temperature": 0.7
  }
  ```
- **Response:** Generated text

**GET `/api/generate/text/models`**
- **Description:** List available text generation models
- **Tags:** `generate`

**GET `/api/generate/text/health`**
- **Description:** Check text generation service health
- **Tags:** `generate`

#### Face Embedding

**POST `/api/generate/face-embedding/extract`**
- **Description:** Extract face embedding from an image
- **Tags:** `generate`
- **Request Body:**
  ```json
  {
    "image_url": "https://...",
    "image_path": "/path/to/image.png",
    "name": "Embedding name"
  }
  ```
- **Response:** Face embedding information

**GET `/api/generate/face-embedding/list`**
- **Description:** List all face embeddings
- **Tags:** `generate`

**GET `/api/generate/face-embedding/health`**
- **Description:** Check face embedding service health
- **Tags:** `generate`

**GET `/api/generate/face-embedding/{embedding_id}`**
- **Description:** Get face embedding details
- **Tags:** `generate`

**DELETE `/api/generate/face-embedding/{embedding_id}`**
- **Description:** Delete a face embedding
- **Tags:** `generate`

#### Video Generation

**POST `/api/generate/video`**
- **Description:** Generate a video
- **Tags:** `generate`
- **Request Body:**
  ```json
  {
    "method": "animatediff",
    "prompt": "A character walking",
    "image_url": "https://...",
    "duration": 5,
    "fps": 24
  }
  ```
- **Response:** Video generation job information

**GET `/api/generate/video/{job_id}`**
- **Description:** Get video generation job status
- **Tags:** `generate`

**GET `/api/generate/video/jobs`**
- **Description:** List all video generation jobs
- **Tags:** `generate`

**POST `/api/generate/video/{job_id}/cancel`**
- **Description:** Cancel a video generation job
- **Tags:** `generate`

**GET `/api/generate/video/presets`**
- **Description:** List video generation presets
- **Tags:** `generate`

**GET `/api/generate/video/presets/{preset_id}`**
- **Description:** Get video preset details
- **Tags:** `generate`

**GET `/api/generate/video/health`**
- **Description:** Check video generation service health
- **Tags:** `generate`

#### A/B Testing

**POST `/api/generate/image/ab-test`**
- **Description:** Create an A/B test for image generation
- **Tags:** `generate`

**GET `/api/generate/image/ab-test/{ab_test_id}`**
- **Description:** Get A/B test results
- **Tags:** `generate`

#### Storage

**GET `/api/generate/storage`**
- **Description:** Get generation storage information
- **Tags:** `generate`

---

### Content Management

**Base Path:** `/api/content`

#### Image Management

**GET `/api/content/images`**
- **Description:** List generated images
- **Tags:** `content`
- **Query Parameters:**
  - `q` (optional): Search query
  - `sort` (optional): Sort order (newest, oldest, name)
  - `limit` (optional, default: 48): Number of results
  - `offset` (optional, default: 0): Pagination offset
- **Response:**
  ```json
  {
    "items": [...],
    "total": 150,
    "limit": 48,
    "offset": 0
  }
  ```

**DELETE `/api/content/images/{filename}`**
- **Description:** Delete a specific image
- **Tags:** `content`

**POST `/api/content/images/delete`**
- **Description:** Delete multiple images
- **Tags:** `content`
- **Request Body:**
  ```json
  {
    "filenames": ["image1.png", "image2.png"]
  }
  ```

**POST `/api/content/images/cleanup`**
- **Description:** Clean up orphaned or temporary images
- **Tags:** `content`

**GET `/api/content/images/download`**
- **Description:** Download images as ZIP
- **Tags:** `content`
- **Query Parameters:**
  - `filenames` (optional): Comma-separated list of filenames
- **Response:** ZIP file download

#### Content Validation

**POST `/api/content/validate`**
- **Description:** Validate content quality
- **Tags:** `content`
- **Request Body:**
  ```json
  {
    "image_url": "https://...",
    "image_path": "/path/to/image.png"
  }
  ```
- **Response:** Validation results with quality scores

**POST `/api/content/validate/{content_id}`**
- **Description:** Validate existing content by ID
- **Tags:** `content`

#### Caption & Description Generation

**POST `/api/content/caption`**
- **Description:** Generate caption for an image
- **Tags:** `content`
- **Request Body:**
  ```json
  {
    "image_url": "https://...",
    "character_id": "uuid-optional",
    "platform": "instagram",
    "tone": "casual",
    "max_length": 220
  }
  ```
- **Response:** Generated caption

**POST `/api/content/description-tags`**
- **Description:** Generate description and tags for content
- **Tags:** `content`
- **Request Body:**
  ```json
  {
    "image_url": "https://...",
    "character_id": "uuid-optional"
  }
  ```
- **Response:** Generated description and tags

**POST `/api/content/content/{content_id}/description-tags`**
- **Description:** Generate description and tags for existing content
- **Tags:** `content`

#### Content Library

**GET `/api/content/library`**
- **Description:** List content library items
- **Tags:** `content`
- **Query Parameters:**
  - `character_id` (optional): Filter by character
  - `type` (optional): Filter by content type
  - `status` (optional): Filter by approval status
  - `limit` (optional): Number of results
  - `offset` (optional): Pagination offset
- **Response:** List of content items with metadata

**GET `/api/content/library/{content_id}`**
- **Description:** Get content library item details
- **Tags:** `content`
- **Response:** Complete content information

**GET `/api/content/library/{content_id}/preview`**
- **Description:** Get content preview (image/video)
- **Tags:** `content`
- **Response:** File response

**GET `/api/content/library/{content_id}/download`**
- **Description:** Download content file
- **Tags:** `content`
- **Response:** File download

**PUT `/api/content/library/{content_id}`**
- **Description:** Update content metadata
- **Tags:** `content`
- **Request Body:**
  ```json
  {
    "description": "Updated description",
    "tags": ["tag1", "tag2"],
    "approval_status": "approved",
    "quality_score": 8.5,
    "folder_path": "/path/to/folder"
  }
  ```
- **Response:** Updated content information

**DELETE `/api/content/library/{content_id}`**
- **Description:** Delete content from library
- **Tags:** `content`

**POST `/api/content/library/batch/approve`**
- **Description:** Approve multiple content items
- **Tags:** `content`
- **Request Body:**
  ```json
  {
    "content_ids": ["uuid1", "uuid2"]
  }
  ```

**POST `/api/content/library/batch/reject`**
- **Description:** Reject multiple content items
- **Tags:** `content`

**POST `/api/content/library/batch/delete`**
- **Description:** Delete multiple content items
- **Tags:** `content`

**POST `/api/content/library/batch/download`**
- **Description:** Download multiple content items as ZIP
- **Tags:** `content`
- **Response:** ZIP file download

**GET `/api/content/library/stats`**
- **Description:** Get content library statistics
- **Tags:** `content`

#### Content Tags

**POST `/api/content/library/{content_id}/tags`**
- **Description:** Add tags to content
- **Tags:** `content`
- **Request Body:**
  ```json
  {
    "tags": ["tag1", "tag2", "tag3"]
  }
  ```

**DELETE `/api/content/library/{content_id}/tags`**
- **Description:** Remove tags from content
- **Tags:** `content`
- **Request Body:**
  ```json
  {
    "tags": ["tag1", "tag2"]
  }
  ```

#### Content Repurposing

**POST `/api/content/library/{content_id}/repurpose`**
- **Description:** Repurpose content for a platform
- **Tags:** `content`
- **Request Body:**
  ```json
  {
    "platform": "twitter",
    "format": "square",
    "caption_style": "short"
  }
  ```
- **Response:** Repurposed content information

**POST `/api/content/library/{content_id}/repurpose/multiple`**
- **Description:** Repurpose content for multiple platforms
- **Tags:** `content`

**GET `/api/content/library/{content_id}/repurpose/platforms`**
- **Description:** Get available repurposing platforms
- **Tags:** `content`

---

### Content Intelligence

**Base Path:** `/api/content-intelligence`

**POST `/api/content-intelligence/analyze`**
- **Description:** Analyze content performance
- **Tags:** `content-intelligence`

**GET `/api/content-intelligence/trends`**
- **Description:** Get trending topics
- **Tags:** `content-intelligence`

**POST `/api/content-intelligence/optimize`**
- **Description:** Get content optimization suggestions
- **Tags:** `content-intelligence`

---

### Scheduling

**Base Path:** `/api/scheduling`

**POST `/api/scheduling/calendar`**
- **Description:** Create content calendar
- **Tags:** `scheduling`

**GET `/api/scheduling/calendar`**
- **Description:** Get content calendar
- **Tags:** `scheduling`

**POST `/api/scheduling/post`**
- **Description:** Schedule a post
- **Tags:** `scheduling`

**GET `/api/scheduling/posts`**
- **Description:** List scheduled posts
- **Tags:** `scheduling`

**PUT `/api/scheduling/posts/{post_id}`**
- **Description:** Update scheduled post
- **Tags:** `scheduling`

**DELETE `/api/scheduling/posts/{post_id}`**
- **Description:** Cancel scheduled post
- **Tags:** `scheduling`

---

### Analytics

**Base Path:** `/api/analytics`

**GET `/api/analytics/engagement`**
- **Description:** Get engagement analytics
- **Tags:** `analytics`

**GET `/api/analytics/performance`**
- **Description:** Get performance metrics
- **Tags:** `analytics`

**GET `/api/analytics/characters`**
- **Description:** Get character performance analytics
- **Tags:** `analytics`

**GET `/api/analytics/content`**
- **Description:** Get content performance analytics
- **Tags:** `analytics`

**GET `/api/analytics/trends`**
- **Description:** Get trend analysis
- **Tags:** `analytics`

---

### Platform Integrations

#### Instagram

**Base Path:** `/api/instagram`

**POST `/api/instagram/connect`**
- **Description:** Connect Instagram account
- **Tags:** `instagram`

**POST `/api/instagram/post`**
- **Description:** Create Instagram post
- **Tags:** `instagram`

**POST `/api/instagram/story`**
- **Description:** Post to Instagram Stories
- **Tags:** `instagram`

**POST `/api/instagram/reel`**
- **Description:** Upload Instagram Reel
- **Tags:** `instagram`

**POST `/api/instagram/like`**
- **Description:** Like a post
- **Tags:** `instagram`

**POST `/api/instagram/comment`**
- **Description:** Comment on a post
- **Tags:** `instagram`

#### Twitter

**Base Path:** `/api/twitter`

**POST `/api/twitter/connect`**
- **Description:** Connect Twitter account
- **Tags:** `twitter`

**POST `/api/twitter/tweet`**
- **Description:** Post a tweet
- **Tags:** `twitter`

**POST `/api/twitter/retweet`**
- **Description:** Retweet a post
- **Tags:** `twitter`

**POST `/api/twitter/reply`**
- **Description:** Reply to a tweet
- **Tags:** `twitter`

#### Facebook

**Base Path:** `/api/facebook`

**POST `/api/facebook/connect`**
- **Description:** Connect Facebook account
- **Tags:** `facebook`

**POST `/api/facebook/post`**
- **Description:** Create Facebook post
- **Tags:** `facebook`

#### YouTube

**Base Path:** `/api/youtube`

**POST `/api/youtube/connect`**
- **Description:** Connect YouTube channel
- **Tags:** `youtube`

**POST `/api/youtube/upload`**
- **Description:** Upload video to YouTube
- **Tags:** `youtube`

#### Telegram

**Base Path:** `/api/telegram`

**POST `/api/telegram/connect`**
- **Description:** Connect Telegram bot
- **Tags:** `telegram`

**POST `/api/telegram/send`**
- **Description:** Send message via Telegram
- **Tags:** `telegram`

#### OnlyFans

**Base Path:** `/api/onlyfans`

**POST `/api/onlyfans/connect`**
- **Description:** Connect OnlyFans account
- **Tags:** `onlyfans`

**POST `/api/onlyfans/upload`**
- **Description:** Upload content to OnlyFans
- **Tags:** `onlyfans`

---

### Automation

**Base Path:** `/api/automation`

**POST `/api/automation/strategy`**
- **Description:** Configure automation strategy
- **Tags:** `automation`

**GET `/api/automation/strategy`**
- **Description:** Get automation strategy
- **Tags:** `automation`

**POST `/api/automation/execute`**
- **Description:** Execute automation task
- **Tags:** `automation`

---

### Voice

**Base Path:** `/api/voice`

**POST `/api/voice/clone`**
- **Description:** Clone a voice
- **Tags:** `voice`

**POST `/api/voice/generate`**
- **Description:** Generate speech
- **Tags:** `voice`

**GET `/api/voice/list`**
- **Description:** List voice clones
- **Tags:** `voice`

---

### Video

**Base Path:** `/api/video`

**POST `/api/video/edit`**
- **Description:** Edit video
- **Tags:** `video`

**POST `/api/video/sync`**
- **Description:** Sync audio and video
- **Tags:** `video`

---

### Workflows

**Base Path:** `/api/workflows`

**GET `/api/workflows`**
- **Description:** List available workflows
- **Tags:** `workflows`

**GET `/api/workflows/{workflow_id}`**
- **Description:** Get workflow details
- **Tags:** `workflows`

**POST `/api/workflows/{workflow_id}/run`**
- **Description:** Run a workflow
- **Tags:** `workflows`

---

### Services

**Base Path:** `/api/services`

**GET `/api/services`**
- **Description:** List all services
- **Tags:** `services`

**GET `/api/services/{service_name}`**
- **Description:** Get service status
- **Tags:** `services`

**POST `/api/services/{service_name}/start`**
- **Description:** Start a service
- **Tags:** `services`

**POST `/api/services/{service_name}/stop`**
- **Description:** Stop a service
- **Tags:** `services`

**POST `/api/services/{service_name}/restart`**
- **Description:** Restart a service
- **Tags:** `services`

---

### ComfyUI

**Base Path:** `/api/comfyui`

**GET `/api/comfyui/status`**
- **Description:** Get ComfyUI service status
- **Tags:** `comfyui`

**GET `/api/comfyui/workflows`**
- **Description:** List ComfyUI workflows
- **Tags:** `comfyui`

**POST `/api/comfyui/queue`**
- **Description:** Queue a ComfyUI job
- **Tags:** `comfyui`

---

### Settings

**Base Path:** `/api/settings`

**GET `/api/settings`**
- **Description:** Get application settings
- **Tags:** `settings`

**PUT `/api/settings`**
- **Description:** Update application settings
- **Tags:** `settings`

---

### Models

**Base Path:** `/api/models`

**GET `/api/models`**
- **Description:** List available AI models
- **Tags:** `models`

**GET `/api/models/{model_id}`**
- **Description:** Get model details
- **Tags:** `models`

**POST `/api/models/install`**
- **Description:** Install a model
- **Tags:** `models`

---

### Resources

**Base Path:** `/api/resources`

**GET `/api/resources/gpu`**
- **Description:** Get GPU resource information
- **Tags:** `resources`

**GET `/api/resources/memory`**
- **Description:** Get memory usage
- **Tags:** `resources`

**GET `/api/resources/storage`**
- **Description:** Get storage information
- **Tags:** `resources`

---

### Posts

**Base Path:** `/api/posts`

**GET `/api/posts`**
- **Description:** List all posts
- **Tags:** `posts`

**POST `/api/posts`**
- **Description:** Create a post
- **Tags:** `posts`

**GET `/api/posts/{post_id}`**
- **Description:** Get post details
- **Tags:** `posts`

**PUT `/api/posts/{post_id}`**
- **Description:** Update a post
- **Tags:** `posts`

---

### Payment

**Base Path:** `/api/payment`

**POST `/api/payment/create`**
- **Description:** Create payment
- **Tags:** `payment`

**GET `/api/payment/{payment_id}`**
- **Description:** Get payment status
- **Tags:** `payment`

---

### Crisis Management

**Base Path:** `/api/crisis`

**GET `/api/crisis/events`**
- **Description:** List crisis events
- **Tags:** `crisis-management`

**POST `/api/crisis/handle`**
- **Description:** Handle a crisis event
- **Tags:** `crisis-management`

---

### Platform Optimization

**Base Path:** `/api/platform`

**GET `/api/platform/optimize`**
- **Description:** Get optimization suggestions
- **Tags:** `platform-optimization`

**POST `/api/platform/optimize`**
- **Description:** Apply optimization
- **Tags:** `platform-optimization`

---

### Installer

**Base Path:** `/api/installer`

**GET `/api/installer/status`**
- **Description:** Get installer status
- **Tags:** `installer`

**POST `/api/installer/install`**
- **Description:** Install a component
- **Tags:** `installer`

---

## Complete Endpoint Index

For a complete list of all 282+ endpoints with their exact paths and methods, refer to the interactive API documentation:

- **Swagger UI:** `http://localhost:8000/docs`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

The Swagger UI provides:
- Complete endpoint listing
- Interactive API testing
- Request/response schema documentation
- Authentication testing (when configured)

---

## Error Codes

Common error codes returned by the API:

| Code | Description |
|------|-------------|
| `validation_error` | Request validation failed |
| `not_found` | Resource not found |
| `rate_limit_exceeded` | Rate limit exceeded |
| `service_unavailable` | Service temporarily unavailable |
| `internal_error` | Internal server error |
| `unauthorized` | Authentication required |
| `forbidden` | Access denied |

---

## Rate Limits

Rate limits are configured per endpoint. Default limits:
- **Image Generation:** 10 requests/minute
- **Text Generation:** 30 requests/minute
- **Content Operations:** 60 requests/minute
- **Character Operations:** 30 requests/minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time when limit resets

---

## Best Practices

1. **Always check job status** for async operations (image/video generation)
2. **Use pagination** for list endpoints to avoid large responses
3. **Handle rate limits** with exponential backoff
4. **Validate responses** before processing data
5. **Use appropriate HTTP methods** (GET for reads, POST for creates, PUT for updates, DELETE for deletes)
6. **Include error handling** for all API calls
7. **Cache responses** when appropriate to reduce API calls

---

## Changelog

**2025-12-17:** Initial API reference documentation created
- Documented all major endpoint categories
- Added request/response examples
- Included error handling information

---

**END OF API REFERENCE**
