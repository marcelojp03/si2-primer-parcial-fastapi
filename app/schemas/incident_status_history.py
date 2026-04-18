from datetime import datetime

from pydantic import BaseModel, Field


class IncidentStatusHistoryBase(BaseModel):
    incident_id: int
    incident_status_id: int
    user_id: int | None = None
    observation: str | None = Field(None, max_length=255)


class IncidentStatusHistoryCreate(IncidentStatusHistoryBase):
    pass


class IncidentStatusHistoryRead(IncidentStatusHistoryBase):
    id: int
    changed_at: datetime

    model_config = {"from_attributes": True}
