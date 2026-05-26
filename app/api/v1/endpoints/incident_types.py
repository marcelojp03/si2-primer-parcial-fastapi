from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, PlatformAdminUser, SuperAdminUser
from app.schemas.incident_type import IncidentTypeCreate, IncidentTypeRead, IncidentTypeUpdate, SLAUpdate
from app.services.incident_type_service import IncidentTypeService

router = APIRouter(prefix="/incident-types", tags=["incident-types"])


@router.post("", response_model=IncidentTypeRead, status_code=201)
async def create_incident_type(
    data: IncidentTypeCreate, session: DbSession, _admin: SuperAdminUser
):
    svc = IncidentTypeService(session)
    return await svc.create(data)


@router.get("/{type_id}", response_model=IncidentTypeRead)
async def read_incident_type(type_id: int, session: DbSession, _current_user: CurrentUser):
    svc = IncidentTypeService(session)
    return await svc.get_by_id(type_id)


@router.get("", response_model=list[IncidentTypeRead])
async def list_incident_types(
    session: DbSession, _current_user: CurrentUser, skip: int = 0, limit: int = 100
):
    svc = IncidentTypeService(session)
    return await svc.get_all(skip=skip, limit=limit)


@router.patch("/{type_id}", response_model=IncidentTypeRead)
async def update_incident_type(
    type_id: int, data: IncidentTypeUpdate, session: DbSession, _admin: SuperAdminUser
):
    svc = IncidentTypeService(session)
    return await svc.update(type_id, data)


@router.patch("/{type_id}/sla", response_model=IncidentTypeRead)
async def configure_sla(
    type_id: int, data: SLAUpdate, session: DbSession, _admin: PlatformAdminUser
):
    """Configura el SLA (en minutos) para un tipo de incidente. Solo ADMIN_PLATAFORMA."""
    svc = IncidentTypeService(session)
    return await svc.update(type_id, IncidentTypeUpdate(sla_minutes=data.sla_minutes))
