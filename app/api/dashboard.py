"""
app.api.dashboard

Agent's Data Insights & Analytics Dashboard App Rerouters.

"""

import asyncio
import logging
from typing import Literal

# from starlette.requests import Request
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse, JSONResponse

from ..utils.settings import settings
from .utils.schemas import InsightForm

logger = logging.getLogger("uvicorn")
dashboard: APIRouter = APIRouter(prefix="/app")
templates = Jinja2Templates(directory=str(settings.template_path))

async def generate_stream(room_id: str, service: str):
    """
    Continuously yields live updates for a given (room_id, service).
    Each stream is fully isolated from others.
    TODO: update this function. This fn is the main communication endpoint.
    TODO: STREAM TEXTS / STATUS FROM OBJ AGENTSTATUS
    TODO: Implement actual dashboard streaming logic
    """
    logger.info(f"Starting stream for {room_id}:{service}")

    try:
        # Placeholder streaming logic
        for i in range(5):
            await asyncio.sleep(1.5)
            message = f"Dashboard stream update {i+1} for room {room_id}"
            # Proper SSE format
            yield f"data: {message}\n\n"
    except Exception as e:
        logger.error(f"Stream error for {room_id}: {e}")
    finally:
        logger.info(f"Stream ended for {room_id}:{service}")
        yield f"data: [System] Stream closed for {room_id}:{service}\n\n"

@dashboard.post("/start-dashboard-app")
async def start_wrangler_session(inputs: InsightForm):
    """
    Launches the appropriate data wrangling service (clean or insights)
    based on the request payload.

    Args:
        upload_type (str): One of ["file-upload", "hugging-face", "kaggle",
                                   "supabase", "mongodb", "google-sheets"]
        inputs (IncomingData): Automatically validated and parsed input payload.

    Returns:
        JSONResponse: Structured response with status, message, and data.
    """
    try:
        session = inputs.get_session_window
        return JSONResponse(status_code=200, content=inputs.model_dump_json())
    except Exception as e:
        raise e
