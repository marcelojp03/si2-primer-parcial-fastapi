from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, session: AsyncSession):
        super().__init__(Payment, session)

    async def get_by_assignment(self, service_assignment_id: int) -> Payment | None:
        stmt = select(Payment).where(Payment.service_assignment_id == service_assignment_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_client(self, client_user_id: int) -> Sequence[Payment]:
        stmt = select(Payment).where(Payment.client_user_id == client_user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
