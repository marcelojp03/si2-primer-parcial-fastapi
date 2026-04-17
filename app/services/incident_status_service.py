from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.incident_status import IncidentStatus
from app.repositories.incident_status_repository import IncidentStatusRepository
from app.schemas.incident_status import IncidentStatusCreate, IncidentStatusUpdate


class IncidentStatusService:
    def __init__(self, session: AsyncSession):
        self.repo = IncidentStatusRepository(session)

    async def create(self, data: IncidentStatusCreate) -> IncidentStatus:
        obj = IncidentStatus(**data.model_dump())
        return await self.repo.create(obj)

    async def get_by_id(self, record_id: int) -> IncidentStatus:
        obj = await self.repo.get_by_id(record_id)
        if not obj:
            raise NotFoundError("Incident status not found")
        return obj

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[IncidentStatus]:
        return await self.repo.get_all(skip=skip, limit=limit)

    async def update(self, record_id: int, data: IncidentStatusUpdate) -> IncidentStatus:
        obj = await self.get_by_id(record_id)
        return await self.repo.update(obj, data.model_dump(exclude_unset=True))
