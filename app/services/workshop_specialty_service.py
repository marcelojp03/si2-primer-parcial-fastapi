from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.workshop_specialty import WorkshopSpecialty
from app.repositories.workshop_specialty_repository import WorkshopSpecialtyRepository
from app.schemas.workshop_specialty import WorkshopSpecialtyCreate


class WorkshopSpecialtyService:
    def __init__(self, session: AsyncSession):
        self.repo = WorkshopSpecialtyRepository(session)

    async def create(self, data: WorkshopSpecialtyCreate) -> WorkshopSpecialty:
        ws = WorkshopSpecialty(**data.model_dump())
        return await self.repo.create(ws)

    async def get_by_id(self, ws_id: int) -> WorkshopSpecialty:
        ws = await self.repo.get_by_id(ws_id)
        if not ws:
            raise NotFoundError("Workshop specialty not found")
        return ws

    async def get_by_workshop(self, workshop_id: int) -> Sequence[WorkshopSpecialty]:
        return await self.repo.get_by_workshop(workshop_id)

    async def delete(self, ws_id: int) -> None:
        ws = await self.get_by_id(ws_id)
        await self.repo.delete(ws)
