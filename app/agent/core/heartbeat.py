"""
app/agent/core/heartbeat.py

"""

from datetime import datetime
from dataclasses import dataclass, field

AGENT_STATE = {
    'idle': 'idle',
    'working': 'working'
}

@dataclass
class AgentStatus:
    alive: bool = field(default=False)
    state: str | None = field(default=None, init=False)
    timestamp: datetime = field(init=False, default_factory=datetime.now)

    def __post_init__(self):
        if self.alive is False and self.state:
            raise ValueError(f'Agent is not alive but state shows the agent is {self.state}. Revise the setup architecture.')

class HeartMonitor(AgentStatus):
    @property
    def is_alive(self):
        return self.alive

    @property
    def last_ping(self):
        return self.timestamp.isoformat()

    def set_alive(self, alive: bool):
        self.alive = alive
        self.timestamp = datetime.now()