from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.workshop_schedule import WorkshopSchedule
from app.repositories.workshop_schedule_repository import WorkshopScheduleRepository
from app.schemas.workshop_schedule import WorkshopScheduleCreate, WorkshopScheduleUpdate


class WorkshopScheduleService:
    def __init__(self, session: AsyncSession):
        self.repo = WorkshopScheduleRepository(session)

    async def create(self, data: WorkshopScheduleCreate) -> WorkshopSchedule:
        schedule = WorkshopSchedule(**data.model_dump())
        return await self.repo.create(schedule)

    async def get_by_id(self, schedule_id: int) -> WorkshopSchedule:
        schedule = await self.repo.get_by_id(schedule_id)
        if not schedule:
            raise NotFoundError("Workshop schedule not found")
        return schedule

    async def get_by_workshop(self, workshop_id: int) -> Sequence[WorkshopSchedule]:
        return await self.repo.get_by_workshop(workshop_id)

    async def update(self, schedule_id: int, data: WorkshopScheduleUpdate) -> WorkshopSchedule:
        schedule = await self.get_by_id(schedule_id)
        return await self.repo.update(schedule, data.model_dump(exclude_unset=True))

    async def delete(self, schedule_id: int) -> None:
        schedule = await self.get_by_id(schedule_id)
        await self.repo.delete(schedule)
