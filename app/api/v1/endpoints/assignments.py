from fastapi import APIRouter

from app.api.deps import AdminTallerOrSuperAdmin, CurrentUser, DbSession
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.workshop import Workshop
from app.models.workshop_candidate import WorkshopCandidate
from app.schemas.assignment import AssignmentRead, AssignmentUpdate
from app.schemas.quotation import QuotationCreate, QuotationRespond
from app.schemas.workshop_candidate import WorkshopCandidateRead, WorkshopCandidateUpdate
from app.services.assignment_service import AssignmentService
from sqlalchemy import select

router = APIRouter(prefix="/assignments", tags=["assignments"])


def _tenant_scope_for_assignment(user) -> int | None:
    if user.role.lower() != "admin_taller":
        return None
    if user.tenant_id is None:
        raise ForbiddenError("Tenant-scoped workshop administrator required")
    return user.tenant_id


@router.get("/invitations/pending", response_model=list[WorkshopCandidateRead])
async def get_pending_invitations(session: DbSession, user: AdminTallerOrSuperAdmin):
    """List pending invitations for the workshop administered by the current user."""
    workshop_result = await session.execute(
        select(Workshop).where(Workshop.admin_user_id == user.id)
    )
    workshop = workshop_result.scalar_one_or_none()
    if not workshop:
        raise NotFoundError("Workshop not found for current user")

    candidates_result = await session.execute(
        select(WorkshopCandidate)
        .where(
            WorkshopCandidate.workshop_id == workshop.id,
            WorkshopCandidate.response_status == "PENDIENTE",
            WorkshopCandidate.notified.is_(True),
        )
        .order_by(WorkshopCandidate.invitation_deadline.asc())
    )
    return candidates_result.scalars().all()


@router.post("/{incident_id}/candidates", response_model=list[WorkshopCandidateRead])
async def find_candidates(
    incident_id: int,
    session: DbSession,
    _user: AdminTallerOrSuperAdmin,
    max_distance_km: float = 50.0,
    max_candidates: int = 5,
    ttl_minutes: int = 15,
):
    """Find and score candidate workshops for an incident.

    - **max_distance_km**: Radio máximo en km para considerar talleres (default 50).
    - **max_candidates**: Cantidad máxima de talleres a notificar (0 = sin límite, default 5).
    - **ttl_minutes**: Minutos que tiene el taller para responder la invitación (default 15).
    """
    svc = AssignmentService(session)
    return await svc.find_candidates(
        incident_id,
        max_distance_km=max_distance_km,
        max_candidates=max_candidates,
        ttl_minutes=ttl_minutes,
    )


@router.post(
    "/{incident_id}/candidates/{workshop_id}/respond", response_model=WorkshopCandidateRead
)
async def respond_candidate(
    incident_id: int,
    workshop_id: int,
    data: WorkshopCandidateUpdate,
    session: DbSession,
    user: AdminTallerOrSuperAdmin,
):
    """Workshop accepts or rejects a candidate invitation.
    When accepting, can optionally include quotation data (cost, time, description)."""
    svc = AssignmentService(session)
    return await svc.respond_candidate(
        incident_id,
        workshop_id,
        data.response_status,
        data.response_note,
        quotation_cost=data.quotation_estimated_cost,
        quotation_minutes=data.quotation_completion_minutes,
        quotation_description=data.quotation_description,
        actor_tenant_id=_tenant_scope_for_assignment(user),
        actor_user_id=user.id,
    )


