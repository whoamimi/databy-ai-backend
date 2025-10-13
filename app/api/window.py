"""
app.api.window

# TODO: remove as websocket is more scalable. Unless, theres another way to use this route.
"""

import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from ..utils.settings import settings

agent_window_router = APIRouter(prefix="/agent-window", tags=["Agent Window"])
templates = Jinja2Templates(directory=str(settings.static_path))

@agent_window_router.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@agent_window_router.get("/stream")
async def agent_window_stream():
    async def event_generator():
        count = 0
        while True:
            count += 1
            yield f"State: idle {count}\n\n"
            await asyncio.sleep(1.5)
    return StreamingResponse(event_generator(), media_type="text/event-stream")