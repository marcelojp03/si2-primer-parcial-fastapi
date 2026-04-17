from datetime import datetime

from pydantic import BaseModel, Field


# ── Workshop ─────────────────────────────────────────────
class WorkshopBase(BaseModel):
    name: str = Field(..., max_length=150)
    description: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=30)
    email: str | None = Field(None, max_length=150)
    address: str | None = Field(None, max_length=255)
    latitude: float | None = None
    longitude: float | None = None
    has_tow: bool = False
    is_24_hours: bool = False


class WorkshopCreate(WorkshopBase):
    admin_user_id: int


class WorkshopUpdate(BaseModel):
    name: str | None = Field(None, max_length=150)
    description: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=30)
    email: str | None = Field(None, max_length=150)
    address: str | None = Field(None, max_length=255)
    latitude: float | None = None
    longitude: float | None = None
    has_tow: bool | None = None
    is_24_hours: bool | None = None
    status: str | None = Field(None, max_length=30)


class WorkshopRead(WorkshopBase):
    id: int
    admin_user_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
