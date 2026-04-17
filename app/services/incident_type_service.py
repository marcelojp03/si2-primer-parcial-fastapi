from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.incident_type import IncidentType
from app.repositories.incident_type_repository import IncidentTypeRepository
from app.schemas.incident_type import IncidentTypeCreate, IncidentTypeUpdate


class IncidentTypeService:
    def __init__(self, session: AsyncSession):
        self.repo = IncidentTypeRepository(session)

    async def create(self, data: IncidentTypeCreate) -> IncidentType:
        obj = IncidentType(**data.model_dump())
        return await self.repo.create(obj)

    async def get_by_id(self, record_id: int) -> IncidentType:
        obj = await self.repo.get_by_id(record_id)
        if not obj:
            raise NotFoundError("Incident type not found")
        return obj

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[IncidentType]:
        return await self.repo.get_all(skip=skip, limit=limit)

    async def update(self, record_id: int, data: IncidentTypeUpdate) -> IncidentType:
        obj = await self.get_by_id(record_id)
        return await self.repo.update(obj, data.model_dump(exclude_unset=True))
