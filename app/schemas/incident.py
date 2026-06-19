from datetime import datetime

from pydantic import BaseModel, Field


class IncidentBase(BaseModel):
    vehicle_id: int
    title: str = Field(..., max_length=150)
    description_text: str | None = None
    reference_address: str | None = Field(None, max_length=255)
    latitude: float | None = None
    longitude: float | None = None
    requires_tow: bool = False
    service_modality: str = Field(default="A_DOMICILIO", pattern=r"^(A_DOMICILIO|CLIENTE_VE_TALLER)$")


class IncidentCreate(IncidentBase):
    client_user_id: int
    client_uuid: str | None = None  # UUID v4 generado por el cliente para idempotencia


class IncidentUpdate(BaseModel):
    incident_type_id: int | None = None
    incident_status_id: int | None = None
    title: str | None = Field(None, max_length=150)
    description_text: str | None = None
    priority_level: str | None = Field(None, max_length=20)
    requires_tow: bool | None = None


class IncidentRead(IncidentBase):
    id: int
    client_user_id: int
    tenant_id: int | None = None
    client_uuid: str | None
    incident_type_id: int | None
    incident_status_id: int
    priority_level: str | None
    requested_at: datetime
    accepted_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
