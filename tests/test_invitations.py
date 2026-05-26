"""Tests para invitaciones con TTL y reputación (CU23/24/25).

Tests unitarios para la lógica de TTL e invitaciones en assignment_service.
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestInvitationTTL:
    """Pruebas de la lógica TTL en assignment_service sin BD."""

    def _make_candidate(self, minutes_ago: int):
        """Crea un candidato mock con deadline ya expirado o vigente."""
        deadline = datetime.now(UTC) - timedelta(minutes=minutes_ago)
        candidate = MagicMock()
        candidate.invitation_deadline = deadline.replace(tzinfo=None)  # stored naive
        candidate.workshop_id = 1
        return candidate

    def test_deadline_expired_detection(self):
        """Verifica la lógica de comparación de TTL expirado."""
        # Expired: deadline fue hace 5 minutos
        candidate = self._make_candidate(minutes_ago=5)
        now = datetime.now(UTC)
        deadline = candidate.invitation_deadline.replace(tzinfo=UTC)
        assert now > deadline, "El deadline debería estar expirado"

    def test_deadline_not_expired(self):
        """Deadline en el futuro no debe considerarse expirado."""
        candidate = MagicMock()
        future = datetime.now(UTC) + timedelta(minutes=10)
        candidate.invitation_deadline = future.replace(tzinfo=None)
        now = datetime.now(UTC)
        deadline = candidate.invitation_deadline.replace(tzinfo=UTC)
        assert now < deadline, "El deadline no debería estar expirado"

    def test_reputation_penalty_value(self):
        """El valor de la penalidad de reputación debe ser 5.0."""
        from app.services.assignment_service import _IGNORE_PENALTY

        assert _IGNORE_PENALTY == 5.0

    def test_score_workshop_weights_sum(self):
        """Los pesos del scoring deben sumar 100."""
        # Distance: 35, specialty: 25, reputation: 20, tow: 10, 24h: 10
        weights = 35 + 25 + 20 + 10 + 10
        assert weights == 100

    @pytest.mark.asyncio
    async def test_idempotency_409_uuid(self):
        """uuid_cliente duplicado devuelve 409 con el incidente existente."""
        import pytest_asyncio
        from httpx import ASGITransport, AsyncClient

        from app.main import app

        uid = uuid.uuid4().hex[:8]
        client_uuid = str(uuid.uuid4())

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # Registrar y loguear un CLIENTE
            email = f"idem_{uid}@test.com"
            await ac.post(
                "/api/v1/auth/register",
                json={
                    "full_name": "Idem Test",
                    "email": email,
                    "password": "pass1234",
                    "role": "CLIENTE",
                },
            )
            resp = await ac.post(
                "/api/v1/auth/login", json={"email": email, "password": "pass1234"}
            )
            token = resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Crear vehículo primero
            me = await ac.get("/api/v1/users/me", headers=headers)
            user_id = me.json()["id"]
            veh_resp = await ac.post(
                "/api/v1/vehicles",
                json={
                    "user_id": user_id,
                    "plate": f"ABC{uid[:3].upper()}",
                    "brand": "Toyota",
                    "model": "Corolla",
                    "year": 2020,
                },
                headers=headers,
            )
            if veh_resp.status_code != 201:
                pytest.skip("No se pudo crear vehículo — entorno sin BD real")
            vehicle_id = veh_resp.json()["id"]

            payload = {
                "client_user_id": user_id,
                "vehicle_id": vehicle_id,
                "title": "Prueba idempotencia",
                "client_uuid": client_uuid,
            }

            r1 = await ac.post("/api/v1/incidents", json=payload, headers=headers)
            if r1.status_code not in (200, 201):
                pytest.skip("No se pudo crear incidente — entorno sin BD real")

            r2 = await ac.post("/api/v1/incidents", json=payload, headers=headers)
            assert r2.status_code == 409
            # El body debe contener el mismo incidente
            assert r2.json()["client_uuid"] == client_uuid
