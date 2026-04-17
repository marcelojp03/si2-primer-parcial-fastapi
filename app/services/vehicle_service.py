from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.vehicle import Vehicle
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


class VehicleService:
    def __init__(self, session: AsyncSession):
        self.repo = VehicleRepository(session)

    async def create(self, data: VehicleCreate) -> Vehicle:
        vehicle = Vehicle(**data.model_dump())
        return await self.repo.create(vehicle)

    async def get_by_id(self, vehicle_id: int) -> Vehicle:
        vehicle = await self.repo.get_by_id(vehicle_id)
        if not vehicle:
            raise NotFoundError("Vehicle not found")
        return vehicle

    async def get_by_user_id(self, user_id: int) -> Sequence[Vehicle]:
        return await self.repo.get_by_user_id(user_id)

    async def update(self, vehicle_id: int, data: VehicleUpdate) -> Vehicle:
        vehicle = await self.get_by_id(vehicle_id)
        return await self.repo.update(vehicle, data.model_dump(exclude_unset=True))
