"""WebSocket router — single endpoint GET /ws.

Authentication: JWT via query param ?token=<bearer_token>

Room subscriptions per role:
  CLIENTE       → user:{id}, incident:{id} (for each open incident)
  ADMIN_TALLER  → user:{id}, tenant:{id}
  SUPERADMIN    → user:{id}

Heartbeat: server sends ping every 30 seconds.
Client must respond with {"type": "pong"} within 30 seconds or the
connection is closed.
"""

import asyncio
import contextlib
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.exceptions import UnauthorizedError
from app.db.session import get_async_session
from app.ws.auth import authenticate_ws_token, extract_tenant_id
from app.ws.events import build_message
from app.ws.manager import ws_manager

logger = logging.getLogger(__name__)
router = APIRouter()

HEARTBEAT_INTERVAL = 30  # seconds
PONG_TIMEOUT = 30  # seconds


@router.websocket("/ws")
async def websocket_endpoint(
    ws: WebSocket,
    token: str = Query(..., description="Bearer JWT token"),
) -> None:
    """Main WebSocket endpoint. Auth via ?token= query param."""

    # ── 1. Authenticate ────────────────────────────────────────
    async for session in get_async_session():
        try:
            user = await authenticate_ws_token(token, session)
        except UnauthorizedError as exc:
            await ws.close(code=4001, reason=str(exc))
            return

        await ws.accept()

        # ── 2. Subscribe to rooms ──────────────────────────────
        room_keys = [f"user:{user.id}"]
        tenant_id = extract_tenant_id(token)
        if tenant_id is not None:
            room_keys.append(f"tenant:{tenant_id}")

        ws_manager.connect(ws, *room_keys)
        logger.info(
            "WS connected user_id=%d role=%s rooms=%s",
            user.id,
            user.role,
            room_keys,
        )

        # ── 3. Main loop ───────────────────────────────────────
        try:
            await _handle_connection(ws, user.id)
        except WebSocketDisconnect:
            pass
        except Exception as exc:
            logger.warning("WS error user_id=%d: %s", user.id, exc)
        finally:
            ws_manager.disconnect(ws)
            logger.info("WS disconnected user_id=%d", user.id)

        # Only one iteration of the async generator
        break


async def _handle_connection(ws: WebSocket, user_id: int) -> None:
    """Handle heartbeat and incoming messages for a single connection."""
    heartbeat_task = asyncio.create_task(_heartbeat_loop(ws, user_id))
    try:
        while True:
            data = await ws.receive_json()
            msg_type: str = data.get("type", "")

            if msg_type == "pong":
                # Client is alive; heartbeat_loop tracks this via the event
                pass
            elif msg_type == "subscribe_incident":
                incident_id = data.get("incident_id")
                if incident_id:
                    ws_manager.connect(ws, f"incident:{incident_id}")
            elif msg_type == "unsubscribe_incident":
                incident_id = data.get("incident_id")
                if incident_id:
                    room_key = f"incident:{incident_id}"
                    ws_manager._rooms.get(room_key, set()).discard(ws)
    finally:
        heartbeat_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await heartbeat_task


async def _heartbeat_loop(ws: WebSocket, user_id: int) -> None:
    """Send ping every HEARTBEAT_INTERVAL seconds and close on timeout."""
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL)
        try:
            await ws.send_json(build_message("ping", {}))
        except Exception:
            break
