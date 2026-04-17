from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, SuperAdminUser
from app.schemas.specialty import SpecialtyCreate, SpecialtyRead, SpecialtyUpdate
from app.services.specialty_service import SpecialtyService

router = APIRouter(prefix="/specialties", tags=["specialties"])


@router.post("", response_model=SpecialtyRead, status_code=201)
async def create_specialty(data: SpecialtyCreate, session: DbSession, _admin: SuperAdminUser):
    svc = SpecialtyService(session)
    return await svc.create(data)


@router.get("/{specialty_id}", response_model=SpecialtyRead)
async def read_specialty(specialty_id: int, session: DbSession, _current_user: CurrentUser):
    svc = SpecialtyService(session)
    return await svc.get_by_id(specialty_id)


@router.get("", response_model=list[SpecialtyRead])
async def list_specialties(
    session: DbSession, _current_user: CurrentUser, skip: int = 0, limit: int = 100
):
    svc = SpecialtyService(session)
    return await svc.get_all(skip=skip, limit=limit)


@router.patch("/{specialty_id}", response_model=SpecialtyRead)
async def update_specialty(
    specialty_id: int, data: SpecialtyUpdate, session: DbSession, _admin: SuperAdminUser
):
    svc = SpecialtyService(session)
    return await svc.update(specialty_id, data)
