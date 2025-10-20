"""
app.agent.pipelines.data_cleaning

Contains the workflow construction

Missing:
1. Classify MRA/MNAR/MCAR Decision-space
2. Render the values

"""

import pandas as pd
from dataclasses import dataclass, field

from ...utils.settings import settings
from ..core._skeleton import Spine
from ..core._db import PromptBuilder
from ..core.pipeline import ChainStage

prompts = settings.agent.stack.prompts

try:
    # reviser every k steps
    plannerPrompt = PromptBuilder(**prompts['checklist_planner'])
    # commander / instructor
    commanderPrompt = PromptBuilder(**prompts["the_commander"])
    # code cell script writer
    cellPrompt = PromptBuilder(**prompts['python_coder'])
    # evaluator
    evaluatorPrompt = PromptBuilder(**prompts["cell_evaluator"])
    # response space generator
    responseSpacePrompt = PromptBuilder(**prompts["response_space_generator"])
    # concluding prompt
    responderPrompt = PromptBuilder(**prompts["chatterbox"])
    # backgroundRevisor -- load fron config

except Exception as e:
    raise e

class Planner(Spine, model_name="base", prompt=plannerPrompt):
    def pre_process(self, **kwargs) -> dict:
        return super().pre_process(**kwargs)

class Commander(Spine, model_name="base", prompt=commanderPrompt):
    def pre_process(self, **kwargs) -> dict:
        return super().pre_process(**kwargs)

class PythonCoder(Spine, model_name="base", prompt=cellPrompt):

    def _validate_code_interpreter_inputs(self, session_id: str, python_script: str, *, max_length: int = 4096):

        if not isinstance(session_id, str) or len(session_id) < 33:
            raise ValueError("session_id must be a non-empty string with at least 33 characters.")
        if not isinstance(python_script, str) or not python_script.strip():
            raise ValueError("python_script must be a non-empty Python source string.")
        if len(python_script) > max_length:
            raise ValueError(f"python_script exceeds the {max_length} character safety limit.")

        return dict(session_id=session_id, python_script=python_script)

    def pre_process(self, **kwargs):
        return self._validate_code_interpreter_inputs(session_id=kwargs.get("session_id", ""), python_script=kwargs.get("python_script", ""))

class Evaluator(Spine, model_name="base", prompt=evaluatorPrompt):
    def pre_process(self, **kwargs) -> dict:
        return super().pre_process(**kwargs)

class ResponseSpaceGenerator(Spine, model_name="base", prompt=responseSpacePrompt):
    def pre_process(self, **kwargs) -> dict:
        return super().pre_process(**kwargs)

class Responder(Spine, model_name="base", prompt=responderPrompt):
    def pre_process(self, **kwargs) -> dict:
        return super().pre_process(**kwargs)

# Planner -> [Commander -> Python -> Evaluator -> ResponseSpaceGenerator -> Responder <-> Commander] x 2 - ReviseWorker -- from cognitive ?

@dataclass(frozen=True)
class Cycle:
    commander: Commander = field(default_factory=Commander)
    programmer: PythonCoder = field(default_factory=PythonCoder)
    evaluator: Evaluator = field(default_factory=Evaluator)
    responseSpace: ResponseSpaceGenerator = field(default_factory=ResponseSpaceGenerator)
    responder: Responder = field(default_factory=Responder)

@dataclass(frozen=True)
class Feedback:
    planner: Planner = field(default_factory=Planner)
    reviseWorker = None

class DataSender(ChainStage):
    def forward(self, session):
        # TODO setup the data upload to hf with session id key . Agent State
        return super().forward(session)

    def validate_stage_output(self, session):
        return super().validate_stage_output(session)

class ThoughtCycle(ChainStage, Cycle):
    def forward(self, session):
        # TODO: RUN JUPYTER KERNEL CELL

        from ..core._skeleton import ActionSpace

        notebook = ActionSpace.get_action(workflow_name="jupyter-notebook", function_name="JupyterNotebook")

        code_instruct = self.commander.run(session.history)
        code_block = self.programmer.run(**{"session_id": session.id, "python_script": code_instruct})

        logs = []
        for item in notebook.run_code(code_block):
            logs.append(item)

        return super().forward(session)

    def validate_stage_output(self, session):
        return super().validate_stage_output(session)

class DataProcessingPipeline(Feedback):
    def __init__(self):
        super().__init__()
        self.reset()

    def reset(self):
        if not hasattr(self, 'pipe'):
            self.pipe = DataSender()

        cycle = ThoughtCycle()
        self.pipe.set_next_stage(cycle)

    def run(self, **kwargs):

        try:
            # ChainStage instances are not callable; invoke the forward method and return its output.
            output = self.pipe.forward(**kwargs)
            return output

        except Exception as e:
            raise e
        finally:
            self.reset()