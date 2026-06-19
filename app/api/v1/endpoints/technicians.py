from fastapi import APIRouter

from app.api.deps import AdminTallerOrSuperAdmin, CurrentUser, DbSession
from app.schemas.assignment import AssignmentRead
from app.schemas.technician import TechnicianCreate, TechnicianRead, TechnicianUpdate
from app.services.technician_service import TechnicianService

router = APIRouter(prefix="/technicians", tags=["technicians"])


@router.post("", response_model=TechnicianRead, status_code=201)
async def create_technician(
    data: TechnicianCreate, session: DbSession, _user: AdminTallerOrSuperAdmin
):
    svc = TechnicianService(session)
    return await svc.create(data)


@router.get("/{technician_id}", response_model=TechnicianRead)
async def read_technician(technician_id: int, session: DbSession, _current_user: CurrentUser):
    svc = TechnicianService(session)
    return await svc.get_by_id(technician_id)


@router.get("/workshop/{workshop_id}", response_model=list[TechnicianRead])
async def list_technicians_by_workshop(
    workshop_id: int, session: DbSession, _current_user: CurrentUser
):
    svc = TechnicianService(session)
    return await svc.get_by_workshop_id(workshop_id)


@router.patch("/{technician_id}", response_model=TechnicianRead)
async def update_technician(
    technician_id: int, data: TechnicianUpdate, session: DbSession, _user: AdminTallerOrSuperAdmin
):
    svc = TechnicianService(session)
    return await svc.update(technician_id, data)


# ── Technician endpoints (para el modo técnico) ──────────────


@router.get("/me", response_model=TechnicianRead)
async def get_my_technician_profile(
    session: DbSession,
    current_user: CurrentUser,
):
    """Get the technician profile linked to the authenticated user."""
    from app.repositories.technician_repository import TechnicianRepository

    repo = TechnicianRepository(session)
    tech = await repo.get_by_user_id(current_user.id)
    if not tech:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Technician profile not found for this user")
    return tech


@router.get("/me/assignments", response_model=list[AssignmentRead])
async def get_my_assignments(
    session: DbSession,
    current_user: CurrentUser,
):
    """Get active assignments for the authenticated technician."""
    from app.repositories.assignment_repository import AssignmentRepository
    from app.repositories.technician_repository import TechnicianRepository

    tech_repo = TechnicianRepository(session)
    tech = await tech_repo.get_by_user_id(current_user.id)
    if not tech:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Technician profile not found")

    assign_repo = AssignmentRepository(session)
    from app.models.service_assignment import ServiceAssignment
    from sqlalchemy import select

    stmt = (
        select(ServiceAssignment)
        .where(
            ServiceAssignment.technician_id == tech.id,
            ServiceAssignment.assignment_status.in_(["ASIGNADO", "EN_CAMINO", "EN_SITIO", "EN_PROCESO"]),
        )
        .order_by(ServiceAssignment.assigned_at.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()
