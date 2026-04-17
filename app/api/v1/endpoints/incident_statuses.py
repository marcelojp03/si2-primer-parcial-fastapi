from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, SuperAdminUser
from app.schemas.incident_status import (
    IncidentStatusCreate,
    IncidentStatusRead,
    IncidentStatusUpdate,
)
from app.services.incident_status_service import IncidentStatusService

router = APIRouter(prefix="/incident-statuses", tags=["incident-statuses"])


@router.post("", response_model=IncidentStatusRead, status_code=201)
async def create_incident_status(
    data: IncidentStatusCreate, session: DbSession, _admin: SuperAdminUser
):
    svc = IncidentStatusService(session)
    return await svc.create(data)


@router.get("/{status_id}", response_model=IncidentStatusRead)
async def read_incident_status(status_id: int, session: DbSession, _current_user: CurrentUser):
    svc = IncidentStatusService(session)
    return await svc.get_by_id(status_id)


@router.get("", response_model=list[IncidentStatusRead])
async def list_incident_statuses(
    session: DbSession, _current_user: CurrentUser, skip: int = 0, limit: int = 100
):
    svc = IncidentStatusService(session)
    return await svc.get_all(skip=skip, limit=limit)


@router.patch("/{status_id}", response_model=IncidentStatusRead)
async def update_incident_status(
    status_id: int, data: IncidentStatusUpdate, session: DbSession, _admin: SuperAdminUser
):
    svc = IncidentStatusService(session)
    return await svc.update(status_id, data)
