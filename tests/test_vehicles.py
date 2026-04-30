"""Tests de integración — Vehículos."""

import pytest
from httpx import AsyncClient

from tests.conftest import _register_and_login, _uid


@pytest.mark.asyncio
async def test_create_vehicle(client: AsyncClient):
    uid = _uid()
    cliente = await _register_and_login(client, "CLIENTE", uid)
    resp = await client.post(
        "/api/v1/vehicles",
        json={
            "plate": f"VH{uid[:6].upper()}",
            "brand": "Honda",
            "model": "Civic",
            "manufacture_year": 2021,
            "color": "Rojo",
            "user_id": cliente["user_id"],
        },
        headers=cliente["headers"],
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["brand"] == "Honda"
    assert data["user_id"] == cliente["user_id"]
    assert data["status"] == "ACTIVO"


@pytest.mark.asyncio
async def test_create_vehicle_requires_auth(client: AsyncClient):
    uid = _uid()
    resp = await client.post(
        "/api/v1/vehicles",
        json={"plate": f"NA{uid[:6].upper()}", "brand": "Ford", "model": "Fiesta", "user_id": 1},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_vehicle(client: AsyncClient):
    uid = _uid()
    cliente = await _register_and_login(client, "CLIENTE", uid)
    create = await client.post(
        "/api/v1/vehicles",
        json={
            "plate": f"GT{uid[:6].upper()}",
            "brand": "Toyota",
            "model": "Corolla",
            "manufacture_year": 2022,
            "color": "Blanco",
            "user_id": cliente["user_id"],
        },
        headers=cliente["headers"],
    )
    vehicle_id = create.json()["id"]
    resp = await client.get(f"/api/v1/vehicles/{vehicle_id}", headers=cliente["headers"])
    assert resp.status_code == 200
    assert resp.json()["id"] == vehicle_id


@pytest.mark.asyncio
async def test_get_vehicle_not_found(client: AsyncClient):
    uid = _uid()
    cliente = await _register_and_login(client, "CLIENTE", uid)
    resp = await client.get("/api/v1/vehicles/999999", headers=cliente["headers"])
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_my_vehicles(client: AsyncClient):
    uid = _uid()
    cliente = await _register_and_login(client, "CLIENTE", uid)
    create = await client.post(
        "/api/v1/vehicles",
        json={
            "plate": f"LS{uid[:6].upper()}",
            "brand": "Kia",
            "model": "Sportage",
            "manufacture_year": 2023,
            "color": "Gris",
            "user_id": cliente["user_id"],
        },
        headers=cliente["headers"],
    )
    vehicle_id = create.json()["id"]
    resp = await client.get("/api/v1/vehicles", headers=cliente["headers"])
    assert resp.status_code == 200
    vehicles = resp.json()
    assert isinstance(vehicles, list)
    assert any(v["id"] == vehicle_id for v in vehicles)


@pytest.mark.asyncio
async def test_update_vehicle(client: AsyncClient):
    uid = _uid()
    cliente = await _register_and_login(client, "CLIENTE", uid)
    create = await client.post(
        "/api/v1/vehicles",
        json={
            "plate": f"UP{uid[:6].upper()}",
            "brand": "Suzuki",
            "model": "Swift",
            "manufacture_year": 2019,
            "color": "Azul",
            "user_id": cliente["user_id"],
        },
        headers=cliente["headers"],
    )
    vehicle_id = create.json()["id"]
    resp = await client.patch(
        f"/api/v1/vehicles/{vehicle_id}",
        json={"color": "Verde"},
        headers=cliente["headers"],
    )
    assert resp.status_code == 200
    assert resp.json()["color"] == "Verde"
