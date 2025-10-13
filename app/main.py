# src/databy/main.py
# TODO: DOCUMENT ENDPOINT FOR THE FASTAPI APP....

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .utils.settings import settings
from .api.docs import docs_router
# from .api.socket import ws_router
from .api.window import agent_window_router

logger = logging.getLogger("uvicorn")
logger.propagate = True

app = FastAPI(
    title=settings.app_title, #settings.API_TITLE,
    description=settings.app_description,
    version=settings.app_version,
)
# CORS middleware for Vite dev server (adjust origins in settings)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",  # Vite dev server default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(docs_router)
# app.include_router(ws_router)
app.include_router(agent_window_router)

@app.get("/")
async def root():
    """Root endpoint."""

    return {
        "message": "Welcome to" + settings.app_title + "!",
        "version": settings.app_version,
        "documentation": settings.docs_endpoint
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "databy-ai"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.exception("Unhandled exception: %s", exc)

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )

