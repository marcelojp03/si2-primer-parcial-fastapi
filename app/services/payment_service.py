from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.payment import Payment
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payment import PaymentCreate, PaymentUpdate


class PaymentService:
    def __init__(self, session: AsyncSession):
        self.repo = PaymentRepository(session)

    async def create(self, data: PaymentCreate) -> Payment:
        payment = Payment(**data.model_dump())
        return await self.repo.create(payment)

    async def get_by_id(self, payment_id: int) -> Payment:
        payment = await self.repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundError("Payment not found")
        return payment

    async def update(self, payment_id: int, data: PaymentUpdate) -> Payment:
        payment = await self.get_by_id(payment_id)
        return await self.repo.update(payment, data.model_dump(exclude_unset=True))
