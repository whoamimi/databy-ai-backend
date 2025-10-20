"""
app.agent.core.actions

Core actionable tools (functions) for the agent to play with for e.g. sending scripts to the agent's sandbox server.
"""

from dataclasses import dataclass, field
from jupyter_client import KernelManager

from ...utils.settings import settings
from ..core._skeleton import ActionSpace

sandbox_actions = ActionSpace('jupyter-notebook')

MAX_TIMEOUT = 5
EXC_STATES = ("IDLE", "RUNNING", "COMPLETE")

@dataclass
class JupyterResponse:
    header: dict
    msg_id: str
    msg_type: str
    metadata: dict
    content: dict[str, str]
    execution_state: str = field(init=False)

    def __post_init__(self):
        if "execution_state" in self.content:
            self.execution_state = self.content.get("execution_state", "")
        if "execution_count" in self.content:
            self.execution_state = "WORKING"
        if "name" in self.content and "text" in self.content:
            self.execution_state = "COMPLETE"

        self.execution_state = self.execution_state.upper()

@sandbox_actions
class JupyterNotebook:
    def __init__(self, max_timeout: int = MAX_TIMEOUT):
        self.max_timeout = max_timeout

    def start(self):
        self.km = KernelManager()
        self.km.start_kernel()
        self.kc = self.km.client()
        self.kc.start_channels()

    def stop(self):
        self.kc.stop_channels()
        self.km.shutdown_kernel(now=True)

    def run_code(self, cell_block: str):

        self.start()

        msg_id: str = self.kc.execute(cell_block)
        n = 0

        while True:
            output = self.kc.get_iopub_msg(timeout=self.max_timeout)

            if output and isinstance(output, dict):
                response = JupyterResponse(
                    header=output.get("header", {}),
                    msg_id=output.get("msg_id", ""),
                    msg_type=output.get("msg_type", ""),
                    metadata=output.get("metadata", {}),
                    content=output.get("content", {})
                )
                yield response

                if n > 1 and response.execution_state == EXC_STATES[0]:
                    break

                n += 1

        self.stop()

