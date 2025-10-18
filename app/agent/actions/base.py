"""
app.agent.core.actions

Core actionable tools (functions) for the agent to play with for e.g. sending scripts to the agent's sandbox server.
"""

import requests

from ...utils.settings import settings
from ..core._skeleton import Actuator
from ..core._skeleton import Actuator

agent_core_actions = Actuator('agent_core_actions_demo')

@agent_core_actions
def subtract_two_numbers(a: int, b: int) -> int:
    """Subtract two numbers with agent stage tracking.

    Args:
        a (int): The first number to subtract from.
        b (int): The second number to subtract.

    Returns:
        int: The difference a - b.
    """
    # TODO: REMOVE FUNCTION THIS IS JUST AN EXAMPLE
    result = a - b
    print(f"Computed {a} - {b} = {result}")
    return result

@agent_core_actions
def send_to_sandbox(script: str):
    """
    Send a script to the remote sandbox agent for execution.

    Args:
        script: The source code or instruction string to send.

    Returns:
        dict: JSON response from the sandbox server.

    Raises:
        RuntimeError: If the sandbox request fails or returns an invalid response.
    """
    uri = settings.agent.server.backup_sandbox_server

    try:
        response = requests.post(
            uri,
            json={"payload": script},   # use JSON to be explicit
            timeout=10,
        )
        response.raise_for_status()  # raises for 4xx/5xx
        return response.json()
    except requests.Timeout:
        raise RuntimeError("Sandbox connection timed out.")
    except requests.RequestException as e:
        raise RuntimeError(f"Sandbox request failed: {e}") from e