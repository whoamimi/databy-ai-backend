"""
app.agent.main

Main Gaby agent orchestration with integrated heartbeat monitoring.

"""

import asyncio
import logging
from typing import Literal
from pydantic import BaseModel, Field

from ..utils.settings import AgentBuild, settings

from .core.pipeline import DataPipeline
from .pipelines.records import SessionProfiler
from .pipelines.data_explorer import (
    DataExplorer
)

logger = logging.getLogger("gaby-agent")

logger.info("[Gaby Agent] Gaby Agent has been called.")

# Agent Handler
class GabyAgent(BaseModel):
    state: Literal["idle", "inactive", "active"] = "idle"
    state_message: str | None = None
    thinking: str | None = None
    history: list[tuple] = Field(default_factory=list, init=False)

# Session Handler
class GabyWindow(SessionProfiler):
    def __init__(self, build: AgentBuild = settings.agent, **kwargs):
        super().__init__(**kwargs)

        self.build: AgentBuild = build
        self.agent: GabyAgent = GabyAgent()
        self.countdown_task: asyncio.Task | None = None
        self.event: asyncio.Event = asyncio.Event()

    async def state_snapshot(self, message: str):
        """ Stream state snapshot."""

        return {
            "output": message,
            "agent": self.agent.model_dump_json()
        }

    @property
    def services(self):
        yield from DataPipeline.services

if __name__ == "__main__":
    print("Starting DataBy Agent demo...")

    import pandas as pd
    from uuid import uuid4
    from datetime import datetime

    data = pd.DataFrame()
    agent = GabyWindow(data=data, id=uuid4(), created_timestamp=datetime.now())
    print(agent)