from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.technician import Technician
from app.repositories.base import BaseRepository


class TechnicianRepository(BaseRepository[Technician]):
    def __init__(self, session: AsyncSession):
        super().__init__(Technician, session)

    async def get_by_workshop_id(self, workshop_id: int) -> Sequence[Technician]:
        stmt = select(Technician).where(Technician.workshop_id == workshop_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
