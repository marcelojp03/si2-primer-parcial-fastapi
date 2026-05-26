"""WebSocket connection manager.

Manages rooms (channels) keyed by string identifiers:
  - incident:{id}   → all parties following an incident
  - tenant:{id}     → ADMIN_TALLER connections scoped to a tenant
  - user:{id}       → single-user personal channel

NOTE: This is a single-process in-memory implementation.
For horizontal scaling, replace with Redis Pub/Sub.
"""

import asyncio
import logging
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        # room_key -> set of WebSocket connections
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)
        # ws -> set of room keys the connection is subscribed to
        self._subscriptions: dict[WebSocket, set[str]] = defaultdict(set)

    # ── Connection lifecycle ───────────────────────────────────

    def connect(self, ws: WebSocket, *room_keys: str) -> None:
        """Register a WebSocket in one or more rooms."""
        for key in room_keys:
            self._rooms[key].add(ws)
            self._subscriptions[ws].add(key)
        logger.debug("WS connect: rooms=%s total_connections=%d", room_keys, len(self._subscriptions))

    def disconnect(self, ws: WebSocket) -> None:
        """Remove a WebSocket from all rooms it was subscribed to."""
        for key in self._subscriptions.pop(ws, set()):
            self._rooms[key].discard(ws)
            if not self._rooms[key]:
                del self._rooms[key]
        logger.debug("WS disconnect: remaining_connections=%d", len(self._subscriptions))

    # ── Sending ────────────────────────────────────────────────

    async def send_to_connection(self, ws: WebSocket, message: dict) -> None:
        """Send a message to a single connection. Silently removes dead connections."""
        try:
            await ws.send_json(message)
        except Exception:
            self.disconnect(ws)

    async def broadcast_to_room(self, room_key: str, message: dict) -> None:
        """Broadcast a message to all connections in a room."""
        targets = list(self._rooms.get(room_key, set()))
        if not targets:
            return
        await asyncio.gather(
            *(self.send_to_connection(ws, message) for ws in targets),
            return_exceptions=True,
        )

    async def send_to_user(self, user_id: int, message: dict) -> None:
        """Send a message to a specific user's personal channel."""
        await self.broadcast_to_room(f"user:{user_id}", message)

    async def send_to_incident(self, incident_id: int, message: dict) -> None:
        """Broadcast to everyone subscribed to an incident channel."""
        await self.broadcast_to_room(f"incident:{incident_id}", message)

    async def send_to_tenant(self, tenant_id: int, message: dict) -> None:
        """Broadcast to all ADMIN_TALLER connections for a tenant."""
        await self.broadcast_to_room(f"tenant:{tenant_id}", message)

    # ── Diagnostics ────────────────────────────────────────────

    @property
    def connection_count(self) -> int:
        return len(self._subscriptions)

    def room_sizes(self) -> dict[str, int]:
        return {k: len(v) for k, v in self._rooms.items() if v}


# Singleton — imported by the router and by services that emit events.
ws_manager = ConnectionManager()
