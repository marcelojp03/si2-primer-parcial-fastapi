from fastapi import APIRouter

from app.api.deps import AdminTallerOrSuperAdmin, ClienteUser, CurrentUser, DbSession
from app.schemas.incident import IncidentCreate, IncidentRead, IncidentUpdate
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post("", response_model=IncidentRead, status_code=201)
async def create_incident(data: IncidentCreate, session: DbSession, _user: ClienteUser):
    svc = IncidentService(session)
    return await svc.create(data)


@router.get("/{incident_id}", response_model=IncidentRead)
async def read_incident(incident_id: int, session: DbSession, _current_user: CurrentUser):
    svc = IncidentService(session)
    return await svc.get_by_id(incident_id)


@router.get("", response_model=list[IncidentRead])
async def list_incidents(
    session: DbSession,
    _current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    status_id: int | None = None,
    client_user_id: int | None = None,
    priority: str | None = None,
):
    svc = IncidentService(session)
    return await svc.get_filtered(
        skip=skip,
        limit=limit,
        status_id=status_id,
        client_user_id=client_user_id,
        priority=priority,
    )


@router.patch("/{incident_id}", response_model=IncidentRead)
async def update_incident(
    incident_id: int, data: IncidentUpdate, session: DbSession, _user: AdminTallerOrSuperAdmin
):
    svc = IncidentService(session)
    return await svc.update(incident_id, data)
