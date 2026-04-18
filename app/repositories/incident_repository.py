from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident
from app.repositories.base import BaseRepository


class IncidentRepository(BaseRepository[Incident]):
    def __init__(self, session: AsyncSession):
        super().__init__(Incident, session)

    async def get_by_client_user_id(self, client_user_id: int) -> Sequence[Incident]:
        stmt = select(Incident).where(Incident.client_user_id == client_user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_filtered(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        status_id: int | None = None,
        client_user_id: int | None = None,
        priority: str | None = None,
    ) -> Sequence[Incident]:
        stmt = select(Incident)
        if status_id is not None:
            stmt = stmt.where(Incident.incident_status_id == status_id)
        if client_user_id is not None:
            stmt = stmt.where(Incident.client_user_id == client_user_id)
        if priority is not None:
            stmt = stmt.where(Incident.priority_level == priority)
        stmt = stmt.order_by(Incident.id.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
