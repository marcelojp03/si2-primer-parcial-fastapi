from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident_status_history import IncidentStatusHistory
from app.repositories.incident_status_history_repository import IncidentStatusHistoryRepository
from app.schemas.incident_status_history import IncidentStatusHistoryCreate


class IncidentStatusHistoryService:
    def __init__(self, session: AsyncSession):
        self.repo = IncidentStatusHistoryRepository(session)

    async def create(self, data: IncidentStatusHistoryCreate) -> IncidentStatusHistory:
        entry = IncidentStatusHistory(**data.model_dump())
        return await self.repo.create(entry)

    async def get_by_incident(self, incident_id: int) -> Sequence[IncidentStatusHistory]:
        return await self.repo.get_by_incident(incident_id)
