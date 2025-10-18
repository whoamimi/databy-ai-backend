"""
app.api.manager.connection

Connection Manager Handler

"""

import asyncio
from typing import List
from .schemas import Room, Output

MAX_ROOMS: int = 50
SESSION_TIMEOUT_IDLE: int = 1200

def mock_invoker(inputs: str):
    print(f"User input: {inputs}")
    return Output(role="assistant", content="Hello I am good too thanks!", mood="idle")

class ConnectionManager:
    """Manages active WebSocket connections."""

    rooms: dict = {}
    total_active: int = 0

    def __init__(self, max_rooms: int = MAX_ROOMS, session_timeout: int = SESSION_TIMEOUT_IDLE):

        self.max_rooms = max_rooms
        self.session_timeout = session_timeout
        self.lock = asyncio.Lock()

    async def add(self, room: Room):

        # TODO: CHECK max users and raise
        room_id = str(room.id)
        if room_id in ConnectionManager.rooms:
            print(f"Streaming Session already exists: {room.id}")
        else:
            print(f"Adding new room: {room_id}")
            ConnectionManager.rooms[room_id] = room
            ConnectionManager.total_active += 1

    async def remove(self, room: Room):
        # TODO: add idle state
        room_id = str(room.id)

        if room_id in ConnectionManager.rooms:
            del ConnectionManager.rooms[room_id]

            if ConnectionManager.total_active > 0:
                ConnectionManager.total_active -= 1

        print(f"Disconnected from room {room.id}")

    async def get_room(self, room_id: str):
        async with self.lock:
            if room := ConnectionManager.rooms.get(room_id, None)
                if room.event is None:
                    ConnectionManager.rooms[room_id].event = asyncio.Event()
            else:
                raise ValueError

            return ConnectionManager.rooms[room_id]
