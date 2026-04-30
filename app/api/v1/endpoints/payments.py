from fastapi import APIRouter

from app.api.deps import ClienteUser, CurrentUser, DbSession, SuperAdminUser
from app.schemas.payment import (
    PaymentCreate,
    PaymentRead,
    PaymentUpdate,
    QRGenerateRequest,
    QRGenerateResponse,
    QRStatusResponse,
)
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentRead, status_code=201)
async def create_payment(data: PaymentCreate, session: DbSession, _user: ClienteUser):
    svc = PaymentService(session)
    return await svc.create(data)


@router.get("/{payment_id}", response_model=PaymentRead)
async def read_payment(payment_id: int, session: DbSession, _current_user: CurrentUser):
    svc = PaymentService(session)
    return await svc.get_by_id(payment_id)


@router.get("", response_model=list[PaymentRead])
async def list_payments(
    session: DbSession,
    _current_user: CurrentUser,
    client_user_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
):
    svc = PaymentService(session)
    if client_user_id is not None:
        return await svc.get_by_client(client_user_id)
    return await svc.get_all(skip=skip, limit=limit)


@router.patch("/{payment_id}", response_model=PaymentRead)
async def update_payment(
    payment_id: int, data: PaymentUpdate, session: DbSession, _admin: SuperAdminUser
):
    svc = PaymentService(session)
    return await svc.update(payment_id, data)


# ── VPAY ─────────────────────────────────────────────────────────────────────


@router.post("/{payment_id}/generate-qr", response_model=QRGenerateResponse)
async def generate_qr(
    payment_id: int,
    data: QRGenerateRequest,
    session: DbSession,
    _user: ClienteUser,
):
    """Genera un código QR de cobro en VPAY para el pago indicado."""
    svc = PaymentService(session)
    id_qr, qr_base64 = await svc.generate_qr(
        payment_id=payment_id,
        gloss=data.gloss,
        additional_data=data.additional_data,
    )
    return QRGenerateResponse(payment_id=payment_id, id_qr=id_qr, qr_base64=qr_base64)


@router.get("/{payment_id}/qr-status", response_model=QRStatusResponse)
async def qr_status(
    payment_id: int,
    session: DbSession,
    _user: CurrentUser,
):
    """Consulta el estado del QR en VPAY. Si está pagado (PAG) actualiza automáticamente el pago y la asignación."""
    svc = PaymentService(session)
    vpay_status, paid = await svc.check_qr_status(payment_id)
    payment = await svc.get_by_id(payment_id)
    return QRStatusResponse(
        payment_id=payment_id,
        id_qr=payment.external_reference or "",
        vpay_status=vpay_status,
        paid=paid,
    )
