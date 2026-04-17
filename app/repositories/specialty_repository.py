from sqlalchemy.ext.asyncio import AsyncSession

from app.models.specialty import Specialty
from app.repositories.base import BaseRepository


class SpecialtyRepository(BaseRepository[Specialty]):
    def __init__(self, session: AsyncSession):
        super().__init__(Specialty, session)
