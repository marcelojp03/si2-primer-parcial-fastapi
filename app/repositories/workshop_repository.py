from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workshop import Workshop
from app.repositories.base import BaseRepository


class WorkshopRepository(BaseRepository[Workshop]):
    def __init__(self, session: AsyncSession):
        super().__init__(Workshop, session)

    async def get_by_admin_user_id(self, admin_user_id: int) -> Workshop | None:
        stmt = select(Workshop).where(Workshop.admin_user_id == admin_user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
