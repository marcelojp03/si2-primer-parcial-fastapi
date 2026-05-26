from fastapi import APIRouter

from app.api.deps import AdminTallerOrSuperAdmin, CurrentUser, DbSession, TenantId
from app.schemas.workshop import WorkshopCreate, WorkshopRead, WorkshopUpdate
from app.services.workshop_service import WorkshopService

router = APIRouter(prefix="/workshops", tags=["workshops"])


@router.post("", response_model=WorkshopRead, status_code=201)
async def create_workshop(
    data: WorkshopCreate,
    session: DbSession,
    _user: AdminTallerOrSuperAdmin,
    tenant_id: TenantId,
):
    svc = WorkshopService(session)
    return await svc.create(data, tenant_id=tenant_id)


@router.get("/{workshop_id}", response_model=WorkshopRead)
async def read_workshop(workshop_id: int, session: DbSession, _current_user: CurrentUser):
    svc = WorkshopService(session)
    return await svc.get_by_id(workshop_id)


@router.get("", response_model=list[WorkshopRead])
async def list_workshops(
    session: DbSession, _current_user: CurrentUser, skip: int = 0, limit: int = 100
):
    svc = WorkshopService(session)
    return await svc.get_all(skip=skip, limit=limit)


@router.patch("/{workshop_id}", response_model=WorkshopRead)
async def update_workshop(
    workshop_id: int, data: WorkshopUpdate, session: DbSession, _user: AdminTallerOrSuperAdmin
):
    svc = WorkshopService(session)
    return await svc.update(workshop_id, data)
