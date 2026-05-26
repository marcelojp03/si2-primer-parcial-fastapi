import logging
import math
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.incident import Incident
from app.models.service_assignment import ServiceAssignment
from app.models.workshop import Workshop
from app.models.workshop_candidate import WorkshopCandidate
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.workshop_candidate_repository import WorkshopCandidateRepository
from app.repositories.workshop_repository import WorkshopRepository
from app.repositories.workshop_specialty_repository import WorkshopSpecialtyRepository
from app.ws.events import (
    AssignmentAcceptedPayload,
    AssignmentInvitedPayload,
    AssignmentRejectedPayload,
    build_message,
)
from app.ws.manager import ws_manager

logger = logging.getLogger(__name__)

# Average speed for ETA calculation (km/h)
_AVG_SPEED_KMH = 40
# Reputation penalty when a workshop ignores an invitation (points out of 100)
_IGNORE_PENALTY = 5.0


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
        now = datetime.now(UTC)
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

    async def assign_best(self, incident_id: int, user_id: int | None = None) -> ServiceAssignment:
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

        assignment = ServiceAssignment(
            incident_id=incident.id,
            workshop_id=chosen.workshop_id,
            assigned_by_user_id=user_id,
            distance_km=chosen.distance_km,
            estimated_arrival_minutes=chosen.estimated_arrival_minutes,
            assignment_status="ASIGNADO",
        )
        assignment = await self.assignment_repo.create(assignment)

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
    ) -> WorkshopCandidate:
        """Workshop accepts or rejects a candidate invitation.

        If the response arrives after invitation_deadline, a reputation penalty
        is applied to the workshop.
        """
        candidate = await self.candidate_repo.get_by_workshop_and_incident(workshop_id, incident_id)
        if not candidate:
            raise NotFoundError("Candidate not found")

        now = datetime.now(UTC)
        status_upper = response_status.upper()

        # Determine if response is late
        invitation_deadline = candidate.invitation_deadline
        if invitation_deadline is not None and invitation_deadline.tzinfo is None:
            invitation_deadline = invitation_deadline.replace(tzinfo=UTC)
        ttl_expired = invitation_deadline is not None and now > invitation_deadline

        candidate.response_status = status_upper
        candidate.responded_at = now
        candidate.response_note = response_note

        # Calculate response time
        notified_at = candidate.notified_at
        if notified_at is not None:
            if notified_at.tzinfo is None:
                notified_at = notified_at.replace(tzinfo=UTC)
            candidate.response_time_seconds = int((now - notified_at).total_seconds())

        # Update workshop reputation counters
        workshop = await self.workshop_repo.get_by_id(workshop_id)
        if workshop:
            workshop.invitations_responded = (workshop.invitations_responded or 0) + 1
            if ttl_expired:
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

        # Emit WS to incident channel
        if status_upper == "ACEPTADO":
            payload: AssignmentAcceptedPayload | AssignmentRejectedPayload = AssignmentAcceptedPayload(
                incident_id=incident_id,
                workshop_id=workshop_id,
                assignment_id=candidate.id,
            )
            await ws_manager.send_to_incident(
                incident_id, build_message("assignment.accepted", payload)
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

    # ── helpers ──────────────────────────────────────────

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
          - distance:       35 %  (closer is better)
          - specialty match: 25 %  (has matching specialty)
          - reputation:      20 %  (puntaje_reputacion / 100)
          - tow capability:  10 %  (has tow if required)
          - 24h service:     10 %  (bonus)
        """
        score = 0.0

        # Distance score (max 35)
        if distance is not None:
            dist_score = max(0.0, 1 - distance / 50.0) * 35
            score += dist_score
        else:
            score += 17  # neutral when no coords

        # Specialty match (max 25)
        if incident.incident_type_id:
            ws_specs = await self.ws_specialty_repo.get_by_workshop(workshop.id)
            spec_ids = {s.specialty_id for s in ws_specs}
            if spec_ids:
                score += 25

        # Reputation score (max 20) — normalized from 0-100
        reputation = float(workshop.reputation_score or 100)
        score += (reputation / 100.0) * 20

        # Tow capability (max 10)
        if (incident.requires_tow and workshop.has_tow) or not incident.requires_tow:
            score += 10

        # 24h bonus (max 10)
        if workshop.is_24_hours:
            score += 10

        return score
