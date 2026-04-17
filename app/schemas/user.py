from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ── Shared ───────────────────────────────────────────────
class UserBase(BaseModel):
    full_name: str = Field(..., max_length=150)
    ci: str | None = Field(None, max_length=30)
    phone: str | None = Field(None, max_length=30)
    email: EmailStr


# ── Create ───────────────────────────────────────────────
class UserCreate(UserBase):
    role: str = Field(..., max_length=30)
    password: str = Field(..., min_length=8)


# ── Update ───────────────────────────────────────────────
class UserUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=150)
    ci: str | None = Field(None, max_length=30)
    phone: str | None = Field(None, max_length=30)
    email: EmailStr | None = None
    status: str | None = Field(None, max_length=30)


# ── Read ─────────────────────────────────────────────────
class UserRead(UserBase):
    id: int
    role: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
