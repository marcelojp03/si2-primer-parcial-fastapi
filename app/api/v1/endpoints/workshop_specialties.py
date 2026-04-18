from fastapi import APIRouter

from app.api.deps import AdminTallerOrSuperAdmin, CurrentUser, DbSession
from app.schemas.workshop_specialty import WorkshopSpecialtyCreate, WorkshopSpecialtyRead
from app.services.workshop_specialty_service import WorkshopSpecialtyService

router = APIRouter(prefix="/workshop-specialties", tags=["workshop-specialties"])


@router.post("", response_model=WorkshopSpecialtyRead, status_code=201)
async def create_workshop_specialty(
    data: WorkshopSpecialtyCreate, session: DbSession, _user: AdminTallerOrSuperAdmin
):
    svc = WorkshopSpecialtyService(session)
    return await svc.create(data)


@router.get("/workshop/{workshop_id}", response_model=list[WorkshopSpecialtyRead])
async def list_specialties_by_workshop(workshop_id: int, session: DbSession, _user: CurrentUser):
    svc = WorkshopSpecialtyService(session)
    return await svc.get_by_workshop(workshop_id)


@router.delete("/{ws_id}", status_code=204)
async def delete_workshop_specialty(ws_id: int, session: DbSession, _user: AdminTallerOrSuperAdmin):
    svc = WorkshopSpecialtyService(session)
    await svc.delete(ws_id)
