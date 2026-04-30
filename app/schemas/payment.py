from datetime import datetime

from pydantic import BaseModel, Field


class PaymentBase(BaseModel):
    service_assignment_id: int
    client_user_id: int
    amount: float = Field(..., ge=0)
    currency: str = "BOB"
    payment_method: str = Field(..., max_length=30)


class PaymentCreate(PaymentBase):
    payment_provider: str | None = Field(None, max_length=50)
    external_reference: str | None = Field(None, max_length=150)


class PaymentUpdate(BaseModel):
    payment_status: str | None = Field(None, max_length=30)
    paid_at: datetime | None = None


class PaymentRead(PaymentBase):
    id: int
    payment_provider: str | None
    external_reference: str | None
    payment_status: str
    paid_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class QRGenerateRequest(BaseModel):
    gloss: str = Field(
        ..., max_length=100, description="Glosa del cobro, ej: 'SERVICIO AUXILIO MECANICO'"
    )
    additional_data: str | None = Field(
        None, max_length=100, description="Glosa secundaria; si se omite se usa gloss"
    )


class QRGenerateResponse(BaseModel):
    payment_id: int
    id_qr: str
    qr_base64: str


class QRStatusResponse(BaseModel):
    payment_id: int
    id_qr: str
    vpay_status: str
    paid: bool
