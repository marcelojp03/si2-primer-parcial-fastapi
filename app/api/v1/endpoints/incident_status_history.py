from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.incident_status_history import (
    IncidentStatusHistoryCreate,
    IncidentStatusHistoryRead,
)
from app.services.incident_status_history_service import IncidentStatusHistoryService

router = APIRouter(prefix="/incident-status-history", tags=["incident-status-history"])


@router.post("", response_model=IncidentStatusHistoryRead, status_code=201)
async def create_status_history(
    data: IncidentStatusHistoryCreate, session: DbSession, _user: CurrentUser
):
    svc = IncidentStatusHistoryService(session)
    return await svc.create(data)


@router.get("/incident/{incident_id}", response_model=list[IncidentStatusHistoryRead])
async def list_history_by_incident(incident_id: int, session: DbSession, _user: CurrentUser):
    svc = IncidentStatusHistoryService(session)
    return await svc.get_by_incident(incident_id)
