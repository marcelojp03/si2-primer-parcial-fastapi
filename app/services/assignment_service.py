import logging
import math
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.incident import Incident
from app.models.incident_status import IncidentStatus
from app.models.incident_status_history import IncidentStatusHistory
from app.models.service_assignment import ServiceAssignment
from app.models.workshop import Workshop
from app.models.workshop_candidate import WorkshopCandidate
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.workshop_candidate_repository import WorkshopCandidateRepository
from app.repositories.workshop_repository import WorkshopRepository
from app.repositories.workshop_specialty_repository import WorkshopSpecialtyRepository
from app.schemas.notification import NotificationCreate
from app.services.notification_service import NotificationService
from app.ws.events import (
    AssignmentAcceptedPayload,
    AssignmentInvitedPayload,
    AssignmentRejectedPayload,
    IncidentStatusChangedPayload,
    build_message,
)
from app.ws.manager import ws_manager

logger = logging.getLogger(__name__)

# Average speed for ETA calculation (km/h)
_AVG_SPEED_KMH = 40
# Reputation penalty when a workshop ignores an invitation (points out of 100)
_IGNORE_PENALTY = 5.0


def _utc_now_naive() -> datetime:
    """Return UTC time compatible with PostgreSQL TIMESTAMP without time zone."""
    return datetime.now(UTC).replace(tzinfo=None)


