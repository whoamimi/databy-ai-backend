"""
app.agent.main

Main Gaby agent orchestration with integrated heartbeat monitoring.

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

    def __init__(self, config: AgentBuild = settings.agent, log_level: str = settings.log_level):
        # config build
        self.server = config.server
        self.log_level = log_level

        # AI/ML server / clients. Ollama is used by default for debugging.
        if self.log_level == "DEBUG":
            self.client: ollama.Client = ollama.Client(config.server.ollama)
        else:
            pass

        super().__init__(client=self.client)

        logger.info("[Gaby Agent] Agent Cognitive state awoke and ready.")
        logger.info("[Gaby Agent] Agent Heart Monitor ready.")

    def setup_data_workspace(self):
        """ Setup datas workspace for agent. """

        pipe = DefineDataset()
        pipe.set_next_stage(DescribeDataset())
        self.init_pipe = pipe
        logger.info("[Gaby Agent] Exploration Pipeline ready.")

    def reset(self):
        """ Sets up all data pipelines ready for any type of session. """
        self.setup_data_workspace()

if __name__ == "__main__":
    print("Starting DataBy Agent demo...")
    pass