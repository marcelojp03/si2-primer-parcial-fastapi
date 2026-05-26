from datetime import datetime

from pydantic import BaseModel, Field


class IncidentTypeBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: str | None = Field(None, max_length=255)


class IncidentTypeCreate(IncidentTypeBase):
    pass


class IncidentTypeUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=255)
    status: str | None = Field(None, max_length=30)
    sla_minutes: int | None = Field(None, gt=0)


class SLAUpdate(BaseModel):
    sla_minutes: int = Field(..., gt=0, description="Minutos SLA para este tipo de incidente")


class IncidentTypeRead(IncidentTypeBase):
    id: int
    status: str
    sla_minutes: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
