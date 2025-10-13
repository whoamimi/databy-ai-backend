"""
app/api/socket.py

WebSocket endpoints for DataBy AI’s autonomous agent.
Handles agent heartbeats, streaming Parquet data, and client communication.
"""

import json
import logging
from datetime import datetime
from typing import Literal, Any

import pandas as pd
import pyarrow.parquet as pq
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from dataclasses import asdict

from ..agent.core.heartbeat import HeartMonitor

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------

logger = logging.getLogger("databy-websocket")
ws_router = APIRouter(prefix="/agent")

heartbeat = HeartMonitor(alive=False)
active_connections: set[WebSocket] = set()

# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------

class SocketOutput(BaseModel):
    type: str
    content: dict | str
    agent: dict = Field(default_factory=lambda: asdict(heartbeat))

class SocketInput(BaseModel):
    type: Literal["ping", "clean", "contact"]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class IncomingData(SocketInput):
    input_method: Literal[
        "mongodb", "hugging-face", "kaggle", "user-input", "supabase", "aws", "gcloud"
    ]
    data: Any | None = None
    credentials: Any | None = None

class CleanForm(IncomingData):
    input_tags: list[str]
    model_objective: str

class InsightForm(IncomingData):
    input_tags: list[str]
    description: str | None

WELCOME_MSG = SocketOutput(
    type="connection_established",
    content={
        "message": "Connected to DataBy AI Agent WebSocket",
        "available_commands": [
            "ping - Check agent status",
            "subscribe - Subscribe to real-time updates",
            "getStatus - Get current status",
            "cleanReport - Request data summary",
            "setAgentState - Manually set agent state",
        ],
    },
)

# -----------------------------------------------------------------------------
# Core WebSocket Endpoint
# -----------------------------------------------------------------------------

@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Main WebSocket endpoint for real-time agent communication."""
    await websocket.accept()
    active_connections.add(websocket)
    heartbeat.set_alive(True)

    await websocket.send_text(WELCOME_MSG.model_dump_json())
    logger.info("🔌 Client connected to DataBy AI WebSocket")

    try:
        while True:
            raw_message = await websocket.receive_text()

            try:
                message = json.loads(raw_message)
                msg_type = message.get("type")
            except json.JSONDecodeError:
                await websocket.send_text(
                    SocketOutput(
                        type="error_input_format",
                        content="Message must be valid JSON.",
                    ).model_dump_json()
                )
                continue

            logger.info(f"📩 Received message: {msg_type}")

            # --- handle message types ---
            if msg_type == "ping":
                response = SocketOutput(
                    type="pong",
                    content={"alive": heartbeat.is_alive, "timestamp": heartbeat.last_ping},
                )

            else:
                response = SocketOutput(
                    type="error_unknown_command",
                    content=f"Unrecognized command: {msg_type}",
                )

            await websocket.send_text(response.model_dump_json())

    except WebSocketDisconnect:
        logger.info("🔻 WebSocket client disconnected")
    except Exception as e:
        logger.exception("Unhandled WebSocket error")
        await websocket.send_text(
            SocketOutput(
                type="server_error", content=f"Internal server error: {str(e)}"
            ).model_dump_json()
        )
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
        heartbeat.set_alive(False)
        logger.info(f"🔒 Connection closed. Active: {len(active_connections)}")