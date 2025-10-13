"""
app.agent.main

Main agent orchestration with integrated heartbeat monitoring.
Demonstrates how to use the heartbeat system for real-time status tracking.
"""


import ollama
import logging
from typing import Literal

from ..utils.settings import AgentBuild, settings
from .core import (
    HeartMonitor,
    Cognitive
)
from .pipelines.data_explorer import (
    DefineDataset,
    DescribeDataset
)

logger = logging.getLogger("gaby-agent")

logger.info("[Gaby Agent] Gaby Agent has been called.")

class GabyAgent(Cognitive, HeartMonitor):
    """ Main / Entry point. Interacts with Websocket during FastAPI Serving and as a pckg for debugging tasks. """

    def __init__(self, config: AgentBuild = settings.agent):

        self.config: AgentBuild = config
        self.client: ollama.Client = ollama.Client(config.server.ollama)

        super().__init__(client=self.client)

        logger.info("[Gaby Agent] Agent Cognitive state awoke and ready.")
        logger.info("[Gaby Agent] Agent Heart Monitor ready.")

    def start_session(self, workflow_type: Literal['clean', 'analyze']):
        if self.alive is False or self.state != 'idle':
            raise ValueError('Expected idle state and alive agent but agent is either dead or occupied . . . :( Check websocket connection and workspace setup. ')

    def setup_data_cleaner(self):
        """ Setup dataset cleaner """
        pipe = DefineDataset()
        pipe.set_next_stage(DescribeDataset())
        self.clean_pipe = pipe

        logger.info("[Gaby Agent] Cleaning Pipeline ready.")

    def setup_dataset(self):
        """ Setup dataset. """
        pipe = DefineDataset()
        pipe.set_next_stage(DescribeDataset())
        self.init_pipe = pipe
        logger.info("[Gaby Agent] Exploration Pipeline ready.")

    def setup_all_pipelines(self):
        """ Sets up all data pipelines ready for any type of session. """
        self.setup_dataset()
        self.setup_data_cleaner()

if __name__ == "__main__":
    print("Starting DataBy Agent demo...")
    pass