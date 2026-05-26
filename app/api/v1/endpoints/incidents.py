from datetime import datetime

from fastapi import APIRouter, Response

from app.api.deps import AdminTallerOrSuperAdmin, ClienteUser, CurrentUser, DbSession
from app.schemas.incident import IncidentCreate, IncidentRead, IncidentUpdate
from app.schemas.location_track import LocationTrackCreate, LocationTrackRead
from app.services.incident_service import IncidentService
from app.services.location_track_service import LocationTrackService

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post("", response_model=IncidentRead, status_code=201)
async def create_incident(
    data: IncidentCreate, session: DbSession, _user: ClienteUser, response: Response
):
    """Crea un incidente. Si se envía `client_uuid` y ya existe, retorna 409 con el existente."""
    svc = IncidentService(session)
    incident, created = await svc.create(data)
    if not created:
        response.status_code = 409
    return incident


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


# ── Location tracking (CU26/CU27) ─────────────────────────────


@router.post("/{incident_id}/locations", response_model=LocationTrackRead, status_code=201)
async def add_location(
    incident_id: int,
    data: LocationTrackCreate,
    session: DbSession,
    _user: AdminTallerOrSuperAdmin,
):
    """Registra la posición GPS del técnico en ruta hacia el incidente.

    Emite evento `incident.location_updated` vía WebSocket a todos los
    suscriptores del canal `incident:{id}`.
    """
    svc = LocationTrackService(session)
    return await svc.add_point(incident_id, data.latitude, data.longitude)


@router.get("/{incident_id}/locations", response_model=list[LocationTrackRead])
async def get_locations(
    incident_id: int,
    session: DbSession,
    _user: CurrentUser,
    since: datetime | None = None,
):
    """Devuelve el historial de posiciones GPS de un incidente.

    - **since**: ISO 8601 timestamp. Si se especifica, solo retorna puntos posteriores.
    """
    svc = LocationTrackService(session)
    return await svc.get_points(incident_id, since=since)
