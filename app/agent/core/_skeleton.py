"""
app.agent.core._skeleton

Defines the base framework for constructing agents.

Base classes
- Spine: Default agent builder
- Actuator: Default toolkit

"""

import ollama
import inspect
import logging
import docstring_parser
from functools import wraps
from abc import ABC, abstractmethod
from typing import List, get_type_hints, Any

from ...utils.settings import settings
from ._db import (
    SpineListener,
    InputContent,
    PromptBuilder
)

logger = logging.getLogger("fastapi")

class Spine(ABC):
    """
    Base Framework of instruct agents. Must declare the pre/post processors otherwise defaults to default callers. This is not supposed to be imported directly or store chat sessions, and is intended to be used as a parent class for building agents.
    """

    registry: list[str] = []

    def __init__(self):
        self.current = None
        self.history: List[SpineListener] = []

    @abstractmethod
    def pre_process(self, **kwargs) -> dict:
        """ Define pre-processing method in subclass. This can be used to engineer user-inputs or digest raw / streaming reports instead of defining additional features. """
        pass

    def post_process(self, output: ollama.ChatResponse) -> str:
        """ Default post-processing method for generative llm. """

        return output.message.get('content')

    @property
    def h(self):
        """ Yield the LLM's output messages only. """
        if len(self.history) > 0:
            for item in self.history:
                if isinstance(item, SpineListener) and isinstance(item.output, ollama.ChatResponse):
                    yield item.output.message.content

    def add(self, listener: SpineListener):
        self.history.append(listener)

    def _input_listener(self, message: list, **kwargs):
        """ Model input message listener / decorator. """

        if not hasattr(self, 'current'):
            raise AttributeError("Failed to locate `current` attribute in instance while calling _input_listener. Pls revise dataclass.")

        if self.current is not None:
            raise ValueError('Temporary holder, `current` expected to be None before calling another agent. Please reset current workspace')

        self.current = SpineListener(function=self.__class__.__qualname__)
        self.current.input = InputContent(raw_input=kwargs, message=message)

    def _output_listener(self, response: ollama.ChatResponse):
        """ Model output response listener / decorator. """

        if not hasattr(self, 'current'):
            raise AttributeError(f"_output_listener: Failed to locate `current` attribute in instance while calling _output_listener. Pls revise dataclass.")

        if self.current is None:
            raise ValueError('Expected temporary content holder `current` attribute to be of SpineListener dataclass but is None. Pls revise build.')

        self.current.output = response
        self.add(self.current)
        self.current = None

    def run(self, client: ollama.Client, **kwargs):
        """ Main caller function. """

        input_kwargs = self.pre_process(**kwargs)
        msg = self.prompt.build_message(**input_kwargs)
        self._input_listener(msg, **kwargs)

        #response: ollama.ChatResponse = await client.chat(
        #    model=cls.model_id,
        #    messages=msg
        #)

        # TODO: UPDATE
        logger.warning("calling Mock ollama since in debug mode.")
        response = ollama.ChatResponse(
            model="yellow",
            message=ollama.Message(role="user", content="hello")
        )

        self._output_listener(response)
        return self.post_process(response)

    @classmethod
    def __init_subclass__(cls, model_name: str, prompt: PromptBuilder, **kwargs):
        if model_name not in settings.agent.stack.model_catalogue:
            raise ValueError(f"Invalud {model_name} entered. Please update the model catalogue loaded from `agent/_config/genai.yaml` or requested model name. ")

        cls.prompt: PromptBuilder = prompt
        cls.model_name: str = model_name
        cls.model_id: str = settings.agent.stack.model_catalogue.get(cls.model_name, {}).model_id

        if cls.__name__ not in Spine.registry:
            Spine.registry.append(cls.__name__)

        return super().__init_subclass__(**kwargs)

class Actuator:
    """Class-based decorator that registers functions as agent tools."""

    workflow: dict[str, dict] = {}
    _action_space: dict[str, dict[str, Any]] = {}

    def __init__(self, workflow: str):

        if workflow not in Actuator.workflow:
            print(f'First time registering {workflow}')
            Actuator.workflow[workflow] = {}
            Actuator._action_space[workflow] = {}

        self.current_workflow = workflow

    @classmethod
    def list_workflows(cls):
        return list(Actuator.workflow)

    @classmethod
    def action_space(cls, workflow_name: str):
        """ For agent to select function tools globally from any workflow. """

        if workflow_name not in Actuator._action_space:
            raise ValueError(f'Requested {workflow_name} does not exist in the Actuator. Please check if this function is defined otherwise revise requested tool.')

        return Actuator._action_space[workflow_name]

    @classmethod
    def get_action(cls, workflow_name: str, function_name: str):
        """ Returns the requested function. This is for the agent to use to call action by itself. """

        actions = cls.action_space(workflow_name)

        if function_name not in actions:
            raise ValueError(f"Function {function_name} is not registry as a tool. Please use @agent_toolbox decorator.")

        return actions[function_name]

    @classmethod
    def get_meta(cls, workflow_name: str, function_name: str):
        """ Returns the requested function. This is for the agent to use to call action by itself. """

        if workflow_name not in Actuator.workflow or function_name not in Actuator.workflow[workflow_name]:
            raise ValueError(f"Function {function_name} is not registry as a tool. Please use class decorator detailed in examples from doc.")

        return Actuator.workflow[workflow_name].get(function_name, {})

    def __call__(self, func):
        """Called when used as a decorator."""

        tool_name = func.__name__

        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        doc = func.__doc__ or "Unknown"
        parsed_doc = docstring_parser.parse(doc)

        # Map docstring arg descriptions
        doc_args = {p.arg_name: p.description for p in parsed_doc.params}

        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            annotation = type_hints.get(param_name, str)
            if annotation in (int, "int"):
                arg_type = "integer"
            elif annotation in (float, "float"):
                arg_type = "number"
            elif annotation in (bool, "bool"):
                arg_type = "boolean"
            else:
                arg_type = "string"

            if param.default == inspect._empty:
                required.append(param_name)

            desc = doc_args.get(param_name, f"Argument `{param_name}` of type {arg_type}")
            properties[param_name] = {"type": arg_type, "description": desc}

        # Register function metadata and callable
        Actuator.workflow[self.current_workflow][tool_name] = {
            "type": "function",
            "function": {
                "name": tool_name,
                "callable": func,
                "description": parsed_doc.short_description or doc.strip(),
                "parameters": {
                    "type": "object",
                    "required": required,
                    "properties": properties,
                },
            },
        }
        Actuator._action_space[self.current_workflow][tool_name] = func
        print(f"[PROG ACTION SPACE] ADDED {tool_name} TO WORKFLOW: `{self.current_workflow}`")

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

class Outbound(ABC):
    @abstractmethod
    def setup_outbound(self, **kwargs):
        """ Default setup if external server is not configured."""
        return kwargs

    @abstractmethod
    def ping(self, **kwargs):
        """ Runs checks to ensure the server is alive. """
        return kwargs

    @abstractmethod
    def inference(self, **kwargs):
        """ Invoke message to outbound / external servers. """
        return kwargs

if __name__ == "__main__":
    print("Registered agents sharing the same spine:\n", Spine.registry)
    # NOTE
    # To view all Registered agents:
    # Spine.registry
    # To view all class based stored variables like prompt, model_name or id:
    # *Subclass name*.prompt