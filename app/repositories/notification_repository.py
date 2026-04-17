from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, session: AsyncSession):
        super().__init__(Notification, session)

    async def get_by_user_id(self, user_id: int) -> Sequence[Notification]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