@router.post("/{incident_id}/assign", response_model=AssignmentRead)
async def assign_workshop(
    incident_id: int,
    session: DbSession,
    user: AdminTallerOrSuperAdmin,
):
    """Assign the best candidate workshop to an incident."""
    svc = AssignmentService(session)
    return await svc.assign_best(
        incident_id,
        user_id=user.id,
        actor_tenant_id=_tenant_scope_for_assignment(user),
    )


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
    current_user: CurrentUser,
):
    """Update assignment status (e.g. EN_CAMINO, EN_PROCESO, COMPLETADO)."""
    from app.core.exceptions import ForbiddenError, NotFoundError
    from app.models.incident import Incident
    from app.models.user import User
    from app.models.workshop import Workshop
    from app.repositories.assignment_repository import AssignmentRepository
    from app.repositories.incident_repository import IncidentRepository
    from app.schemas.notification import NotificationCreate
    from app.services.notification_service import NotificationService
    from app.ws.events import IncidentStatusChangedPayload, build_message
    from app.ws.manager import ws_manager
    from sqlalchemy import select

    repo = AssignmentRepository(session)
    assignment = await repo.get_by_id(assignment_id)
    if not assignment:
        raise NotFoundError("Assignment not found")

    # Tenant isolation: ADMIN_TALLER solo puede modificar asignaciones de su tenant
    role = current_user.role.lower()
    if role == "admin_taller":
        if current_user.tenant_id is None:
            raise ForbiddenError("Tenant-scoped workshop administrator required")
        ws_result = await session.execute(
            select(Workshop.tenant_id).where(Workshop.id == assignment.workshop_id)
        )
        ws_tenant = ws_result.scalar_one_or_none()
        if ws_tenant != current_user.tenant_id:
            raise ForbiddenError("Cannot modify assignments outside your tenant")

    # Technician isolation: TECNICO solo puede modificar sus propias asignaciones
    if role == "tecnico":
        from app.repositories.technician_repository import TechnicianRepository

        tech_repo = TechnicianRepository(session)
        tech = await tech_repo.get_by_user_id(current_user.id)
        if not tech or assignment.technician_id != tech.id:
            raise ForbiddenError("You can only modify your own assignments")

    old_status = assignment.assignment_status
    updated = await repo.update(assignment, data.model_dump(exclude_unset=True))

    if data.assignment_status and data.assignment_status != old_status:
        incident_repo = IncidentRepository(session)
        incident = await incident_repo.get_by_id(assignment.incident_id)
        if incident:
            payload = IncidentStatusChangedPayload(
                incident_id=assignment.incident_id,
                old_status=old_status,
                new_status=data.assignment_status,
            )
            msg = build_message("incident.status_changed", payload)
            await ws_manager.send_to_incident(assignment.incident_id, msg)
            await ws_manager.send_to_user(incident.client_user_id, msg)

            # FCM push notifications for key status changes
            push_titles = {
                "EN_CAMINO": "Auxilio en camino",
                "EN_SITIO": "Auxilio en sitio",
                "EN_PROCESO": "Atención en curso",
                "COMPLETADO": "Servicio completado",
            }
            push_messages = {
                "EN_CAMINO": "El auxilio está en camino hacia tu ubicación.",
                "EN_SITIO": "El auxilio ha llegado a tu ubicación.",
                "EN_PROCESO": "El taller está trabajando en tu vehículo.",
                "COMPLETADO": "El servicio ha sido completado. Procede al pago.",
            }
            if data.assignment_status in push_messages:
                result = await session.execute(
                    select(User).where(User.id == incident.client_user_id)
                )
                client_user = result.scalar_one_or_none()
                if client_user:
                    notif_data = NotificationCreate(
                        user_id=incident.client_user_id,
                        incident_id=assignment.incident_id,
                        notification_type="assignment_status",
                        channel="PUSH",
                        title=push_titles[data.assignment_status],
                        message=push_messages[data.assignment_status],
                    )
                    notif_svc = NotificationService(session)
                    await notif_svc.create_and_push(notif_data, device_token=client_user.fcm_token)

    return updated


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


# ── Selección de taller por el cliente ────────────────────────


@router.post("/{incident_id}/select-workshop/{workshop_id}", response_model=AssignmentRead)
async def select_workshop(
    incident_id: int,
    workshop_id: int,
    session: DbSession,
    current_user: CurrentUser,
):
    """Client selects a workshop that accepted their incident. Creates the assignment."""
    from app.services.assignment_service import AssignmentService

    svc = AssignmentService(session)
    return await svc.select_workshop(incident_id, workshop_id, client_user_id=current_user.id)


@router.get("/{incident_id}/accepted-candidates", response_model=list[WorkshopCandidateRead])
async def list_accepted_candidates(
    incident_id: int,
    session: DbSession,
    _user: CurrentUser,
):
    """List workshops that have accepted the invitation (for client selection)."""
    from app.repositories.workshop_candidate_repository import WorkshopCandidateRepository

    repo = WorkshopCandidateRepository(session)
    candidates = await repo.get_by_incident(incident_id)
    return [c for c in candidates if c.response_status == "ACEPTADO"]


# ── Cotizaciones ──────────────────────────────────────────────


@router.post("/{assignment_id}/quote", response_model=AssignmentRead)
async def submit_quote(
    assignment_id: int,
    data: QuotationCreate,
    session: DbSession,
    _user: AdminTallerOrSuperAdmin,
):
    """Workshop submits a quotation (estimated cost, time, description) for an assignment."""
    from app.repositories.assignment_repository import AssignmentRepository

    repo = AssignmentRepository(session)
    assignment = await repo.get_by_id(assignment_id)
    if not assignment:
        raise NotFoundError("Assignment not found")

    update_data = data.model_dump()
    update_data["quotation_status"] = "PENDIENTE"
    return await repo.update(assignment, update_data)


@router.patch("/{assignment_id}/quote/respond", response_model=AssignmentRead)
async def respond_quote(
    assignment_id: int,
    data: QuotationRespond,
    session: DbSession,
    _user: CurrentUser,
):
    """Client approves or rejects a quotation."""
    from app.repositories.assignment_repository import AssignmentRepository

    repo = AssignmentRepository(session)
    assignment = await repo.get_by_id(assignment_id)
    if not assignment:
        raise NotFoundError("Assignment not found")

    return await repo.update(assignment, {"quotation_status": data.status})
