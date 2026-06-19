import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.incident_location_track import IncidentLocationTrack
from app.models.service_assignment import ServiceAssignment
from app.repositories.incident_location_track_repository import IncidentLocationTrackRepository
from app.repositories.incident_repository import IncidentRepository
from app.ws.events import LocationUpdatedPayload, build_message
from app.ws.manager import ws_manager

logger = logging.getLogger(__name__)


class LocationTrackService:
    def __init__(self, session: AsyncSession):
        self.repo = IncidentLocationTrackRepository(session)
        self.incident_repo = IncidentRepository(session)
        self._session = session

    async def add_point(
        self, incident_id: int, latitude: float, longitude: float,
        user=None,
    ) -> IncidentLocationTrack:
        incident = await self.incident_repo.get_by_id(incident_id)
        if not incident:
            raise NotFoundError("Incident not found")

        # If user is a TECNICO, validate they are assigned to this incident
        if user and user.role.lower() == "tecnico":
            from app.repositories.technician_repository import TechnicianRepository
            tech_repo = TechnicianRepository(self._session)
            tech = await tech_repo.get_by_user_id(user.id)
            if not tech:
                raise ForbiddenError("Technician profile not found")
            stmt = select(ServiceAssignment.id).where(
                ServiceAssignment.incident_id == incident_id,
                ServiceAssignment.technician_id == tech.id,
            )
            result = await self._session.execute(stmt)
            if not result.scalar_one_or_none():
                raise ForbiddenError("You are not assigned to this incident")

        track = await self.repo.add_point(incident_id, latitude, longitude)

        # Emit WS event to all parties subscribed to this incident
        payload = LocationUpdatedPayload(
            incident_id=incident_id,
            latitude=latitude,
            longitude=longitude,
            recorded_at=datetime.now(UTC),
        )
        await ws_manager.send_to_incident(
            incident_id,
            build_message("incident.location_updated", payload),
        )
        logger.debug("Location point added for incident %d: (%.6f, %.6f)", incident_id, latitude, longitude)
        return track

    async def get_points(
        self, incident_id: int, since: datetime | None = None
    ) -> list[IncidentLocationTrack]:
        incident = await self.incident_repo.get_by_id(incident_id)
        if not incident:
            raise NotFoundError("Incident not found")
        if since:
            return await self.repo.get_since(incident_id, since)
        return await self.repo.get_recent(incident_id)
