from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident_type import IncidentType
from app.repositories.base import BaseRepository


class IncidentTypeRepository(BaseRepository[IncidentType]):
    def __init__(self, session: AsyncSession):
        super().__init__(IncidentType, session)
