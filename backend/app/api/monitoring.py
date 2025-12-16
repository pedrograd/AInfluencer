"""Real-time monitoring WebSocket endpoint.

This module provides a WebSocket endpoint for real-time system monitoring,
pushing status updates to connected clients when system state changes.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from app.api.status import unified_status
from app.services.unified_logging import get_unified_logger

router = APIRouter()

# Store active WebSocket connections
_active_connections: set[WebSocket] = set()

# Background task for monitoring
_monitoring_task: asyncio.Task[None] | None = None
_monitoring_interval = 2.0  # Update every 2 seconds


async def broadcast_status() -> None:
    """Broadcast system status to all connected WebSocket clients."""
    if not _active_connections:
        return
    
    try:
        status = unified_status()
        message = json.dumps(status)
        
        # Send to all connected clients
        disconnected = set()
        for connection in _active_connections:
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_text(message)
                else:
                    disconnected.add(connection)
            except Exception as exc:
                logger = get_unified_logger()
                logger.warning("monitoring", f"Failed to send status to client: {exc}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        _active_connections.difference_update(disconnected)
    except Exception as exc:
        logger = get_unified_logger()
        logger.error("monitoring", f"Error broadcasting status: {exc}")


async def monitoring_loop() -> None:
    """Background task that periodically broadcasts system status."""
    logger = get_unified_logger()
    logger.info("monitoring", "Real-time monitoring loop started")
    
    while True:
        try:
            await asyncio.sleep(_monitoring_interval)
            await broadcast_status()
        except asyncio.CancelledError:
            logger.info("monitoring", "Real-time monitoring loop cancelled")
            break
        except Exception as exc:
            logger.error("monitoring", f"Error in monitoring loop: {exc}")
            await asyncio.sleep(_monitoring_interval)


def start_monitoring_task() -> None:
    """Start the background monitoring task if not already running."""
    global _monitoring_task
    
    if _monitoring_task is None or _monitoring_task.done():
        loop = asyncio.get_event_loop()
        _monitoring_task = loop.create_task(monitoring_loop())


def stop_monitoring_task() -> None:
    """Stop the background monitoring task."""
    global _monitoring_task
    
    if _monitoring_task and not _monitoring_task.done():
        _monitoring_task.cancel()
        _monitoring_task = None


@router.websocket("/ws/monitoring")
async def websocket_monitoring(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time system monitoring.
    
    Clients connect to this endpoint to receive real-time updates about
    system status, including:
    - Backend service status
    - Frontend service status
    - ComfyUI service status
    - System information (OS, Python, GPU, disk)
    - Overall system status
    
    Updates are pushed every 2 seconds automatically, or immediately
    when system state changes.
    
    Example client connection:
        ```javascript
        const ws = new WebSocket('ws://localhost:8000/api/ws/monitoring');
        ws.onmessage = (event) => {
            const status = JSON.parse(event.data);
            console.log('System status:', status);
        };
        ```
    """
    logger = get_unified_logger()
    
    await websocket.accept()
    _active_connections.add(websocket)
    
    # Start monitoring task if not already running
    start_monitoring_task()
    
    # Send initial status immediately
    try:
        status = unified_status()
        await websocket.send_text(json.dumps(status))
    except Exception as exc:
        logger.warning("monitoring", f"Failed to send initial status: {exc}")
    
    logger.info("monitoring", f"WebSocket client connected (total: {len(_active_connections)})")
    
    try:
        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for client messages (ping/pong or disconnect)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle ping messages
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_text("ping")
                except Exception:
                    break
            except WebSocketDisconnect:
                break
    except Exception as exc:
        logger.warning("monitoring", f"WebSocket error: {exc}")
    finally:
        _active_connections.discard(websocket)
        logger.info("monitoring", f"WebSocket client disconnected (total: {len(_active_connections)})")
        
        # Stop monitoring task if no clients connected
        if not _active_connections:
            stop_monitoring_task()

