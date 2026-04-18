from datetime import datetime

from pydantic import BaseModel


class WorkshopSpecialtyBase(BaseModel):
    workshop_id: int
    specialty_id: int


class WorkshopSpecialtyCreate(WorkshopSpecialtyBase):
    pass


class WorkshopSpecialtyRead(WorkshopSpecialtyBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
