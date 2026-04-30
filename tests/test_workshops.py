"""Tests de integración — Talleres (workshops)."""

import pytest
from httpx import AsyncClient

from tests.conftest import _register_and_login, _uid


def _workshop_payload(uid: str, admin_user_id: int) -> dict:
    return {
        "name": f"Taller {uid}",
        "description": "Taller de prueba",
        "phone": "77712345",
        "email": f"taller_{uid}@test.com",
        "address": "Av. Test 123",
        "latitude": -17.78,
        "longitude": -63.18,
        "has_tow": True,
        "is_24_hours": False,
        "admin_user_id": admin_user_id,
    }


@pytest.mark.asyncio
async def test_create_workshop_as_admin(client: AsyncClient):
    uid = _uid()
    admin = await _register_and_login(client, "ADMIN_TALLER", uid)
    resp = await client.post(
        "/api/v1/workshops",
        json=_workshop_payload(uid, admin["user_id"]),
        headers=admin["headers"],
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == f"Taller {uid}"
    assert data["status"] == "ACTIVO"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_workshop_forbidden_for_cliente(client: AsyncClient):
    uid = _uid()
    cliente = await _register_and_login(client, "CLIENTE", uid)
    resp = await client.post(
        "/api/v1/workshops",
        json=_workshop_payload(uid, cliente["user_id"]),
        headers=cliente["headers"],
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_workshop_requires_auth(client: AsyncClient):
    uid = _uid()
    resp = await client.post(
        "/api/v1/workshops",
        json={"name": "No Auth", "admin_user_id": 1},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_workshop(client: AsyncClient):
    uid = _uid()
    admin = await _register_and_login(client, "ADMIN_TALLER", uid)
    cliente = await _register_and_login(client, "CLIENTE", uid)
    create = await client.post(
        "/api/v1/workshops",
        json=_workshop_payload(uid, admin["user_id"]),
        headers=admin["headers"],
    )
    workshop_id = create.json()["id"]

    resp = await client.get(f"/api/v1/workshops/{workshop_id}", headers=cliente["headers"])
    assert resp.status_code == 200
    assert resp.json()["id"] == workshop_id


@pytest.mark.asyncio
async def test_get_workshop_not_found(client: AsyncClient):
    uid = _uid()
    cliente = await _register_and_login(client, "CLIENTE", uid)
    resp = await client.get("/api/v1/workshops/999999", headers=cliente["headers"])
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_workshops(client: AsyncClient):
    uid = _uid()
    cliente = await _register_and_login(client, "CLIENTE", uid)
    resp = await client.get("/api/v1/workshops", headers=cliente["headers"])
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_update_workshop(client: AsyncClient):
    uid = _uid()
    admin = await _register_and_login(client, "ADMIN_TALLER", uid)
    create = await client.post(
        "/api/v1/workshops",
        json=_workshop_payload(uid, admin["user_id"]),
        headers=admin["headers"],
    )
    workshop_id = create.json()["id"]

    resp = await client.patch(
        f"/api/v1/workshops/{workshop_id}",
        json={"description": "Descripcion actualizada"},
        headers=admin["headers"],
    )
    assert resp.status_code == 200
    assert resp.json()["description"] == "Descripcion actualizada"
