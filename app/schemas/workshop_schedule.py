from datetime import datetime, time

from pydantic import BaseModel, Field


class WorkshopScheduleBase(BaseModel):
    weekday: str = Field(..., max_length=20)
    start_time: time
    end_time: time
    active: bool = True


class WorkshopScheduleCreate(WorkshopScheduleBase):
    workshop_id: int


class WorkshopScheduleUpdate(BaseModel):
    weekday: str | None = Field(None, max_length=20)
    start_time: time | None = None
    end_time: time | None = None
    active: bool | None = None


class WorkshopScheduleRead(WorkshopScheduleBase):
    id: int
    workshop_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
