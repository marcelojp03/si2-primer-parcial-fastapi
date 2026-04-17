from datetime import datetime

from pydantic import BaseModel, Field


class AssignmentBase(BaseModel):
    incident_id: int
    workshop_id: int
    technician_id: int | None = None
    specialty_id: int | None = None


class AssignmentCreate(AssignmentBase):
    assigned_by_user_id: int | None = None
    distance_km: float | None = Field(None, ge=0)
    estimated_arrival_minutes: int | None = Field(None, ge=0)
    estimated_cost: float | None = Field(None, ge=0)


class AssignmentUpdate(BaseModel):
    technician_id: int | None = None
    assignment_status: str | None = Field(None, max_length=30)
    performed_service_description: str | None = None
    final_cost: float | None = Field(None, ge=0)
    final_notes: str | None = None


class AssignmentRead(AssignmentBase):
    id: int
    assigned_by_user_id: int | None
    performed_service_description: str | None
    distance_km: float | None
    estimated_arrival_minutes: int | None
    estimated_cost: float | None
    final_cost: float | None
    assignment_status: str
    final_notes: str | None
    assigned_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
