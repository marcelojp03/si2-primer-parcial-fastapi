from datetime import datetime

from pydantic import BaseModel, Field


class IncidentStatusBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: str | None = Field(None, max_length=255)
    sort_order: int


class IncidentStatusCreate(IncidentStatusBase):
    pass


class IncidentStatusUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=255)
    sort_order: int | None = None
    status: str | None = Field(None, max_length=30)


class IncidentStatusRead(IncidentStatusBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
