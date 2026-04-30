from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.payment import Payment
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payment import PaymentCreate, PaymentUpdate
from app.utils import vpay_client


class PaymentService:
    def __init__(self, session: AsyncSession):
        self.repo = PaymentRepository(session)
        self.assignment_repo = AssignmentRepository(session)

    async def create(self, data: PaymentCreate) -> Payment:
        existing = await self.repo.get_by_assignment(data.service_assignment_id)
        if existing:
            return existing
        payment = Payment(**data.model_dump())
        return await self.repo.create(payment)

    async def get_by_id(self, payment_id: int) -> Payment:
        payment = await self.repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundError("Payment not found")
        return payment

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Payment]:
        return await self.repo.get_all(skip=skip, limit=limit)

    async def get_by_client(self, client_user_id: int) -> Sequence[Payment]:
        return await self.repo.get_by_client(client_user_id)

    async def update(self, payment_id: int, data: PaymentUpdate) -> Payment:
        payment = await self.get_by_id(payment_id)
        return await self.repo.update(payment, data.model_dump(exclude_unset=True))

    # ── VPAY ─────────────────────────────────────────────

    async def generate_qr(
        self,
        payment_id: int,
        gloss: str,
        additional_data: str | None = None,
    ) -> tuple[str, str]:
        """Genera un QR de cobro en VPAY. Retorna (id_qr, qr_base64)."""
        from datetime import date

        payment = await self.get_by_id(payment_id)

        if payment.payment_method.upper() != "QR":
            raise BadRequestError("El método de pago debe ser QR para generar un código VPAY")

        if payment.payment_status == "PAGADO":
            raise BadRequestError("El pago ya fue completado, no se puede generar un nuevo QR")

        id_qr, qr_base64 = await vpay_client.generate_qr(
            amount=float(payment.amount),
            gloss=gloss,
            expiration_date=date.today(),
            additional_data=additional_data or gloss,
        )

        await self.repo.update(
            payment,
            {"payment_provider": "VPAY", "external_reference": id_qr},
        )
        return id_qr, qr_base64

    async def check_qr_status(self, payment_id: int) -> tuple[str, bool]:
        """Consulta el estado del QR en VPAY. Si está pagado (PAG) actualiza el pago y la asignación.
        Retorna (vpay_status, paid)."""
        payment = await self.get_by_id(payment_id)

        if not payment.external_reference:
            raise BadRequestError("El pago aún no tiene un QR generado")

        vpay_status = await vpay_client.check_qr_status(payment.external_reference)
        paid = vpay_status == "PAG"

        if paid and payment.payment_status != "PAGADO":
            await self.repo.update(
                payment,
                {"payment_status": "PAGADO", "paid_at": datetime.now(UTC)},
            )
            assignment = await self.assignment_repo.get_by_id(payment.service_assignment_id)
            if assignment:
                await self.assignment_repo.update(assignment, {"assignment_status": "PAGADO"})

        return vpay_status, paid
