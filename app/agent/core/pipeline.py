"""
app.agent.core.chain

Pipeline Chain Builder for agent's workflow.

TODO: revise GabyAgent

"""

import logging
from abc import ABC, abstractmethod
from collections import OrderedDict

from ..pipelines.records import SessionProfiler

logger = logging.getLogger("databy.agent.pipeline")

class ChainBuilder(ABC):
    """Base class for all pipeline stages."""

    @abstractmethod
    def set_next_stage(self, stage: "ChainBuilder"):
        """Sets the next stage in the pipeline chain."""
        pass

    @abstractmethod
    def forward(self, session: SessionProfiler):
        """Executes the stage logic and forwards to next stage."""
        pass

    @abstractmethod
    def update_agent_state(self, session: SessionProfiler):
        """Updates the agent's state during stage execution."""
        pass

    @abstractmethod
    def validate_stage_output(self, session: SessionProfiler):
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

    def update_agent_state(self, session: SessionProfiler):
        """Updates agent state to reflect the next stage name.

        Args:
            agent (HeartMonitor): Agent to update

        Returns:
            HeartMonitor: Updated agent instance

        TODO: Revise this method's functionality.
        """

        session.agent.state = f"{str(self._next_stage.__class__.__qualname__)}"
        return session

    @abstractmethod
    def validate_stage_output(self, session):
        """Validates stage output before proceeding.

        Args:
            session: Session data to validate

        Returns:
            Session data after validation
        """
        pass

    @abstractmethod
    def forward(self, session: SessionProfiler):
        """Executes the stage and forwards to next stage if available.

        Args:
            session: Session data to process

        Returns:
            Result from next stage or None if this is the final stage
        """

        # 1. Calls the session's validations rules
        self.validate_stage_output(session)
        # 2. Updates the agent's heart monitor activity defined at the current stage
        session = self.update_agent_state(session)
        logger.info(f"Agent state updated to: {session.agent.state}")

        if self._next_stage is not None:
            # 3. Calls the next stage
            logger.info(f"Executing next stage: {self._next_stage.__class__.__qualname__}")
            return self._next_stage.forward(session)
        else:
            logger.info(f"Completed {self.__class__.__qualname__} workflow. Running final report for entire session")
            # super().validate_stage_output(session)
            return session

class DataPipeline(ABC):
    services: OrderedDict = OrderedDict()

    def __call__(self, session):
        """Runs the pipeline workflow."""

        if not hasattr(self, "pipe") or self.pipe is None:
            raise RuntimeError(
                f"No pipeline assigned in {self.__class__.__name__}. "
                "Call reset(pipeline) or define 'chain' during subclass initialization."
            )

        return self.pipe.forward(session)

    def __init_subclass__(cls, kwargs):
        """
        Automatically build a linked chain of pipeline stages when subclassed.
        Example:
            class MyPipeline(DataPipeline, chain=OrderedDict([
                ("stage1", StageA()),
                ("stage2", StageB())
            ])): ...
        """
        super().__init_subclass__()

        for idx, key in enumerate(kwargs):
            if idx == 0:
                setattr(cls, "pipe", kwargs[key]())
            else:
                setattr(cls, key, kwargs[key]())
                getattr(cls, "pipe").set_next_stage(getattr(cls, key))

            DataPipeline.services[cls.__qualname__] = cls