from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident
from app.models.incident_status import IncidentStatus
from app.models.payment import Payment
from app.models.rating import Rating
from app.models.service_assignment import ServiceAssignment
from app.models.technician import Technician
from app.models.workshop import Workshop
from app.schemas.metrics import MetricsDashboard


class MetricsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_dashboard(self) -> MetricsDashboard:
        # Total incidents
        total_incidents = await self._scalar(select(func.count(Incident.id)))

        # Incidents by status (join to get status name)
        stmt = (
            select(IncidentStatus.name, func.count(Incident.id))
            .join(IncidentStatus, Incident.incident_status_id == IncidentStatus.id)
            .group_by(IncidentStatus.name)
        )
        result = await self.session.execute(stmt)
        incidents_by_status = dict(result.all())

        # Incidents by priority
        stmt = (
            select(Incident.priority_level, func.count(Incident.id))
            .where(Incident.priority_level.isnot(None))
            .group_by(Incident.priority_level)
        )
        result = await self.session.execute(stmt)
        incidents_by_priority = dict(result.all())

        # Assignments
        total_assignments = await self._scalar(select(func.count(ServiceAssignment.id)))

        stmt = select(
            ServiceAssignment.assignment_status, func.count(ServiceAssignment.id)
        ).group_by(ServiceAssignment.assignment_status)
        result = await self.session.execute(stmt)
        assignments_by_status = dict(result.all())

        # Payments
        total_payments = await self._scalar(select(func.count(Payment.id)))

        total_revenue_val = await self._scalar(select(func.coalesce(func.sum(Payment.amount), 0)))

        # Ratings
        total_ratings = await self._scalar(select(func.count(Rating.id)))

        avg_rating_val = await self._scalar(select(func.avg(Rating.score)))

        # Workshops & technicians
        total_workshops = await self._scalar(select(func.count(Workshop.id)))
        total_technicians = await self._scalar(select(func.count(Technician.id)))

        return MetricsDashboard(
            total_incidents=total_incidents or 0,
            incidents_by_status=incidents_by_status,
            incidents_by_priority=incidents_by_priority,
            total_assignments=total_assignments or 0,
            assignments_by_status=assignments_by_status,
            total_payments=total_payments or 0,
            total_revenue=float(total_revenue_val or 0),
            average_rating=round(float(avg_rating_val), 2) if avg_rating_val else None,
            total_ratings=total_ratings or 0,
            total_workshops=total_workshops or 0,
            total_technicians=total_technicians or 0,
        )

    async def _scalar(self, stmt):
        result = await self.session.execute(stmt)
        return result.scalar()
