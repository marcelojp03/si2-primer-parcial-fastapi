from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.technician_specialty import TechnicianSpecialty
from app.repositories.base import BaseRepository


class TechnicianSpecialtyRepository(BaseRepository[TechnicianSpecialty]):
    def __init__(self, session: AsyncSession):
        super().__init__(TechnicianSpecialty, session)

    async def get_by_technician(self, technician_id: int) -> Sequence[TechnicianSpecialty]:
        stmt = select(TechnicianSpecialty).where(TechnicianSpecialty.technician_id == technician_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
