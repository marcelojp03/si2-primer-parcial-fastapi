from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import Vehicle
from app.repositories.base import BaseRepository


class VehicleRepository(BaseRepository[Vehicle]):
    def __init__(self, session: AsyncSession):
        super().__init__(Vehicle, session)

    async def get_by_user_id(self, user_id: int) -> Sequence[Vehicle]:
        stmt = select(Vehicle).where(Vehicle.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_plate(self, plate: str) -> Vehicle | None:
        stmt = select(Vehicle).where(Vehicle.plate == plate)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
