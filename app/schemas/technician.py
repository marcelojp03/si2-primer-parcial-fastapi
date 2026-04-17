from datetime import datetime

from pydantic import BaseModel, Field


class TechnicianBase(BaseModel):
    workshop_id: int
    full_name: str = Field(..., max_length=150)
    ci: str | None = Field(None, max_length=30)
    phone: str | None = Field(None, max_length=30)
    notes: str | None = Field(None, max_length=255)


class TechnicianCreate(TechnicianBase):
    pass


class TechnicianUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=150)
    ci: str | None = Field(None, max_length=30)
    phone: str | None = Field(None, max_length=30)
    availability_status: str | None = Field(None, max_length=30)
    notes: str | None = Field(None, max_length=255)


class TechnicianRead(TechnicianBase):
    id: int
    availability_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
