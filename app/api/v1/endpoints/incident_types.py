from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, SuperAdminUser
from app.schemas.incident_type import IncidentTypeCreate, IncidentTypeRead, IncidentTypeUpdate
from app.services.incident_type_service import IncidentTypeService

router = APIRouter(prefix="/incident-types", tags=["incident-types"])


@router.post("", response_model=IncidentTypeRead, status_code=201)
async def create_incident_type(data: IncidentTypeCreate, session: DbSession, _admin: SuperAdminUser):
    svc = IncidentTypeService(session)
    return await svc.create(data)


@router.get("/{type_id}", response_model=IncidentTypeRead)
async def read_incident_type(type_id: int, session: DbSession, _current_user: CurrentUser):
    svc = IncidentTypeService(session)
    return await svc.get_by_id(type_id)


@router.get("", response_model=list[IncidentTypeRead])
async def list_incident_types(session: DbSession, _current_user: CurrentUser, skip: int = 0, limit: int = 100):
    svc = IncidentTypeService(session)
    return await svc.get_all(skip=skip, limit=limit)


@router.patch("/{type_id}", response_model=IncidentTypeRead)
async def update_incident_type(type_id: int, data: IncidentTypeUpdate, session: DbSession, _admin: SuperAdminUser):
    svc = IncidentTypeService(session)
    return await svc.update(type_id, data)
