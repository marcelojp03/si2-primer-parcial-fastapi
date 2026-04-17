from fastapi import APIRouter

from app.api.deps import AdminTallerOrSuperAdmin, CurrentUser, DbSession
from app.schemas.technician import TechnicianCreate, TechnicianRead, TechnicianUpdate
from app.services.technician_service import TechnicianService

router = APIRouter(prefix="/technicians", tags=["technicians"])


@router.post("", response_model=TechnicianRead, status_code=201)
async def create_technician(data: TechnicianCreate, session: DbSession, _user: AdminTallerOrSuperAdmin):
    svc = TechnicianService(session)
    return await svc.create(data)


@router.get("/{technician_id}", response_model=TechnicianRead)
async def read_technician(technician_id: int, session: DbSession, _current_user: CurrentUser):
    svc = TechnicianService(session)
    return await svc.get_by_id(technician_id)


@router.get("/workshop/{workshop_id}", response_model=list[TechnicianRead])
async def list_technicians_by_workshop(workshop_id: int, session: DbSession, _current_user: CurrentUser):
    svc = TechnicianService(session)
    return await svc.get_by_workshop_id(workshop_id)


@router.patch("/{technician_id}", response_model=TechnicianRead)
async def update_technician(technician_id: int, data: TechnicianUpdate, session: DbSession, _user: AdminTallerOrSuperAdmin):
    svc = TechnicianService(session)
    return await svc.update(technician_id, data)
