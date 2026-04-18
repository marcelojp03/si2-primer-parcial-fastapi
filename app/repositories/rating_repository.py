from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rating import Rating
from app.repositories.base import BaseRepository


class RatingRepository(BaseRepository[Rating]):
    def __init__(self, session: AsyncSession):
        super().__init__(Rating, session)

    async def get_by_assignment(self, assignment_id: int) -> Rating | None:
        stmt = select(Rating).where(Rating.service_assignment_id == assignment_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
