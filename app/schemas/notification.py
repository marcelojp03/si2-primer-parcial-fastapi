from datetime import datetime

from pydantic import BaseModel, Field


class NotificationBase(BaseModel):
    user_id: int | None = None
    incident_id: int | None = None
    notification_type: str = Field(..., max_length=50)
    channel: str = Field(..., max_length=30)
    title: str = Field(..., max_length=150)
    message: str = Field(..., max_length=255)
    extra_data_json: str | None = None


class NotificationCreate(NotificationBase):
    pass


class NotificationRead(NotificationBase):
    id: int
    status: str
    sent_at: datetime | None
    read_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
