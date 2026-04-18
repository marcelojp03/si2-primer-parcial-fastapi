from fastapi import APIRouter

from app.api.deps import AdminTallerOrSuperAdmin, CurrentUser, DbSession
from app.schemas.workshop_schedule import (
    WorkshopScheduleCreate,
    WorkshopScheduleRead,
    WorkshopScheduleUpdate,
)
from app.services.workshop_schedule_service import WorkshopScheduleService

router = APIRouter(prefix="/workshop-schedules", tags=["workshop-schedules"])


@router.post("", response_model=WorkshopScheduleRead, status_code=201)
async def create_schedule(
    data: WorkshopScheduleCreate, session: DbSession, _user: AdminTallerOrSuperAdmin
):
    svc = WorkshopScheduleService(session)
    return await svc.create(data)


@router.get("/workshop/{workshop_id}", response_model=list[WorkshopScheduleRead])
async def list_schedules_by_workshop(workshop_id: int, session: DbSession, _user: CurrentUser):
    svc = WorkshopScheduleService(session)
    return await svc.get_by_workshop(workshop_id)


@router.get("/{schedule_id}", response_model=WorkshopScheduleRead)
async def read_schedule(schedule_id: int, session: DbSession, _user: CurrentUser):
    svc = WorkshopScheduleService(session)
    return await svc.get_by_id(schedule_id)


@router.patch("/{schedule_id}", response_model=WorkshopScheduleRead)
async def update_schedule(
    schedule_id: int,
    data: WorkshopScheduleUpdate,
    session: DbSession,
    _user: AdminTallerOrSuperAdmin,
):
    svc = WorkshopScheduleService(session)
    return await svc.update(schedule_id, data)


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule(schedule_id: int, session: DbSession, _user: AdminTallerOrSuperAdmin):
    svc = WorkshopScheduleService(session)
    await svc.delete(schedule_id)
