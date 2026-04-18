import logging
import math
from collections.abc import Sequence
from datetime import UTC, datetime

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

logger = logging.getLogger(__name__)

# Average speed for ETA calculation (km/h)
_AVG_SPEED_KMH = 40


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
        self, incident_id: int, *, max_distance_km: float = 50.0
    ) -> Sequence[WorkshopCandidate]:
        """Score and persist candidate workshops for an incident."""
        incident = await self._get_incident(incident_id)
        workshops = await self.workshop_repo.get_all(skip=0, limit=500)

        candidates: list[WorkshopCandidate] = []
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
                notified=False,
                response_status="PENDIENTE",
            )
            candidates.append(candidate)

        # Sort by score descending
        candidates.sort(key=lambda c: c.score or 0, reverse=True)

        # Persist
        for c in candidates:
            self.session.add(c)
        await self.session.flush()

        logger.info("Found %d candidates for incident %d", len(candidates), incident_id)
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
        """Workshop accepts or rejects a candidate invitation."""
        candidate = await self.candidate_repo.get_by_workshop_and_incident(workshop_id, incident_id)
        if not candidate:
            raise NotFoundError("Candidate not found")

        candidate.response_status = response_status.upper()
        candidate.responded_at = datetime.now(UTC)
        candidate.response_note = response_note
        await self.session.flush()
        await self.session.refresh(candidate)
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
          - distance:       40 %  (closer is better)
          - specialty match: 30 %  (has matching specialty)
          - tow capability:  15 %  (has tow if required)
          - 24h service:     15 %  (bonus)
        """
        score = 0.0

        # Distance score (max 40)
        if distance is not None:
            dist_score = max(0.0, 1 - distance / 50.0) * 40
            score += dist_score
        else:
            score += 20  # neutral when no coords

        # Specialty match (max 30)
        if incident.incident_type_id:
            ws_specs = await self.ws_specialty_repo.get_by_workshop(workshop.id)
            spec_ids = {s.specialty_id for s in ws_specs}
            # Simple heuristic: if type matches any specialty, full score
            if spec_ids:
                score += 30

        # Tow capability (max 15)
        if (incident.requires_tow and workshop.has_tow) or not incident.requires_tow:
            score += 15

        # 24h bonus (max 15)
        if workshop.is_24_hours:
            score += 15

        return score
