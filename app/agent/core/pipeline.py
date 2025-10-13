"""
app.agent.core.chain

Pipeline Chain Builder for agent's workflow.
"""

import logging
from abc import ABC, abstractmethod
from .heartbeat import HeartMonitor

logger = logging.getLogger("databy.agent.pipeline")

class ChainBuilder(ABC):
    """ Base class builder for all stages. """

    @abstractmethod
    def set_next_stage(self, stage: "ChainBuilder"):
        """ Sets the next stage after handling the current stage. """
        pass

    @abstractmethod
    def forward(self, agent: HeartMonitor, session):
        """ forward logic e.g. invoke next stage instead of the current. """
        pass

    @abstractmethod
    def update_agent_state(self, agent: HeartMonitor):
        """ Changes made to the agent's state per sequential update. """
        pass

    @abstractmethod
    def validate_stage_output(self, session):
        """ Validates the reports / outputs per stage change. """
        pass

class ChainStage(ChainBuilder):
    _next_stage: ChainBuilder | None = None

    def set_next_stage(self, stage: ChainBuilder):
        self._next_stage = stage
        return stage

    def update_agent_state(self, agent: HeartMonitor):
        """ Updates / Changes to the agent's state per stage change. """

        agent.state = f"{str(self._next_stage.__class__.__qualname__)}"

        return agent

    @abstractmethod
    def validate_stage_output(self, session) -:
        """ Validates the reports / outputs per stage change.
        TODO: update final checks
        """
        return session

    @abstractmethod
    def forward(self, agent: HeartMonitor, session):

        if self._next_stage:
            # 1. Updates the agent's heart monitor activity for current stage (not next)
            agent = self.update_agent_state(agent)
            # 2. Calls the session's validations rules
            logger.info(f"Agent state updated to: {agent.state}")
            session = self.validate_stage_output(session)
            # 3. Calls the next stage
            logger.info(f"Executing next stage: {self._next_stage.__class__.__qualname__}")
            return self._next_stage.forward(agent, session)

        logger.info(f"Completed {self.__class__.__qualname__} workflow. Running final report for entire session")
        super().validate_stage_output(session)

        return None


#    def __init_subclass__(cls, prompt_chain: list) -> None:
#        cls.prompt_chain = prompt_chain
#        return super().__init_subclass__()