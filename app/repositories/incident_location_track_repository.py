from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident_location_track import IncidentLocationTrack
from app.repositories.base import BaseRepository


class IncidentLocationTrackRepository(BaseRepository[IncidentLocationTrack]):
    def __init__(self, session: AsyncSession):
        super().__init__(IncidentLocationTrack, session)

    async def add_point(
        self, incident_id: int, latitude: float, longitude: float
    ) -> IncidentLocationTrack:
        track = IncidentLocationTrack(
            incident_id=incident_id,
            latitude=latitude,
            longitude=longitude,
        )
        return await self.create(track)

    async def get_recent(
        self, incident_id: int, limit: int = 50
    ) -> list[IncidentLocationTrack]:
        stmt = (
            select(IncidentLocationTrack)
            .where(IncidentLocationTrack.incident_id == incident_id)
            .order_by(IncidentLocationTrack.recorded_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_since(
        self, incident_id: int, since: datetime
    ) -> list[IncidentLocationTrack]:
        stmt = (
            select(IncidentLocationTrack)
            .where(
                IncidentLocationTrack.incident_id == incident_id,
                IncidentLocationTrack.recorded_at >= since,
            )
            .order_by(IncidentLocationTrack.recorded_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
