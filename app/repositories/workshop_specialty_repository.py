from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workshop_specialty import WorkshopSpecialty
from app.repositories.base import BaseRepository


class WorkshopSpecialtyRepository(BaseRepository[WorkshopSpecialty]):
    def __init__(self, session: AsyncSession):
        super().__init__(WorkshopSpecialty, session)

    async def get_by_workshop(self, workshop_id: int) -> Sequence[WorkshopSpecialty]:
        stmt = select(WorkshopSpecialty).where(WorkshopSpecialty.workshop_id == workshop_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
