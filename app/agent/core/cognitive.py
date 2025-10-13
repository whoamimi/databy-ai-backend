""" app/agent/core/cognitive.py

TODO: Update Prompt definitions.
TODO: REASONING MODE CHECKS FOR REASONING AGENT

"""

import ollama
import pandas as pd
from typing import List
from dataclasses import dataclass, field

from ...utils.settings import settings, AgentBuild
from ._skeleton import Spine
from ._db import PromptBuilder
from .heartbeat import HeartMonitor

prompts = settings.agent.stack.prompts

try:
    NarratePrompt = PromptBuilder(**prompts['story_narrater'])
    ContradictPrompt = PromptBuilder(**prompts['contradict'])
    ExploitPrompt = PromptBuilder(**prompts['exploit'])
    ExplorePrompt = PromptBuilder(**prompts['explore'])
    PlanPrompt = PromptBuilder(**prompts['explore'])
    revisionWorkerPrompt = PromptBuilder(**prompts['revise_tries'])
    questionPrompt = PromptBuilder(**prompts["question"])
except Exception as e:
    raise e

# determines the num of steps before invoking acts
MAX_WINDOW: int = 5
# entire cognitive prompts defined here
COGNITIVE_STATES: list = [
    "narrate",
    "revise",
    "contradict",
    "exploit",
    "explore",
    "plan",
    "question"
]

@dataclass
class ThoughtInterval:
    """ Step Interval defining when to invoke the actions. """

    narrate: int = MAX_WINDOW
    contradict: int = MAX_WINDOW
    question: int = MAX_WINDOW
    revise: int = MAX_WINDOW

@dataclass
class CognitiveAction:
    """ Probabilities influencing the agent's decision-making process in terms of cognitive tasks. Must always sum to 1"""

    _exploit: float = 0.95
    _explore: float = 0.05

    @property
    def exploit(self):
        return self._exploit

    @property
    def explore(self):
        return self._explore

    def _normalize(self):
        import numpy as np
        arr = np.array([self._exploit, self._explore])

        z = arr / np.sum(arr)
        self._exploit = z[0]
        self._explore = z[-1]

    @exploit.setter
    def exploit(self, adjust: float):
        """ Number must be relative to how much you want to increase, not the actual value. """

        self._exploit += adjust
        self._normalize()

    @explore.setter
    def explore(self, adjust: float):
        """ Number must be relative to how much you want to increase, not the actual value. """

        self._explore += adjust
        self._normalize()


class StoryNarrater(Spine, model_name="base", prompt=NarratePrompt):
    """ Story Telling / Summarizing agent. """

    def pre_process(self, obj):
        # TODO:
        # DB preparation - Grab the history summaries for 3 >= historical data
        df = pd.DataFrame(obj.last_narration) # type: ignore
        return {"history": df.to_markdown(index=False)}

    def post_process(self, response: ollama.ChatResponse):
        """ Returns nothing by default."""
        print('Narration finished generating')
        return None

class Contradict(Spine, model_name="base", prompt=ContradictPrompt):
    def pre_process(self, **kwargs):
        return kwargs

class Exploit(Spine, model_name="base", prompt=ExploitPrompt):
    """
    Create samples of exploitive / traditional / rigour methods to solving a particular problem. Default number of samples to 3.
    """

    def pre_process(self, **kwargs):
        pass

    def post_process(self, **kwargs):
        # TODO
        # overrides the base method with decision making
        # agent selects from the N samples given.
        # agent prompts another agent to do so otherwise
        pass

class Explore(Spine, model_name="base", prompt=ExplorePrompt):
    """
    Create samples of explorative / creative methods to a particular problem. Defaults number of samples to 3.
    """
    def pre_process(self, **kwargs):
        return kwargs

    def post_process(self, **kwargs):
        # TODO:
        # overrides the base method with decision making
        # agent selects from the N samples given.
        # agent prompts another agent to do so otherwise
        pass

class Planner(Spine, model_name="base", prompt=PlanPrompt):
    def pre_process(self, **kwargs):
        # TODO: check if require any further changes.
        return kwargs

class RevisionWorker(Spine, model_name="base", prompt=revisionWorkerPrompt):
    def pre_process(self, **kwargs):
        # TODO: check if require any further changes.
        return kwargs

class SherlockHolmes(Spine, model_name="base", prompt=questionPrompt):
    def pre_process(self, **kwargs):
        # TODO: check if require any further changes.
        return kwargs

@dataclass(frozen=True)
class StateAction:
    contradict: Contradict = field(default_factory=Contradict, init=False)
    exploit: Exploit = field(default_factory=Exploit, init=False)
    explore: Explore = field(default_factory=Explore, init=False)
    plan: Planner = field(default_factory=Planner, init=False)
    question: SherlockHolmes = field(default_factory=SherlockHolmes, init=False)

@dataclass(frozen=True)
class StateCondition:
    narrate: StoryNarrater = field(default_factory=StoryNarrater, init=False)
    revise: RevisionWorker = field(default_factory=RevisionWorker, init=False)

class Cognitive(StateAction, StateCondition):
    """
    Call this once during a session.
    Orchestrates the Agent's workflow, reasoning and intent.
    """

    def __init__(
        self,
        client: ollama.Client,
        max_window: int = MAX_WINDOW
    ):
        super().__init__()

        self.client = client
        self.max_window = max_window
        self.actions = CognitiveAction()
        self.conditionInterval = ThoughtInterval()

    def memory(self):
        """ Yields all agent's memory stored in current session. """

        for state_action in COGNITIVE_STATES:
            for hist in getattr(self, state_action).history:
                if isinstance(hist, list) and len(hist) > 0:
                    yield from hist

    @property
    def last_narration(self):
        """ Returns the last narration (or set of narrated summaries). """

        hist = list(self.narrate.h)

        if len(hist) == 0:
            return []

        if 0 < len(hist) <= self.max_window:
            return hist[-1:]
        else:
            return hist[-self.max_window:]

    def run_background(self):
        if len(self.last_narration) // self.max_window == 0:
            # BASE execution function for narrating agent
            # No need to add as this is already stored in the default class wrappers of the processing pipeline.
            self.narrate.run(client=self.client, object=self)

if __name__ == "__main__":
    cognitive = Cognitive(client=None)
    print(cognitive)
    print(cognitive.narrate.history)
    print(list(cognitive.memory()))