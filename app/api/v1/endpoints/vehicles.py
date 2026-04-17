from fastapi import APIRouter

from app.api.deps import ClienteOrSuperAdmin, CurrentUser, DbSession
from app.schemas.vehicle import VehicleCreate, VehicleRead, VehicleUpdate
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.post("", response_model=VehicleRead, status_code=201)
async def create_vehicle(data: VehicleCreate, session: DbSession, _user: ClienteOrSuperAdmin):
    svc = VehicleService(session)
    return await svc.create(data)


@router.get("/{vehicle_id}", response_model=VehicleRead)
async def read_vehicle(vehicle_id: int, session: DbSession, _current_user: CurrentUser):
    svc = VehicleService(session)
    return await svc.get_by_id(vehicle_id)


@router.get("", response_model=list[VehicleRead])
async def list_my_vehicles(session: DbSession, current_user: CurrentUser):
    svc = VehicleService(session)
    return await svc.get_by_user_id(current_user.id)


@router.patch("/{vehicle_id}", response_model=VehicleRead)
async def update_vehicle(
    vehicle_id: int, data: VehicleUpdate, session: DbSession, _user: ClienteOrSuperAdmin
):
    svc = VehicleService(session)
    return await svc.update(vehicle_id, data)
