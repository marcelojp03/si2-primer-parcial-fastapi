from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident_status import IncidentStatus
from app.repositories.base import BaseRepository


class IncidentStatusRepository(BaseRepository[IncidentStatus]):
    def __init__(self, session: AsyncSession):
        super().__init__(IncidentStatus, session)
