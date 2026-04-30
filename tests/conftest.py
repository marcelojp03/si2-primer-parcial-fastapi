import uuid
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app

BASE = "http://test"


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE) as ac:
        yield ac


def _uid() -> str:
    return uuid.uuid4().hex[:8]


async def _register_and_login(ac: AsyncClient, role: str, uid: str) -> dict:
    """Helper: register user and return headers + user_id."""
    email = f"{role.lower()}_{uid}@test.com"
    password = "testpass123"
    full_name = f"Test {role.capitalize()}"
    await ac.post(
        "/api/v1/auth/register",
        json={"full_name": full_name, "email": email, "password": password, "role": role},
    )
    resp = await ac.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    me = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    return {
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "user_id": me.json()["id"],
        "email": email,
    }
