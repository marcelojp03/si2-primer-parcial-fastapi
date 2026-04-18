from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service_assignment import ServiceAssignment
from app.repositories.base import BaseRepository


class AssignmentRepository(BaseRepository[ServiceAssignment]):
    def __init__(self, session: AsyncSession):
        super().__init__(ServiceAssignment, session)

    async def get_by_incident(self, incident_id: int) -> ServiceAssignment | None:
        stmt = select(ServiceAssignment).where(ServiceAssignment.incident_id == incident_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
