from datetime import datetime

from pydantic import BaseModel, Field


class IncidentEvidenceBase(BaseModel):
    evidence_type: str = Field(..., max_length=20)
    file_url: str | None = Field(None, max_length=255)
    file_key: str | None = Field(None, max_length=255)
    mime_type: str | None = Field(None, max_length=100)
    file_name: str | None = Field(None, max_length=150)
    file_size: int | None = None


class IncidentEvidenceCreate(IncidentEvidenceBase):
    incident_id: int


class IncidentEvidenceRead(IncidentEvidenceBase):
    id: int
    incident_id: int
    uploaded_at: datetime

    model_config = {"from_attributes": True}
