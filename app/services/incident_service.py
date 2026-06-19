from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.incident import Incident
from app.models.incident_status import IncidentStatus
from app.repositories.incident_repository import IncidentRepository
from app.schemas.incident import IncidentCreate, IncidentUpdate


class IncidentService:
    def __init__(self, session: AsyncSession):
        self.repo = IncidentRepository(session)

    async def _get_pendiente_status_id(self) -> int:
        result = await self.repo.session.execute(
            select(IncidentStatus.id).where(IncidentStatus.name == "PENDIENTE").limit(1)
        )
        status_id = result.scalar_one_or_none()
        if status_id is None:
            raise NotFoundError("Estado 'PENDIENTE' no encontrado en la base de datos")
        return status_id

    async def create(self, data: IncidentCreate) -> tuple["Incident", bool]:
        """Crea un incidente. Retorna (incident, created).

        Si ``data.client_uuid`` está presente y ya existe un incidente con ese UUID,
        retorna (existing, False) para que el endpoint responda 409.
        """
        if data.client_uuid:
            existing = await self.repo.get_by_uuid(data.client_uuid)
            if existing:
                return existing, False

        status_id = await self._get_pendiente_status_id()
        dump = data.model_dump()
        incident = Incident(
            client_user_id=dump["client_user_id"],
            vehicle_id=dump["vehicle_id"],
            title=dump["title"],
            description_text=dump.get("description_text"),
            reference_address=dump.get("reference_address"),
            latitude=dump.get("latitude"),
            longitude=dump.get("longitude"),
            requires_tow=dump.get("requires_tow", False),
            service_modality=dump.get("service_modality", "A_DOMICILIO"),
            client_uuid=dump.get("client_uuid"),
            incident_status_id=status_id,
        )
        return await self.repo.create(incident), True

    async def get_by_id(self, incident_id: int) -> Incident:
        incident = await self.repo.get_by_id(incident_id)
        if not incident:
            raise NotFoundError("Incident not found")
        return incident

    async def get_by_client(self, client_user_id: int) -> Sequence[Incident]:
        return await self.repo.get_by_client_user_id(client_user_id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Incident]:
        return await self.repo.get_all(skip=skip, limit=limit)

    async def get_filtered(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        status_id: int | None = None,
        client_user_id: int | None = None,
        priority: str | None = None,
    ) -> Sequence[Incident]:
        return await self.repo.get_filtered(
            skip=skip,
            limit=limit,
            status_id=status_id,
            client_user_id=client_user_id,
            priority=priority,
        )

    async def update(self, incident_id: int, data: IncidentUpdate) -> Incident:
        incident = await self.get_by_id(incident_id)
        return await self.repo.update(incident, data.model_dump(exclude_unset=True))
