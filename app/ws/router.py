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
from app.db.session import async_session_factory
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

    try:
        async with async_session_factory() as session:
            user = await authenticate_ws_token(token, session)
            user_id = user.id
            user_role = user.role
    except UnauthorizedError as exc:
        await ws.close(code=4001, reason=str(exc))
        return
    except Exception as exc:
        logger.warning("WS auth error before accept: %s", exc)
        await ws.close(code=1011, reason="WebSocket authentication failed")
        return

    await ws.accept()

    room_keys = [f"user:{user_id}"]
    tenant_id = extract_tenant_id(token)
    if tenant_id is not None:
        room_keys.append(f"tenant:{tenant_id}")

    ws_manager.connect(ws, *room_keys)
    logger.info(
        "WS connected user_id=%d role=%s rooms=%s",
        user_id,
        user_role,
        room_keys,
    )

    try:
        await _handle_connection(ws, user_id)
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.warning("WS error user_id=%d: %s", user_id, exc)
    finally:
        ws_manager.disconnect(ws)
        logger.info("WS disconnected user_id=%d", user_id)


async def _handle_connection(ws: WebSocket, user_id: int) -> None:
    """Handle heartbeat and incoming messages for a single connection."""
    pong_received = asyncio.Event()
    pong_received.set()  # initially alive
    heartbeat_task = asyncio.create_task(_heartbeat_loop(ws, user_id, pong_received))
    try:
        while True:
            data = await ws.receive_json()
            msg_type: str = data.get("type", "")

            if msg_type == "pong":
                pong_received.set()
            elif msg_type == "ping":
                await ws.send_json(build_message("pong", {}))
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


async def _heartbeat_loop(ws: WebSocket, user_id: int, pong_received: asyncio.Event) -> None:
    """Send ping every HEARTBEAT_INTERVAL seconds and close on pong timeout."""
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL)
        pong_received.clear()
        try:
            await ws.send_json(build_message("ping", {}))
        except Exception:
            break
        try:
            await asyncio.wait_for(pong_received.wait(), timeout=PONG_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning("WS pong timeout user_id=%d — closing connection", user_id)
            try:
                await ws.close(code=1001, reason="Pong timeout")
            except Exception:
                pass
            break
