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

    async def create(self, data: IncidentCreate) -> Incident:
        status_id = await self._get_pendiente_status_id()
        incident = Incident(**data.model_dump(), incident_status_id=status_id)
        return await self.repo.create(incident)

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
