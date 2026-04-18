from fastapi import APIRouter

from app.api.deps import AdminTallerOrSuperAdmin, CurrentUser, DbSession
from app.schemas.assignment import AssignmentRead, AssignmentUpdate
from app.schemas.workshop_candidate import WorkshopCandidateRead, WorkshopCandidateUpdate
from app.services.assignment_service import AssignmentService

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.post("/{incident_id}/candidates", response_model=list[WorkshopCandidateRead])
async def find_candidates(
    incident_id: int,
    session: DbSession,
    _user: AdminTallerOrSuperAdmin,
    max_distance_km: float = 50.0,
):
    """Find and score candidate workshops for an incident."""
    svc = AssignmentService(session)
    return await svc.find_candidates(incident_id, max_distance_km=max_distance_km)


@router.post(
    "/{incident_id}/candidates/{workshop_id}/respond", response_model=WorkshopCandidateRead
)
async def respond_candidate(
    incident_id: int,
    workshop_id: int,
    data: WorkshopCandidateUpdate,
    session: DbSession,
    _user: AdminTallerOrSuperAdmin,
):
    """Workshop accepts or rejects a candidate invitation."""
    svc = AssignmentService(session)
    return await svc.respond_candidate(
        incident_id, workshop_id, data.response_status, data.response_note
    )


@router.post("/{incident_id}/assign", response_model=AssignmentRead)
async def assign_workshop(
    incident_id: int,
    session: DbSession,
    user: AdminTallerOrSuperAdmin,
):
    """Assign the best candidate workshop to an incident."""
    svc = AssignmentService(session)
    return await svc.assign_best(incident_id, user_id=user.id)


@router.get("/{incident_id}", response_model=AssignmentRead)
async def get_assignment(
    incident_id: int,
    session: DbSession,
    _user: CurrentUser,
):
    """Get the assignment for an incident."""
    from app.repositories.assignment_repository import AssignmentRepository

    repo = AssignmentRepository(session)
    assignment = await repo.get_by_incident(incident_id)
    if not assignment:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("No assignment found for this incident")
    return assignment


@router.patch("/{assignment_id}/status", response_model=AssignmentRead)
async def update_assignment(
    assignment_id: int,
    data: AssignmentUpdate,
    session: DbSession,
    _user: AdminTallerOrSuperAdmin,
):
    """Update assignment status (e.g. EN_CAMINO, EN_PROCESO, COMPLETADO)."""
    from app.core.exceptions import NotFoundError
    from app.repositories.assignment_repository import AssignmentRepository

    repo = AssignmentRepository(session)
    assignment = await repo.get_by_id(assignment_id)
    if not assignment:
        raise NotFoundError("Assignment not found")
    return await repo.update(assignment, data.model_dump(exclude_unset=True))


@router.get("/{incident_id}/candidates", response_model=list[WorkshopCandidateRead])
async def list_candidates(
    incident_id: int,
    session: DbSession,
    _user: CurrentUser,
):
    """List all candidate workshops for an incident."""
    from app.repositories.workshop_candidate_repository import WorkshopCandidateRepository

    repo = WorkshopCandidateRepository(session)
    return await repo.get_by_incident(incident_id)
