"""
app.main

TODO: DOCUMENT ENDPOINT FOR THE FASTAPI APP....
"""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .utils.settings import settings
from .api.socket import window
from .api.datasource import router
from .api.mongodb import mongo
from .api.dashboard import dashboard

logger = logging.getLogger("uvicorn")
logger.propagate = True

app = FastAPI(
    title=settings.app_title, #settings.API_TITLE,
    description=settings.app_description,
    version=settings.app_version,
)

# CORS middleware for NextJS dev server (adjust origins in settings)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",  # NextJS dev server default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Mount static files BEFORE including routers
app.mount("/static", StaticFiles(directory=str(settings.static_path)), name="static")
app.include_router(window)
app.include_router(router)
app.include_router(mongo)
app.include_router(dashboard)

@app.get("/", include_in_schema=False)
async def root():
    """
    Redirect root URL to the automatic Swagger UI docs page.
    """
    return RedirectResponse(url="/docs")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.exception("Unhandled exception: %s", exc)

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )

