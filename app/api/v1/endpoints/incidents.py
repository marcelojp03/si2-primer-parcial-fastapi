from datetime import datetime

from fastapi import APIRouter, Response
from sqlalchemy import select

from app.api.deps import AdminTallerOrSuperAdmin, AdminTallerTecnicoOrSuperAdmin, ClienteUser, CurrentUser, DbSession
from app.core.exceptions import ForbiddenError
from app.models.incident import Incident
from app.models.service_assignment import ServiceAssignment
from app.models.workshop import Workshop
from app.models.workshop_candidate import WorkshopCandidate
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
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    status_id: int | None = None,
    priority: str | None = None,
):
    role = current_user.role.lower()
    svc = IncidentService(session)

    if role == "cliente":
        return await svc.get_filtered(
            skip=skip,
            limit=limit,
            status_id=status_id,
            client_user_id=current_user.id,
            priority=priority,
        )

    if role == "admin_taller":
        workshop_result = await session.execute(
            select(Workshop).where(Workshop.admin_user_id == current_user.id)
        )
        workshop = workshop_result.scalar_one_or_none()
        if not workshop:
            return []

        tenant_workshop_ids_subq = (
            select(Workshop.id).where(Workshop.tenant_id == workshop.tenant_id).subquery()
        )
        stmt = select(Incident).distinct()
        stmt = stmt.outerjoin(
            WorkshopCandidate,
            WorkshopCandidate.incident_id == Incident.id,
        ).outerjoin(
            ServiceAssignment,
            ServiceAssignment.incident_id == Incident.id,
        )
        stmt = stmt.where(
            (WorkshopCandidate.workshop_id.in_(select(tenant_workshop_ids_subq)))
            | (ServiceAssignment.workshop_id.in_(select(tenant_workshop_ids_subq)))
        )
        if status_id is not None:
            stmt = stmt.where(Incident.incident_status_id == status_id)
        if priority is not None:
            stmt = stmt.where(Incident.priority_level == priority)
        stmt = stmt.order_by(Incident.id.desc()).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

    return await svc.get_filtered(
        skip=skip,
        limit=limit,
        status_id=status_id,
        priority=priority,
    )


@router.patch("/{incident_id}", response_model=IncidentRead)
async def update_incident(
    incident_id: int, data: IncidentUpdate, session: DbSession, _user: AdminTallerOrSuperAdmin
):
    svc = IncidentService(session)
    return await svc.update(incident_id, data)


@router.post("/{incident_id}/cancel", response_model=IncidentRead)
async def cancel_incident(
    incident_id: int,
    session: DbSession,
    current_user: CurrentUser,
):
    """Cancel an incident. The client can only cancel their own incidents."""
    from app.core.exceptions import ForbiddenError
    from app.models.incident_status import IncidentStatus
    from app.services.incident_service import IncidentService
    from sqlalchemy import select

    svc = IncidentService(session)
    incident = await svc.get_by_id(incident_id)
    if incident.client_user_id != current_user.id:
        raise ForbiddenError("You can only cancel your own incidents")
    result = await session.execute(
        select(IncidentStatus.id).where(IncidentStatus.name == "CANCELADO").limit(1)
    )
    status_id = result.scalar_one_or_none()
    if status_id:
        return await svc.update(incident_id, IncidentUpdate(incident_status_id=status_id))
    return incident


# ── Location tracking (CU26/CU27) ─────────────────────────────


@router.post("/{incident_id}/locations", response_model=LocationTrackRead, status_code=201)
async def add_location(
    incident_id: int,
    data: LocationTrackCreate,
    session: DbSession,
    current_user: CurrentUser,
):
    """Registra la posición GPS del técnico en ruta hacia el incidente.

    Emite evento `incident.location_updated` vía WebSocket a todos los
    suscriptores del canal `incident:{id}`.
    - Si el usuario es TECNICO, valida que esté asignado al incidente.
    """
    svc = LocationTrackService(session)
    return await svc.add_point(incident_id, data.latitude, data.longitude, user=current_user)


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
