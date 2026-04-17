from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.specialty import Specialty
from app.repositories.specialty_repository import SpecialtyRepository
from app.schemas.specialty import SpecialtyCreate, SpecialtyUpdate


class SpecialtyService:
    def __init__(self, session: AsyncSession):
        self.repo = SpecialtyRepository(session)

    async def create(self, data: SpecialtyCreate) -> Specialty:
        specialty = Specialty(**data.model_dump())
        return await self.repo.create(specialty)

    async def get_by_id(self, specialty_id: int) -> Specialty:
        specialty = await self.repo.get_by_id(specialty_id)
        if not specialty:
            raise NotFoundError("Specialty not found")
        return specialty

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Specialty]:
        return await self.repo.get_all(skip=skip, limit=limit)

    async def update(self, specialty_id: int, data: SpecialtyUpdate) -> Specialty:
        specialty = await self.get_by_id(specialty_id)
        return await self.repo.update(specialty, data.model_dump(exclude_unset=True))
