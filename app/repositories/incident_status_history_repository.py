from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident_status_history import IncidentStatusHistory
from app.repositories.base import BaseRepository


class IncidentStatusHistoryRepository(BaseRepository[IncidentStatusHistory]):
    def __init__(self, session: AsyncSession):
        super().__init__(IncidentStatusHistory, session)

    async def get_by_incident(self, incident_id: int) -> Sequence[IncidentStatusHistory]:
        stmt = (
            select(IncidentStatusHistory)
            .where(IncidentStatusHistory.incident_id == incident_id)
            .order_by(IncidentStatusHistory.changed_at)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
