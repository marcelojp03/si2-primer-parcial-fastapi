"""Tests de integración — Autenticación (registro y login)."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_cliente(client: AsyncClient):
    uid = uuid.uuid4().hex[:8]
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Cliente Nuevo",
            "email": f"reg_{uid}@test.com",
            "password": "password123",
            "role": "CLIENTE",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["role"] == "CLIENTE"
    assert data["status"] == "ACTIVO"
    assert "id" in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_register_admin_taller(client: AsyncClient):
    uid = uuid.uuid4().hex[:8]
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Admin Taller",
            "email": f"adm_{uid}@test.com",
            "password": "password123",
            "role": "ADMIN_TALLER",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["role"] == "ADMIN_TALLER"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    uid = uuid.uuid4().hex[:8]
    email = f"dup_{uid}@test.com"
    payload = {
        "full_name": "Dup User",
        "email": email,
        "password": "password123",
        "role": "CLIENTE",
    }
    r1 = await client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201

    r2 = await client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code in (400, 409, 422)


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    uid = uuid.uuid4().hex[:8]
    email = f"login_{uid}@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Login User",
            "email": email,
            "password": "password123",
            "role": "CLIENTE",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    uid = uuid.uuid4().hex[:8]
    email = f"wrongpw_{uid}@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={"full_name": "WP User", "email": email, "password": "password123", "role": "CLIENTE"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "wrongpassword"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "noexiste_xyz@test.com", "password": "password123"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_token(client: AsyncClient):
    uid = uuid.uuid4().hex[:8]
    email = f"me_{uid}@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={"full_name": "Me User", "email": email, "password": "password123", "role": "CLIENTE"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    token = login.json()["access_token"]
    resp = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == email
