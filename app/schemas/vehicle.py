from datetime import datetime

from pydantic import BaseModel, Field


class VehicleBase(BaseModel):
    plate: str = Field(..., max_length=20)
    brand: str = Field(..., max_length=80)
    model: str = Field(..., max_length=80)
    manufacture_year: int | None = Field(None, ge=1950, le=2100)
    color: str | None = Field(None, max_length=50)
    notes: str | None = Field(None, max_length=255)


class VehicleCreate(VehicleBase):
    user_id: int


class VehicleUpdate(BaseModel):
    plate: str | None = Field(None, max_length=20)
    brand: str | None = Field(None, max_length=80)
    model: str | None = Field(None, max_length=80)
    manufacture_year: int | None = Field(None, ge=1950, le=2100)
    color: str | None = Field(None, max_length=50)
    notes: str | None = Field(None, max_length=255)
    status: str | None = Field(None, max_length=30)


class VehicleRead(VehicleBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
