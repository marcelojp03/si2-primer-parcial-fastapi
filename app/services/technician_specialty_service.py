from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.technician_specialty import TechnicianSpecialty
from app.repositories.technician_specialty_repository import TechnicianSpecialtyRepository
from app.schemas.technician_specialty import TechnicianSpecialtyCreate


class TechnicianSpecialtyService:
    def __init__(self, session: AsyncSession):
        self.repo = TechnicianSpecialtyRepository(session)

    async def create(self, data: TechnicianSpecialtyCreate) -> TechnicianSpecialty:
        ts = TechnicianSpecialty(**data.model_dump())
        return await self.repo.create(ts)

    async def get_by_id(self, ts_id: int) -> TechnicianSpecialty:
        ts = await self.repo.get_by_id(ts_id)
        if not ts:
            raise NotFoundError("Technician specialty not found")
        return ts

    async def get_by_technician(self, technician_id: int) -> Sequence[TechnicianSpecialty]:
        return await self.repo.get_by_technician(technician_id)

    async def delete(self, ts_id: int) -> None:
        ts = await self.get_by_id(ts_id)
        await self.repo.delete(ts)
