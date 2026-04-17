from datetime import datetime

from pydantic import BaseModel


class AiAnalysisRead(BaseModel):
    id: int
    incident_id: int
    transcribed_audio: str | None = None
    generated_summary: str | None = None
    predicted_incident_type_id: int | None = None
    predicted_priority_level: str | None = None
    suggested_specialty_id: int | None = None
    visible_damage_detected: str | None = None
    predicted_requires_tow: bool | None = None
    confidence_score: float | None = None
    raw_response_json: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
