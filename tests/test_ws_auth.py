"""Tests para autenticación WebSocket (CU: WS auth)."""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from starlette.testclient import TestClient

from app.main import app

BASE = "http://test"


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE) as ac:
        yield ac


async def _login(ac: AsyncClient, email: str, password: str) -> str:
    resp = await ac.post("/api/v1/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


async def _register_login(ac: AsyncClient, uid: str) -> str:
    email = f"wstest_{uid}@test.com"
    await ac.post(
        "/api/v1/auth/register",
        json={"full_name": "WS User", "email": email, "password": "pass1234", "role": "CLIENTE"},
    )
    return await _login(ac, email, "pass1234")


class TestWSAuth:
    """Verifica que el endpoint WS require token válido."""

    def test_ws_no_token_rejected(self):
        """Sin token debe rechazarse con 403."""
        with TestClient(app) as tc:
            with pytest.raises(Exception):
                # Starlette TestClient raises WebSocketDisconnect or similar on 403
                with tc.websocket_connect("/ws") as ws:
                    ws.receive_json()

    def test_ws_invalid_token_rejected(self):
        """Token inválido debe rechazarse."""
        with TestClient(app) as tc:
            with pytest.raises(Exception):
                with tc.websocket_connect("/ws?token=invalid.token.here") as ws:
                    ws.receive_json()

    @pytest.mark.asyncio
    async def test_ws_valid_token_accepted(self, client: AsyncClient):
        """Token válido debe permitir conectar y recibir el ping inicial."""
        uid = uuid.uuid4().hex[:8]
        token = await _register_login(client, uid)

        with TestClient(app) as tc:
            with tc.websocket_connect(f"/ws?token={token}") as ws:
                # El router envía heartbeat cada 30s, pero debemos poder conectar
                # Enviamos un ping y esperamos pong
                ws.send_json({"type": "ping"})
                msg = ws.receive_json()
                assert msg["type"] == "pong"
