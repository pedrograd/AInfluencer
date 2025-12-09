# AInfluencer Backend API

FastAPI backend for the AInfluencer web application.

## Features

- File upload handling
- Media management
- Character management
- WebSocket support for real-time updates
- Proxy to ComfyUI

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python main.py
# or
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

## API Endpoints

### Health
- `GET /` - Root endpoint
- `GET /api/health` - Health check

### Media
- `GET /api/media` - List all media
- `GET /api/media/{media_id}` - Get specific media
- `DELETE /api/media/{media_id}` - Delete media

### Characters
- `GET /api/characters` - List all characters
- `GET /api/characters/{character_id}` - Get specific character
- `POST /api/characters` - Create character
- `PUT /api/characters/{character_id}` - Update character
- `DELETE /api/characters/{character_id}` - Delete character

### Upload
- `POST /api/upload/image` - Upload image file

### WebSocket
- `WS /ws` - WebSocket connection for real-time updates

## Development

The backend is designed to work alongside the Next.js frontend and ComfyUI. It handles file management and provides a RESTful API for the web application.
