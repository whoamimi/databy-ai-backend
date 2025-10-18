"""
app/agent/core/heartbeat.py

TODO:
- run checks

"""

from datetime import datetime
from dataclasses import dataclass, field

AGENT_STATE = {
    'idle': 'idle',
    'working': 'working'
}

@dataclass
class AgentStatus:
    alive: bool = field(default=True)
    state: str = field(default="idle", init=False)
    timestamp: datetime = field(init=False, default_factory=datetime.now)

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