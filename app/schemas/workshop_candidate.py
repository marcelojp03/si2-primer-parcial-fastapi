from datetime import datetime

from pydantic import BaseModel, Field


class WorkshopCandidateBase(BaseModel):
    incident_id: int
    workshop_id: int
    score: float | None = None
    distance_km: float | None = None
    estimated_arrival_minutes: int | None = None


class WorkshopCandidateCreate(WorkshopCandidateBase):
    pass


class WorkshopCandidateUpdate(BaseModel):
    response_status: str | None = Field(None, max_length=30)
    response_note: str | None = Field(None, max_length=255)


class WorkshopCandidateRead(WorkshopCandidateBase):
    id: int
    notified: bool
    notified_at: datetime | None
    response_status: str
    responded_at: datetime | None
    response_note: str | None

    model_config = {"from_attributes": True}
