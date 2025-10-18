"""
app.agent.core.chain

Pipeline Chain Builder for agent's workflow.

TODO: revise GabyAgent

"""

import logging
from abc import ABC, abstractmethod
from .heartbeat import HeartMonitor

logger = logging.getLogger("databy.agent.pipeline")

class ChainBuilder(ABC):
    """Base class for all pipeline stages."""

    @abstractmethod
    def set_next_stage(self, stage: "ChainBuilder"):
        """Sets the next stage in the pipeline chain."""
        pass

    @abstractmethod
    def forward(self, agent: HeartMonitor, session):
        """Executes the stage logic and forwards to next stage."""
        pass

    @abstractmethod
    def update_agent_state(self, agent: HeartMonitor):
        """Updates the agent's state during stage execution."""
        pass

    @abstractmethod
    def validate_stage_output(self, session):
        """Validates the stage output before proceeding."""
        pass

class ChainStage(ChainBuilder):
    """Concrete implementation of ChainBuilder with pipeline chaining logic."""

    _next_stage: ChainBuilder | None = None

    def set_next_stage(self, stage: ChainBuilder):
        """Sets the next stage and returns it for chaining.

        Args:
            stage (ChainBuilder): Next stage in the pipeline

        Returns:
            ChainBuilder: The stage that was set as next
        """
        self._next_stage = stage
        return stage

    def update_agent_state(self, agent: HeartMonitor):
        """Updates agent state to reflect the next stage name.

        Args:
            agent (HeartMonitor): Agent to update

        Returns:
            HeartMonitor: Updated agent instance

        TODO: Revise this method's functionality.
        """
        agent.state = f"{str(self._next_stage.__class__.__qualname__)}"
        return agent

    @abstractmethod
    def validate_stage_output(self, session):
        """Validates stage output before proceeding.

        Args:
            session: Session data to validate

        Returns:
            Session data after validation
        """
        return session

    @abstractmethod
    def forward(self, agent: HeartMonitor, session):
        """Executes the stage and forwards to next stage if available.

        Args:
            agent (HeartMonitor): Agent with current state
            session: Session data to process

        Returns:
            Result from next stage or None if this is the final stage
        """
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

class SewageSystem(ABC):
    @abstractmethod
    def reset(self, pipeline: ChainStage):
        """ Rechain the pipeline if required. """
        pass

    @abstractmethod
    def run(self, session):
        """ Runs the pipeline / workflow / cycle. """
        pass


class BasementPipe(SewageSystem):
    def __init__(self, pipe: ChainStage):
        """Initialize with an optional pipeline root stage."""
        self.pipe = pipe

    def reset(self, pipeline: ChainStage):
        """Rechain the pipeline by assigning the root stage."""
        self.pipe = pipeline
        return self.pipe

    def run(self, **kwargs):
        """Run the pipeline expecting 'agent' and 'session' in kwargs."""
        try:
            if self.pipe is None:
                raise RuntimeError("No pipeline assigned to BasementPipe. Call reset(pipeline) first.")

            agent = kwargs.get("agent")
            session = kwargs.get("session")

            if agent is None or session is None:
                raise TypeError("run() requires 'agent' and 'session' keyword arguments.")

            return self.pipe.forward(agent, session)
        except Exception as e:
            raise e