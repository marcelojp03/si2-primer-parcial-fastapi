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
    quotation_estimated_cost: float | None = Field(None, ge=0)
    quotation_completion_minutes: int | None = Field(None, ge=1)
    quotation_description: str | None = Field(None, max_length=500)


class WorkshopCandidateRead(WorkshopCandidateBase):
    id: int
    notified: bool
    notified_at: datetime | None
    invitation_deadline: datetime | None
    response_status: str
    responded_at: datetime | None
    response_note: str | None
    quotation_estimated_cost: float | None = None
    quotation_completion_minutes: int | None = None
    quotation_description: str | None = None

    model_config = {"from_attributes": True}
