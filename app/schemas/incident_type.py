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


class IncidentTypeRead(IncidentTypeBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
