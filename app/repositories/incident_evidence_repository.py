from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident_evidence import IncidentEvidence
from app.repositories.base import BaseRepository


class IncidentEvidenceRepository(BaseRepository[IncidentEvidence]):
    def __init__(self, session: AsyncSession):
        super().__init__(IncidentEvidence, session)

    async def get_by_incident(self, incident_id: int) -> Sequence[IncidentEvidence]:
        stmt = select(IncidentEvidence).where(IncidentEvidence.incident_id == incident_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
