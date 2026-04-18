from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workshop_candidate import WorkshopCandidate
from app.repositories.base import BaseRepository


class WorkshopCandidateRepository(BaseRepository[WorkshopCandidate]):
    def __init__(self, session: AsyncSession):
        super().__init__(WorkshopCandidate, session)

    async def get_by_incident(self, incident_id: int) -> Sequence[WorkshopCandidate]:
        stmt = (
            select(WorkshopCandidate)
            .where(WorkshopCandidate.incident_id == incident_id)
            .order_by(WorkshopCandidate.score.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_workshop_and_incident(
        self, workshop_id: int, incident_id: int
    ) -> WorkshopCandidate | None:
        stmt = select(WorkshopCandidate).where(
            WorkshopCandidate.workshop_id == workshop_id,
            WorkshopCandidate.incident_id == incident_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
