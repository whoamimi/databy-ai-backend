"""
app/agent/core/_db.py

Contains data handlers for base classes defined in app.agent.core._skeleton.py

"""

import ollama
from datetime import datetime
from dataclasses import dataclass, field

from typing import (
    Callable,
    Any
)

@dataclass
class InputContent:
    message: list
    raw_input: dict = field(repr=False)
    input_timestamp: datetime = field(init=False, default=datetime.now())

@dataclass
class SpineListener:
    function: str
    input: InputContent = field(init=False)
    output: ollama.ChatResponse | Any = field(init=False)
    created_timestamp: datetime = field(init=False, default=datetime.now())

@dataclass
class Toolkit:
    function: Callable
    workflow_name: str = field(default="body")
    function_name: str = field(default="")
    meta: dict = field(init=False)

    def __post_init__(self):
        # TODO: ADD THIS TO THE PRE-PROCESSING OF THE PROMPTBUILDER
        # GETS ACTION TOOL and assign to the function
        # action = ActionSpace.action(workflow_name=self.workflow_name, function_name=self.function.__name__)
        # ASSIGNS META DESCRIPTORS OF THE FUNCTION TO PASS TO THE AGENT
        from ._skeleton import ActionSpace

        self.meta = ActionSpace.get_meta(self.workflow_name, self.function.__name__)

@dataclass
class PromptBuilder:
    prompt: str
    input_template: str | None = None
    tools: list[Toolkit] = field(default_factory=list)

    def build_message(self, **kwargs):
        """Fill in the input template with kwargs if provided, otherwise return kwargs as str."""

        if self.input_template:
            output = {"role": "user", "content": self.input_template.format(**kwargs)}
        else:

            try:
                system_prompt = self.prompt.format(**kwargs)
                output = {
                    "role": "system",
                    "content": system_prompt
                }
            except (ValueError, KeyError, TypeError):
                output = {
                    "role": "user",
                    "content": str(kwargs)
                }
            except Exception as e:
                raise e

        return [output]
