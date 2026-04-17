from datetime import datetime

from pydantic import BaseModel, Field


class RatingBase(BaseModel):
    service_assignment_id: int
    client_user_id: int
    score: int = Field(..., ge=1, le=5)
    comment: str | None = Field(None, max_length=255)


class RatingCreate(RatingBase):
    pass


class RatingRead(RatingBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
