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
