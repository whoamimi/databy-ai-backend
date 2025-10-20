"""
app.api.auth

API endpoints for handling google auth.

Endpoints:
- GET /data/google-sheets/auth: Initiate Google Sheets OAuth flow
- GET /data/google-sheets/callback: Handle OAuth callback from Google
- POST /data/google-sheets/validate: Validate Google Sheets access
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from .utils.schemas import (
    GoogleSheetsData
)

logger = logging.getLogger("uvicorn")
data_router = APIRouter(prefix="/data", tags=["data-inputs"])

# Store pending Google Sheets auth sessions (in production, use Redis or database)
_pending_google_auth: dict[str, dict] = {}

@data_router.get("/google-sheets/auth")
async def google_sheets_auth_init(
    session_id: str = Query(..., description="Session ID to associate with this auth"),
    redirect_uri: str = Query(..., description="URI to redirect back to after auth")
):
    """
    Initiates Google Sheets OAuth flow.

    In production, this should:
    1. Generate OAuth URL with proper scopes
    2. Store session_id and redirect_uri in cache
    3. Redirect user to Google OAuth consent page
    """
    # Store session info
    _pending_google_auth[session_id] = {
        "redirect_uri": redirect_uri,
        "timestamp": None  # TODO: Add timestamp
    }

    # TODO: Replace with actual Google OAuth URL generation
    google_oauth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        "client_id=YOUR_CLIENT_ID&"
        "redirect_uri=YOUR_REDIRECT_URI&"
        "response_type=code&"
        "scope=https://www.googleapis.com/auth/spreadsheets.readonly&"
        f"state={session_id}"
    )

    logger.info(f"Initiating Google Sheets auth for session {session_id}")

    return {
        "status": "redirect",
        "auth_url": google_oauth_url,
        "session_id": session_id
    }


@data_router.get("/google-sheets/callback")
async def google_sheets_auth_callback(
    code: str = Query(..., description="OAuth authorization code"),
    state: str = Query(..., description="Session ID from state parameter"),
    error: str | None = Query(None, description="Error from OAuth provider")
):
    """
    Handles the OAuth callback from Google.

    In production, this should:
    1. Exchange code for access_token
    2. Store access_token securely
    3. Redirect back to original application with session_id
    """
    if error:
        logger.error(f"Google OAuth error: {error}")
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    session_id = state

    if session_id not in _pending_google_auth:
        raise HTTPException(status_code=400, detail="Invalid or expired session")

    # TODO: Exchange code for access_token using Google OAuth API
    # access_token = exchange_code_for_token(code)

    session_info = _pending_google_auth.pop(session_id)
    redirect_uri = session_info.get("redirect_uri", "/")

    logger.info(f"Google Sheets auth successful for session {session_id}")

    # Redirect back to application with session info
    return RedirectResponse(
        url=f"{redirect_uri}?session_id={session_id}&auth=success"
    )


@data_router.post("/google-sheets/validate")
async def validate_google_sheets(data: GoogleSheetsData):
    """
    Validates Google Sheets data configuration.
    Can be used to test spreadsheet access before starting a job.
    """
    try:
        # TODO: Test actual Google Sheets API access
        # sheets_service = build('sheets', 'v4', credentials=credentials)
        # result = sheets_service.spreadsheets().values().get(
        #     spreadsheetId=data.spreadsheet_id,
        #     range=data.range or 'A1:Z1'
        # ).execute()

        logger.info(f"Validating Google Sheets: {data.spreadsheet_id}")

        return {
            "status": "success",
            "spreadsheet_id": data.spreadsheet_id,
            "sheet_name": data.sheet_name,
            "accessible": True  # TODO: Replace with actual check
        }

    except Exception as e:
        logger.error(f"Google Sheets validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