def _to_utc_naive(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in km between two (lat, lon) points."""
    r = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    )
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class AssignmentService:
    """Intelligent workshop assignment engine.

    Considers: incident location, type, workshop availability,
    workshop specialties, distance, and case priority.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.incident_repo = IncidentRepository(session)
        self.workshop_repo = WorkshopRepository(session)
        self.ws_specialty_repo = WorkshopSpecialtyRepository(session)
        self.candidate_repo = WorkshopCandidateRepository(session)
        self.assignment_repo = AssignmentRepository(session)

    # ── public API ───────────────────────────────────────

    async def find_candidates(
        self,
        incident_id: int,
        *,
        max_distance_km: float = 50.0,
        max_candidates: int = 5,
        ttl_minutes: int = 15,
    ) -> Sequence[WorkshopCandidate]:
        """Score and persist the top-N candidate workshops for an incident.

        Args:
            incident_id: Incident to find candidates for.
            max_distance_km: Maximum radius to consider workshops (km).
            max_candidates: Maximum number of top-scored candidates to persist
                and notify. Use 0 for unlimited.
            ttl_minutes: Minutes each workshop has to respond before deadline expires.
        """
        incident = await self._get_incident(incident_id)
        workshops = await self.workshop_repo.get_all(skip=0, limit=500)
        now = _utc_now_naive()
        deadline = now + timedelta(minutes=ttl_minutes)

        candidates: list[WorkshopCandidate] = []
        ws_map: dict[int, Workshop] = {w.id: w for w in workshops}
        for ws in workshops:
            if ws.status != "ACTIVO":
                continue

            # Distance filter
            distance = self._calc_distance(incident, ws)
            if distance is not None and distance > max_distance_km:
                continue

            # Score
            score = await self._score_workshop(incident, ws, distance)

            candidate = WorkshopCandidate(
                incident_id=incident.id,
                workshop_id=ws.id,
                score=round(score, 2),
                distance_km=round(distance, 2) if distance is not None else None,
                estimated_arrival_minutes=(
                    round((distance / _AVG_SPEED_KMH) * 60) if distance else None
                ),
                notified=True,
                notified_at=now,
                invitation_deadline=deadline,
                response_status="PENDIENTE",
            )
            candidates.append(candidate)

        # Sort by score descending and keep top-N
        candidates.sort(key=lambda c: c.score or 0, reverse=True)
        if max_candidates > 0:
            candidates = candidates[:max_candidates]

        # Persist and update workshop invitation counters
        for c in candidates:
            self.session.add(c)
            ws_obj = ws_map.get(c.workshop_id)
            if ws_obj:
                ws_obj.invitations_received = (ws_obj.invitations_received or 0) + 1

        # Set incident tenant_id from first candidate workshop's tenant
        if candidates and incident.tenant_id is None:
            first_ws = ws_map.get(candidates[0].workshop_id)
            if first_ws and first_ws.tenant_id:
                incident.tenant_id = first_ws.tenant_id

        await self.session.flush()

        # Emit WS notification to each workshop's tenant channel
        for c in candidates:
            ws_obj = ws_map.get(c.workshop_id)
            if ws_obj and ws_obj.tenant_id:
                payload = AssignmentInvitedPayload(
                    incident_id=incident_id,
                    workshop_id=c.workshop_id,
                    candidate_id=c.id,
                    deadline=deadline,
                )
                await ws_manager.send_to_tenant(
                    ws_obj.tenant_id,
                    build_message("assignment.invited", payload),
                )

        logger.info(
            "Found %d candidates (max=%d, ttl=%dmin) for incident %d",
            len(candidates),
            max_candidates,
            ttl_minutes,
            incident_id,
        )
        return candidates

    async def generate_candidates_if_missing(
        self,
        incident_id: int,
        *,
        max_distance_km: float = 50.0,
        max_candidates: int = 5,
        ttl_minutes: int = 15,
    ) -> Sequence[WorkshopCandidate]:
        """Generate workshop invitations once for an incident.

        This is used after AI analysis. It is intentionally idempotent so a
        retried analysis request does not duplicate invitations.
        """
        existing_assignment = await self.assignment_repo.get_by_incident(incident_id)
        if existing_assignment:
            logger.info(
                "Auto candidate generation skipped for incident %d: assignment already exists",
                incident_id,
            )
            return []

        existing_candidates = await self.candidate_repo.get_by_incident(incident_id)
        if existing_candidates:
            logger.info(
                "Auto candidate generation skipped for incident %d: %d candidates already exist",
                incident_id,
                len(existing_candidates),
            )
            return existing_candidates

        candidates = await self.find_candidates(
            incident_id,
            max_distance_km=max_distance_km,
            max_candidates=max_candidates,
            ttl_minutes=ttl_minutes,
        )
        if not candidates:
            logger.warning("Auto candidate generation found no workshops for incident %d", incident_id)
            return []

        incident = await self._get_incident(incident_id)
        await self._mark_incident_notified(incident)
        logger.info(
            "Auto candidate generation created %d candidates for incident %d",
            len(candidates),
            incident_id,
        )
        return candidates

    async def assign_best(
        self,
        incident_id: int,
        user_id: int | None = None,
        actor_tenant_id: int | None = None,
    ) -> ServiceAssignment:
        """Pick the best accepted candidate (or top-scored) and create a ServiceAssignment."""
        incident = await self._get_incident(incident_id)

        # Check no existing assignment
        existing = await self.assignment_repo.get_by_incident(incident_id)
        if existing:
            raise BadRequestError("Incident already has an assignment")

        # Prefer ACEPTADO candidates, fallback to best scored PENDIENTE
        candidates = await self.candidate_repo.get_by_incident(incident_id)
        if not candidates:
            raise BadRequestError("No candidates found. Run find_candidates first.")

        accepted = [c for c in candidates if c.response_status == "ACEPTADO"]
        chosen = accepted[0] if accepted else candidates[0]

        workshop = await self.workshop_repo.get_by_id(chosen.workshop_id)
        if not workshop:
            raise NotFoundError("Workshop not found")
        if workshop.tenant_id is None:
            raise BadRequestError("Workshop does not have a tenant")
        if actor_tenant_id is not None and workshop.tenant_id != actor_tenant_id:
            raise ForbiddenError("Cannot assign a workshop outside the current tenant")

        assignment = ServiceAssignment(
            incident_id=incident.id,
            workshop_id=chosen.workshop_id,
            tenant_id=workshop.tenant_id,
            assigned_by_user_id=user_id,
            distance_km=chosen.distance_km,
            estimated_arrival_minutes=chosen.estimated_arrival_minutes,
            assignment_status="ASIGNADO",
        )
        assignment = await self.assignment_repo.create(assignment)
        await self._mark_incident_accepted(incident, user_id=user_id)
        await self._expire_other_pending_candidates(incident_id, chosen.id)

        # Emit WS to incident channel and client's personal channel
        payload = AssignmentAcceptedPayload(
            incident_id=incident_id,
            workshop_id=chosen.workshop_id,
            assignment_id=assignment.id,
        )
        msg = build_message("assignment.accepted", payload)
        await ws_manager.send_to_incident(incident_id, msg)
        await ws_manager.send_to_user(incident.client_user_id, msg)

        logger.info(
            "Assigned workshop %d to incident %d (score=%.2f)",
            chosen.workshop_id,
            incident_id,
            chosen.score or 0,
        )
        return assignment

    async def respond_candidate(
        self,
        incident_id: int,
        workshop_id: int,
        response_status: str,
        response_note: str | None = None,
        quotation_cost: float | None = None,
        quotation_minutes: int | None = None,
        quotation_description: str | None = None,
        actor_tenant_id: int | None = None,
        actor_user_id: int | None = None,
    ) -> WorkshopCandidate:
        """Workshop accepts or rejects a candidate invitation.

        If the response arrives after invitation_deadline, a reputation penalty
        is applied to the workshop.
        """
        if not response_status:
            raise BadRequestError("Response status is required")

        incident = await self._get_incident(incident_id)
        candidate = await self.candidate_repo.get_by_workshop_and_incident(workshop_id, incident_id)
        if not candidate:
            raise NotFoundError("Candidate not found")

        workshop = await self.workshop_repo.get_by_id(workshop_id)
        if not workshop:
            raise NotFoundError("Workshop not found")
        if workshop.tenant_id is None:
            raise BadRequestError("Workshop does not have a tenant")
        if actor_tenant_id is not None and workshop.tenant_id != actor_tenant_id:
            raise ForbiddenError("Cannot respond to an invitation outside the current tenant")

        now = _utc_now_naive()
        status_upper = response_status.upper()
        if status_upper not in {"ACEPTADO", "RECHAZADO", "EXPIRADO"}:
            raise BadRequestError("Invalid response status")

        previous_status = (candidate.response_status or "").upper()
        if previous_status != "PENDIENTE" and previous_status != status_upper:
            raise BadRequestError("Invitation already has a final response")

        existing_assignment = await self.assignment_repo.get_by_incident(incident_id)
        if status_upper == "ACEPTADO" and existing_assignment and existing_assignment.workshop_id != workshop_id:
            raise BadRequestError("Incident already has an assignment")

        # Determine if response is late
        invitation_deadline = _to_utc_naive(candidate.invitation_deadline)
        ttl_expired = invitation_deadline is not None and now > invitation_deadline
        is_first_response = previous_status == "PENDIENTE" and candidate.responded_at is None

        candidate.response_status = status_upper
        candidate.responded_at = now
        candidate.response_note = response_note
        if status_upper == "ACEPTADO":
            candidate.quotation_estimated_cost = quotation_cost
            candidate.quotation_completion_minutes = quotation_minutes
            candidate.quotation_description = quotation_description

        # Calculate response time
        notified_at = _to_utc_naive(candidate.notified_at)
        if notified_at is not None:
            candidate.response_time_seconds = int((now - notified_at).total_seconds())

        # Update workshop reputation counters
        if is_first_response:
            workshop.invitations_responded = (workshop.invitations_responded or 0) + 1
        if is_first_response and ttl_expired:
            workshop.invitations_ignored = (workshop.invitations_ignored or 0) + 1
            new_score = max(0.0, float(workshop.reputation_score or 100) - _IGNORE_PENALTY)
            workshop.reputation_score = new_score
            logger.info(
                "Reputation penalty applied to workshop %d (late response): %.1f",
                workshop_id,
                new_score,
            )

        await self.session.flush()
        await self.session.refresh(candidate)

        # Emit WS to incident channel — ACEPTADO now waits for client selection
        if status_upper == "ACEPTADO":
            if existing_assignment:
                # If already assigned (e.g. from client selection), reject duplicate
                raise BadRequestError("Incident already has an assignment")

            # Notify client that this workshop accepted, pending their selection
            payload = AssignmentAcceptedPayload(
                incident_id=incident_id,
                workshop_id=workshop_id,
                assignment_id=0,  # no assignment yet
            )
            msg = build_message("assignment.accepted", payload)
            await ws_manager.send_to_incident(incident_id, msg)
            await ws_manager.send_to_user(incident.client_user_id, msg)
            logger.info(
                "Workshop %d accepted incident %d; waiting for client selection",
                workshop_id,
                incident_id,
            )
        else:
            payload = AssignmentRejectedPayload(
                incident_id=incident_id,
                workshop_id=workshop_id,
                candidate_id=candidate.id,
            )
            await ws_manager.send_to_incident(
                incident_id, build_message("assignment.rejected", payload)
            )

        return candidate

    async def select_workshop(
        self, incident_id: int, workshop_id: int, client_user_id: int
    ) -> ServiceAssignment:
        """Client selects a workshop that accepted their incident. Creates the assignment."""
        incident = await self._get_incident(incident_id)
        if incident.client_user_id != client_user_id:
            raise ForbiddenError("You can only select a workshop for your own incident")

        existing = await self.assignment_repo.get_by_incident(incident_id)
        if existing:
            raise BadRequestError("Incident already has an assignment")

        # Find the accepted candidate
        candidate = await self.candidate_repo.get_by_workshop_and_incident(workshop_id, incident_id)
        if not candidate:
            raise NotFoundError("Candidate not found")
        if candidate.response_status != "ACEPTADO":
            raise BadRequestError("Workshop has not accepted this incident")

        workshop = await self.workshop_repo.get_by_id(workshop_id)
        if not workshop:
            raise NotFoundError("Workshop not found")

        # Auto-asignar el primer técnico disponible del taller
        from app.models.technician import Technician
        from sqlalchemy import select

        tech_result = await self.session.execute(
            select(Technician).where(
                Technician.workshop_id == workshop_id,
                Technician.availability_status == "DISPONIBLE",
            ).limit(1)
        )
        first_tech = tech_result.scalar_one_or_none()

        assignment = ServiceAssignment(
            incident_id=incident.id,
            workshop_id=workshop_id,
            tenant_id=workshop.tenant_id,
            technician_id=first_tech.id if first_tech else None,
            distance_km=candidate.distance_km,
            estimated_arrival_minutes=candidate.estimated_arrival_minutes,
            assignment_status="ASIGNADO",
        )
        assignment = await self.assignment_repo.create(assignment)
        await self._mark_incident_accepted(incident, user_id=client_user_id)
        await self._expire_other_pending_candidates(incident_id, candidate.id)

        payload = AssignmentAcceptedPayload(
            incident_id=incident_id,
            workshop_id=workshop_id,
            assignment_id=assignment.id,
        )
        msg = build_message("assignment.accepted", payload)
        await ws_manager.send_to_incident(incident_id, msg)
        await ws_manager.send_to_user(incident.client_user_id, msg)

        logger.info(
            "Client %d selected workshop %d for incident %d; assignment %d created",
            client_user_id, workshop_id, incident_id, assignment.id,
        )
        return assignment

    # ── helpers ──────────────────────────────────────────

    async def _push_to_client(
        self, user_id: int, incident_id: int, title: str, message: str
    ) -> None:
        """Send a push notification to the client via FCM + WS."""
        from app.models.user import User
        from sqlalchemy import select

        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return
        notif_data = NotificationCreate(
            user_id=user_id,
            incident_id=incident_id,
            notification_type="assignment_status",
            channel="PUSH",
            title=title,
            message=message,
        )
        notif_svc = NotificationService(self.session)
        await notif_svc.create_and_push(notif_data, device_token=user.fcm_token)

    async def _expire_other_pending_candidates(self, incident_id: int, accepted_candidate_id: int) -> None:
        candidates = await self.candidate_repo.get_by_incident(incident_id)
        for other in candidates:
            if other.id == accepted_candidate_id:
                continue
            if other.response_status == "PENDIENTE":
                other.response_status = "EXPIRADO"
                other.response_note = "Asignación tomada por otro taller"
        await self.session.flush()

    async def _mark_incident_accepted(
        self, incident: Incident, user_id: int | None = None
    ) -> None:
        accepted_status = await self._get_incident_status_by_name("ACEPTADO")
        if not accepted_status:
            raise BadRequestError("Incident status ACEPTADO not found")

        now = _utc_now_naive()
        old_status_id = incident.incident_status_id
        old_status_name = await self._get_incident_status_name(old_status_id)

        if incident.accepted_at is None:
            incident.accepted_at = now

        if incident.incident_status_id == accepted_status.id:
            incident.updated_at = now
            await self.session.flush()
            return

        incident.incident_status_id = accepted_status.id
        incident.updated_at = now
        self.session.add(
            IncidentStatusHistory(
                incident_id=incident.id,
                incident_status_id=accepted_status.id,
                user_id=user_id,
                observation="Taller aceptó invitación y se creó asignación",
            )
        )
        await self.session.flush()

        payload = IncidentStatusChangedPayload(
            incident_id=incident.id,
            old_status=old_status_name or str(old_status_id),
            new_status=accepted_status.name,
        )
        msg = build_message("incident.status_changed", payload)
        await ws_manager.send_to_incident(incident.id, msg)
        await ws_manager.send_to_user(incident.client_user_id, msg)
        await self._push_to_client(
            incident.client_user_id,
            incident.id,
            "Taller asignado",
            "Un taller ha aceptado tu solicitud. Revisa los detalles.",
        )

    async def _mark_incident_notified(self, incident: Incident) -> None:
        notified_status = await self._get_incident_status_by_name("NOTIFICADO")
        if not notified_status:
            raise BadRequestError("Incident status NOTIFICADO not found")

        now = _utc_now_naive()
        old_status_id = incident.incident_status_id
        old_status_name = await self._get_incident_status_name(old_status_id)

        if incident.incident_status_id == notified_status.id:
            incident.updated_at = now
            await self.session.flush()
            return

        incident.incident_status_id = notified_status.id
        incident.updated_at = now
        self.session.add(
            IncidentStatusHistory(
                incident_id=incident.id,
                incident_status_id=notified_status.id,
                user_id=None,
                observation="Candidatos generados automaticamente despues del analisis IA",
            )
        )
        await self.session.flush()

        payload = IncidentStatusChangedPayload(
            incident_id=incident.id,
            old_status=old_status_name or str(old_status_id),
            new_status=notified_status.name,
        )
        msg = build_message("incident.status_changed", payload)
        await ws_manager.send_to_incident(incident.id, msg)
        await ws_manager.send_to_user(incident.client_user_id, msg)
        await self._push_to_client(
            incident.client_user_id,
            incident.id,
            "Buscando taller",
            "Estamos notificando talleres cercanos para tu emergencia.",
        )

    async def _get_incident_status_by_name(self, name: str) -> IncidentStatus | None:
        result = await self.session.execute(
            select(IncidentStatus).where(IncidentStatus.name == name)
        )
        return result.scalar_one_or_none()

    async def _get_incident_status_name(self, status_id: int | None) -> str | None:
        if status_id is None:
            return None
        status = await self.session.get(IncidentStatus, status_id)
        return status.name if status else None

    async def _get_incident(self, incident_id: int) -> Incident:
        incident = await self.incident_repo.get_by_id(incident_id)
        if not incident:
            raise NotFoundError("Incident not found")
        return incident

    @staticmethod
    def _calc_distance(incident: Incident, workshop: Workshop) -> float | None:
        if (
            incident.latitude is None
            or incident.longitude is None
            or workshop.latitude is None
            or workshop.longitude is None
        ):
            return None
        return _haversine(
            float(incident.latitude),
            float(incident.longitude),
            float(workshop.latitude),
            float(workshop.longitude),
        )

    async def _score_workshop(
        self, incident: Incident, workshop: Workshop, distance: float | None
    ) -> float:
        """Calculate a 0-100 score for a workshop given an incident.

        Weights:
          - distance:       30 %  (closer is better)
          - specialty match: 20 %  (has matching specialty)
          - reputation:      15 %  (puntaje_reputacion / 100)
          - capacity:        15 %  (active technicians + availability)
          - tow capability:  10 %  (has tow if required)
          - 24h service:     10 %  (bonus)
        """
        score = 0.0

        # Distance score (max 30)
        if distance is not None:
            dist_score = max(0.0, 1 - distance / 50.0) * 30
            score += dist_score
        else:
            score += 15  # neutral when no coords

        # Specialty match (max 20)
        if incident.incident_type_id:
            ws_specs = await self.ws_specialty_repo.get_by_workshop(workshop.id)
            spec_ids = {s.specialty_id for s in ws_specs}
            if spec_ids:
                score += 20

        # Reputation score (max 15) — normalized from 0-100
        reputation = float(workshop.reputation_score or 100)
        score += (reputation / 100.0) * 15

        # Capacity score (max 15): more active technicians = higher capacity
        from app.models.technician import Technician
        from sqlalchemy import select, func
        tech_count = await self.session.scalar(
            select(func.count(Technician.id)).where(
                Technician.workshop_id == workshop.id,
                Technician.availability_status == "AVAILABLE",
            )
        ) or 0
        # 0 techs = 0, 1 tech = 7, 2+ techs = 15
        if tech_count >= 2:
            score += 15
        elif tech_count == 1:
            score += 7
        # else 0

        # Tow capability (max 10)
        if (incident.requires_tow and workshop.has_tow) or not incident.requires_tow:
            score += 10

        # 24h bonus (max 10)
        if workshop.is_24_hours:
            score += 10

        return score
