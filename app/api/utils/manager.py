"""
app.api.manager.connection

Connection Manager Handler

TODO: remove this before i remove myself

"""
import asyncio
import logging
from ...agent.main import GabyWindow

logger = logging.getLogger("uvicorn")

MAX_ROOMS = 50
SESSION_TIMEOUT_IDLE = 1200  # 20 min

class ConnectionManager:
    """Manages active SSE/WebSocket connections."""

    rooms: dict[str, GabyWindow] = {}
    total_active: int = 0

    def __init__(self, max_rooms: int = MAX_ROOMS, session_timeout: int = SESSION_TIMEOUT_IDLE):
        self.max_rooms = max_rooms
        self.session_timeout = session_timeout
        self.lock = asyncio.Lock()

    # --------------------------------------------------
    # Room lifecycle
    # --------------------------------------------------
    async def add(self, session: GabyWindow):
        """Add a new active session."""
        room_id = str(session.id)

        async with self.lock:
            if room_id in self.rooms:
                logger.info(f"Session {room_id} already exists.")
                return

            session.event = asyncio.Event()
            self.rooms[room_id] = session
            self.total_active += 1

            # Start idle countdown
            session.countdown_task = asyncio.create_task(self._countdown(room_id))
            logger.info(f"Room {room_id} added and countdown started ({self.session_timeout}s).")

    async def remove(self, room_id: str):
        """Remove a room immediately and cancel its countdown."""

        async with self.lock:
            if room_id not in self.rooms:
                logger.warning(f"Attempt to remove non-existent room {room_id}")
                return

            room = self.rooms[room_id]

            # Cancel countdown
            if room.countdown_task and not room.countdown_task.done():
                room.countdown_task.cancel()
                try:
                    await room.countdown_task
                except asyncio.CancelledError:
                    pass

            # End active streams
            if room.event:
                room.event.set()

            del self.rooms[room_id]
            self.total_active = max(0, self.total_active - 1)

            logger.info(f"Room {room_id} removed and countdown cancelled.")

    async def get_room(self, room_id: str) -> GabyWindow:
        """Retrieve an active room safely."""
        async with self.lock:
            if room := self.rooms.get(room_id):
                return room
            raise ValueError(f"Room {room_id} not found")


    async def _countdown(self, room_id: str):
        """Background coroutine that expires a room after idle timeout."""
        try:
            logger.debug(f"[countdown] Starting {self.session_timeout}s timer for {room_id}")
            await asyncio.sleep(self.session_timeout)

            if room_id in self.rooms:
                logger.info(f"[countdown] Room {room_id} idle timeout reached. Removing.")
                await self.remove(room_id)

        except asyncio.CancelledError:
            logger.debug(f"[countdown] Cancelled countdown for {room_id}")
        except Exception as e:
            logger.error(f"[countdown] Error for {room_id}: {e}")

    async def reset_countdown(self, room_id: str):
        """Reset countdown timer due to user activity."""
        async with self.lock:
            if room_id not in self.rooms:
                logger.warning(f"Cannot reset countdown for non-existent room {room_id}")
                return

            room = self.rooms[room_id]

            # Cancel existing timer
            if room.countdown_task and not room.countdown_task.done():
                room.countdown_task.cancel()
                try:
                    await room.countdown_task
                except asyncio.CancelledError:
                    pass

            # Start new timer
            room.countdown_task = asyncio.create_task(self._countdown(room_id))
            logger.info(f"[countdown] Reset countdown for room {room_id}.")