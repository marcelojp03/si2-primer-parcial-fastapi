from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workshop_schedule import WorkshopSchedule
from app.repositories.base import BaseRepository


class WorkshopScheduleRepository(BaseRepository[WorkshopSchedule]):
    def __init__(self, session: AsyncSession):
        super().__init__(WorkshopSchedule, session)

    async def get_by_workshop(self, workshop_id: int) -> Sequence[WorkshopSchedule]:
        stmt = select(WorkshopSchedule).where(WorkshopSchedule.workshop_id == workshop_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
