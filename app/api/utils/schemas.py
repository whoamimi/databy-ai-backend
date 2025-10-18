"""
app.api.schemas
"""

import asyncio
from uuid import uuid4, UUID
from datetime import datetime
from pydantic import BaseModel, Field

from ollama import Message, ChatResponse
from typing import Literal, Any

# BASE MODEL CLASS
class SessionBase(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AgentState(BaseModel):
    mood: str | Literal["idle", "inactive", "active"] = "clean"

# STREAMING SOCKETS
class Room(SessionBase, AgentState):
    history: list[tuple] = Field(default_factory=list)
    service: str | Literal["clean", "analytics"] = Field(default="clean")
    event: asyncio.Event | None = Field(default=None)

class Output(Message, AgentState):
    pass

# FASTAPI ENDPOINTS
class IncomingData(SessionBase):
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

if __name__ == "__main__":
    room = Room(service="clean")
    print(room)