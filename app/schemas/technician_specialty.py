from datetime import datetime

from pydantic import BaseModel


class TechnicianSpecialtyBase(BaseModel):
    technician_id: int
    specialty_id: int


class TechnicianSpecialtyCreate(TechnicianSpecialtyBase):
    pass


class TechnicianSpecialtyRead(TechnicianSpecialtyBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
