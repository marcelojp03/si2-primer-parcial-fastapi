from fastapi import APIRouter

from app.api.deps import AdminTallerOrSuperAdmin, CurrentUser, DbSession
from app.schemas.technician_specialty import TechnicianSpecialtyCreate, TechnicianSpecialtyRead
from app.services.technician_specialty_service import TechnicianSpecialtyService

router = APIRouter(prefix="/technician-specialties", tags=["technician-specialties"])


@router.post("", response_model=TechnicianSpecialtyRead, status_code=201)
async def create_technician_specialty(
    data: TechnicianSpecialtyCreate, session: DbSession, _user: AdminTallerOrSuperAdmin
):
    svc = TechnicianSpecialtyService(session)
    return await svc.create(data)


@router.get("/technician/{technician_id}", response_model=list[TechnicianSpecialtyRead])
async def list_specialties_by_technician(
    technician_id: int, session: DbSession, _user: CurrentUser
):
    svc = TechnicianSpecialtyService(session)
    return await svc.get_by_technician(technician_id)


@router.delete("/{ts_id}", status_code=204)
async def delete_technician_specialty(
    ts_id: int, session: DbSession, _user: AdminTallerOrSuperAdmin
):
    svc = TechnicianSpecialtyService(session)
    await svc.delete(ts_id)
