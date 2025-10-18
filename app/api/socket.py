"""
app/api/socket.py

Agent's Streaming Window to display decision-tree and actions.
"""

import asyncio
import logging
from uuid import uuid4
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from starlette.requests import Request

from ..utils.settings import settings
from .utils.connection import ConnectionManager
from .utils.schemas import Room

logger = logging.getLogger("uvicorn")
window: APIRouter = APIRouter(prefix="/agent")

manager: ConnectionManager = ConnectionManager()
templates = Jinja2Templates(directory=str(settings.static_path))

async def generate_stream(room_id: str, service: str):
    """
    Continuously yields live updates for a given (room_id, service).
    Each stream is fully isolated from others.
    TODO: update this function. This fn is the main communication endpoint.
    TODO: STREAM TEXTS / STATUS FROM OBJ AGENTSTATUS
    """

    stop_event = await manager.get_room(room_id)
    logger.info(f"Starting stream for {room_id}:{service}")

    while not stop_event.is_set():
        await asyncio.sleep(1.5)
        message = f"Active Streams: {manager.total_active} from {service} (room {room_id})\n\n"
        yield message.encode("utf-8")

    logger.info(f"Stream ended for {room_id}:{service}")
    yield f"data: [System] Stream closed for {room_id}:{service}\n\n".encode("utf-8")


async def start_agent_window(service: str):
    """ Utility Redirecting fn to respective page and session. """

    room = Room(service=service)
    room_id = str(room.id)
    await manager.add(room)
    return RedirectResponse(url=f"/agent/window/{room_id}/{service}")

@window.get("/clean/")
async def start_data_cleaning():
    """
    Auto-creates a new isolated streaming session and redirects
    to /window/{room_id}/{service}.
    """
    await start_agent_window(service="clean")

@window.get("/analytics/")
async def start_data_dashboard():
    """
    Auto-creates a new isolated streaming session and redirects
    to /window/{room_id}/{service}.
    """
    await start_agent_window(service="analytics")

@window.get("/window/{room_id}/{service}", response_class=HTMLResponse)
async def agent_window(request: Request, room_id: str, service: str):
    """
    Serves both the HTML streaming interface and, if requested with the appropriate
    'Accept' header, streams live Server-Sent Events (SSE) updates.
    """
    if room_id not in manager.rooms:
        logger.warning(f"Attempt to access non-existent room: {room_id}")
        return HTMLResponse(content="Room not found", status_code=404)

    # Detect if this is an EventSource (SSE) request
    if request.headers.get("accept") == "text/event-stream":
        logger.info(f"Starting SSE stream for {room_id}:{service}")
        return StreamingResponse(generate_stream(room_id, service), media_type="text/event-stream")

    # Otherwise, serve the HTML page
    logger.info(f"Serving HTML window for {room_id}:{service}")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "room_id": room_id,
        "service": service
    })