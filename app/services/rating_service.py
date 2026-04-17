from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.rating import Rating
from app.repositories.rating_repository import RatingRepository
from app.schemas.rating import RatingCreate


class RatingService:
    def __init__(self, session: AsyncSession):
        self.repo = RatingRepository(session)

    async def create(self, data: RatingCreate) -> Rating:
        rating = Rating(**data.model_dump())
        return await self.repo.create(rating)

    async def get_by_id(self, rating_id: int) -> Rating:
        rating = await self.repo.get_by_id(rating_id)
        if not rating:
            raise NotFoundError("Rating not found")
        return rating
