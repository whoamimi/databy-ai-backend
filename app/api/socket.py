"""
app/api/socket.py

Agent's Streaming Window to display decision-tree and actions.
"""

import asyncio
import logging

# from starlette.requests import Request
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse, JSONResponse

from ..utils.settings import settings
from .utils.manager import ConnectionManager
from .utils.schemas import CleanForm

logger = logging.getLogger("uvicorn")
window: APIRouter = APIRouter(prefix="/agent")
templates = Jinja2Templates(directory=str(settings.template_path))

manager: ConnectionManager = ConnectionManager()

async def generate_stream(room_id: str, service: str):
    """ Streaming agent's state to platform. TODO: STREAM TEXTS / STATUS FROM OBJ AGENTSTATUS. """

    room = await manager.get_room(room_id)
    logger.info(f"Starting stream for {room_id}:{service}")

    try:
        while not room.event.is_set():
            await asyncio.sleep(1.5)
            message = f"{room.id}: {room.agent.state_message}"
            # Proper SSE format
            yield f"state: {message}\n\n"
    except Exception as e:
        logger.error(f"Stream error for {room_id}:{service}\n{e}")
    finally:
        logger.info(f"Stream ended for {room_id}:{service}")
        yield f"State: [System] Stream closed for {room_id}:{service}\n\n"
        await manager.remove(str(room.id))
        yield f"Room Session has been closed."

@window.post("/start-wrangler")
async def start_wrangler_session(inputs: CleanForm):
    """
    Launches the appropriate data wrangling service (clean or insights)
    based on the request payload.

    Args:
        upload_type (str): One of ["file-upload", "hugging-face", "kaggle",
                                   "supabase", "mongodb", "google-sheets"]
        inputs (IncomingData): Automatically validated and parsed input payload.

    Returns:
        RedirectResponse: Always redirects to agent window, even on error.
    """
    room_id = str(inputs.id)

    try:
        session = inputs.get_session_window
        await manager.add(session)
        # session.countdown_task = asyncio.create_task(manager.countdown(room_id))
        return RedirectResponse(url=f"/agent/{room_id}/clean", status_code=303)
    except Exception as e:
        # Log the error but still redirect to show it in the agent window
        logger.error(f"Error starting session {room_id}: {e}")
        # Create a minimal error session to display the error
        error_message = str(e)
        return RedirectResponse(
            url=f"/agent/{room_id}/clean?error={error_message}",
            status_code=303
        )

@window.get("/{room_id}/{service}", response_class=HTMLResponse)
async def agent_window(request: Request, room_id: str, service: str):
    """
    Serves both the HTML streaming interface and, if requested with the appropriate
    'Accept' header, streams live Server-Sent Events (SSE) updates.
    """

    # Get error message from query params if present
    error_message = request.query_params.get("error")

    if room_id not in manager.rooms and not error_message:
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
        "service": service,
        "stream": "Connecting . . .",
        "error": error_message
    })