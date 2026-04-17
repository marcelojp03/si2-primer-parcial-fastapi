from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.technician import Technician
from app.repositories.technician_repository import TechnicianRepository
from app.schemas.technician import TechnicianCreate, TechnicianUpdate


class TechnicianService:
    def __init__(self, session: AsyncSession):
        self.repo = TechnicianRepository(session)

    async def create(self, data: TechnicianCreate) -> Technician:
        technician = Technician(**data.model_dump())
        return await self.repo.create(technician)

    async def get_by_id(self, technician_id: int) -> Technician:
        technician = await self.repo.get_by_id(technician_id)
        if not technician:
            raise NotFoundError("Technician not found")
        return technician

    async def get_by_workshop_id(self, workshop_id: int) -> Sequence[Technician]:
        return await self.repo.get_by_workshop_id(workshop_id)

    async def update(self, technician_id: int, data: TechnicianUpdate) -> Technician:
        technician = await self.get_by_id(technician_id)
        return await self.repo.update(technician, data.model_dump(exclude_unset=True))
