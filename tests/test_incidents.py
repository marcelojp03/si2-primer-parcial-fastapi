"""Tests de integración — Incidentes (con filtros)."""

import pytest
from httpx import AsyncClient

from tests.conftest import _register_and_login, _uid


def _incident_payload(vehicle_id: int, client_user_id: int, title: str = "Incidente de prueba") -> dict:
    return {
        "vehicle_id": vehicle_id,
        "client_user_id": client_user_id,
        "title": title,
        "description_text": "Descripcion del incidente de prueba",
        "reference_address": "Calle Falsa 123",
        "latitude": -17.783,
        "longitude": -63.182,
        "requires_tow": False,
    }


async def _create_vehicle(ac: AsyncClient, cliente: dict, uid: str) -> int:
    resp = await ac.post(
        "/api/v1/vehicles",
        json={
            "plate": f"IN{uid[:6].upper()}",
            "brand": "Toyota",
            "model": "Corolla",
            "manufacture_year": 2022,
            "color": "Blanco",
            "user_id": cliente["user_id"],
        },
        headers=cliente["headers"],
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_incident(client: AsyncClient):
    uid = _uid()
    cliente = await _register_and_login(client, "CLIENTE", uid)
    vehicle_id = await _create_vehicle(client, cliente, uid)
    resp = await client.post(
        "/api/v1/incidents",
        json=_incident_payload(vehicle_id, cliente["user_id"]),
        headers=cliente["headers"],
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["vehicle_id"] == vehicle_id
    assert data["client_user_id"] == cliente["user_id"]
    assert data["incident_status_id"] is not None
    assert "id" in data


@pytest.mark.asyncio
async def test_create_incident_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/api/v1/incidents",
        json=_incident_payload(1, 1),
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_incident_forbidden_for_admin(client: AsyncClient):
    uid = _uid()
    admin = await _register_and_login(client, "ADMIN_TALLER", uid)
    resp = await client.post(
        "/api/v1/incidents",
        json=_incident_payload(1, 1),
        headers=admin["headers"],
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_incident(client: AsyncClient):
    uid = _uid()
    cliente = await _register_and_login(client, "CLIENTE", uid)
    vehicle_id = await _create_vehicle(client, cliente, uid)
    create = await client.post(
        "/api/v1/incidents",
        json=_incident_payload(vehicle_id, cliente["user_id"], "Incidente GET"),
        headers=cliente["headers"],
    )
    incident_id = create.json()["id"]
    resp = await client.get(f"/api/v1/incidents/{incident_id}", headers=cliente["headers"])
    assert resp.status_code == 200
    assert resp.json()["id"] == incident_id


@pytest.mark.asyncio
async def test_get_incident_not_found(client: AsyncClient):
    uid = _uid()
    cliente = await _register_and_login(client, "CLIENTE", uid)
    resp = await client.get("/api/v1/incidents/999999", headers=cliente["headers"])
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_incidents(client: AsyncClient):
    uid = _uid()
    cliente = await _register_and_login(client, "CLIENTE", uid)
    resp = await client.get("/api/v1/incidents", headers=cliente["headers"])
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_list_incidents_filter_by_client(client: AsyncClient):
    uid = _uid()
    cliente = await _register_and_login(client, "CLIENTE", uid)
    vehicle_id = await _create_vehicle(client, cliente, uid)
    await client.post(
        "/api/v1/incidents",
        json=_incident_payload(vehicle_id, cliente["user_id"], "Filtro cliente"),
        headers=cliente["headers"],
    )
    resp = await client.get(
        f"/api/v1/incidents?client_user_id={cliente['user_id']}",
        headers=cliente["headers"],
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert all(inc["client_user_id"] == cliente["user_id"] for inc in data)


@pytest.mark.asyncio
async def test_list_incidents_filter_by_status(client: AsyncClient):
    uid = _uid()
    cliente = await _register_and_login(client, "CLIENTE", uid)
    vehicle_id = await _create_vehicle(client, cliente, uid)
    create = await client.post(
        "/api/v1/incidents",
        json=_incident_payload(vehicle_id, cliente["user_id"], "Filtro status"),
        headers=cliente["headers"],
    )
    status_id = create.json()["incident_status_id"]
    resp = await client.get(
        f"/api/v1/incidents?status_id={status_id}",
        headers=cliente["headers"],
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert all(inc["incident_status_id"] == status_id for inc in data)


@pytest.mark.asyncio
async def test_update_incident_as_admin(client: AsyncClient):
    uid = _uid()
    cliente = await _register_and_login(client, "CLIENTE", uid)
    admin = await _register_and_login(client, "ADMIN_TALLER", uid)
    vehicle_id = await _create_vehicle(client, cliente, uid)
    create = await client.post(
        "/api/v1/incidents",
        json=_incident_payload(vehicle_id, cliente["user_id"], "Incidente PATCH"),
        headers=cliente["headers"],
    )
    incident_id = create.json()["id"]
    resp = await client.patch(
        f"/api/v1/incidents/{incident_id}",
        json={"priority_level": "ALTA", "title": "Incidente actualizado"},
        headers=admin["headers"],
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["priority_level"] == "ALTA"
    assert data["title"] == "Incidente actualizado"
