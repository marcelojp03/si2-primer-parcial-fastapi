from datetime import datetime

from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    name: str = Field(..., max_length=150)
    slug: str = Field(..., max_length=80, pattern=r"^[a-z0-9-]+$")


class TenantUpdate(BaseModel):
    name: str | None = Field(None, max_length=150)
    status: str | None = Field(None, max_length=30)


class TenantRead(BaseModel):
    id: int
    name: str
    slug: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
