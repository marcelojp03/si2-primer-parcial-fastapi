from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.workshop import Workshop
from app.repositories.workshop_repository import WorkshopRepository
from app.schemas.workshop import WorkshopCreate, WorkshopUpdate


class WorkshopService:
    def __init__(self, session: AsyncSession):
        self.repo = WorkshopRepository(session)

    async def create(self, data: WorkshopCreate) -> Workshop:
        workshop = Workshop(**data.model_dump())
        return await self.repo.create(workshop)

    async def get_by_id(self, workshop_id: int) -> Workshop:
        workshop = await self.repo.get_by_id(workshop_id)
        if not workshop:
            raise NotFoundError("Workshop not found")
        return workshop

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Workshop]:
        return await self.repo.get_all(skip=skip, limit=limit)

    async def update(self, workshop_id: int, data: WorkshopUpdate) -> Workshop:
        workshop = await self.get_by_id(workshop_id)
        return await self.repo.update(workshop, data.model_dump(exclude_unset=True))
