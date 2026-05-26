from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident
from app.models.incident_status import IncidentStatus
from app.models.incident_type import IncidentType
from app.models.payment import Payment
from app.models.rating import Rating
from app.models.service_assignment import ServiceAssignment
from app.models.technician import Technician
from app.models.workshop import Workshop
from app.schemas.metrics import KPIDashboard, MetricsDashboard


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

    # ── KPI Dashboard (CU33) ──────────────────────────────────

    async def get_kpis(self, tenant_id: int | None = None) -> KPIDashboard:
        """KPIs operacionales, opcionalmente filtrados por tenant."""
        cutoff_30d = datetime.now(UTC) - timedelta(days=30)

        # Base workshop filter
        ws_stmt = select(Workshop.id)
        if tenant_id is not None:
            ws_stmt = ws_stmt.where(Workshop.tenant_id == tenant_id)
        ws_ids_result = await self.session.execute(ws_stmt)
        ws_ids = [r[0] for r in ws_ids_result.all()]

        # Incidents scoped to this tenant via assignments
        inc_filter = (
            ServiceAssignment.tenant_id == tenant_id if tenant_id is not None else True
        )
        scoped_incident_ids_stmt = select(ServiceAssignment.incident_id).where(inc_filter)
        result = await self.session.execute(scoped_incident_ids_stmt)
        scoped_incident_ids = [r[0] for r in result.all()]

        # Total incidents (use scoped if tenant provided, otherwise global)
        if tenant_id is not None and scoped_incident_ids:
            total_inc = await self._scalar(
                select(func.count(Incident.id)).where(Incident.id.in_(scoped_incident_ids))
            )
            inc_30d = await self._scalar(
                select(func.count(Incident.id)).where(
                    Incident.id.in_(scoped_incident_ids),
                    Incident.requested_at >= cutoff_30d,
                )
            )
        else:
            total_inc = await self._scalar(select(func.count(Incident.id)))
            inc_30d = await self._scalar(
                select(func.count(Incident.id)).where(Incident.requested_at >= cutoff_30d)
            )

        # Active workshops in tenant
        active_ws = await self._scalar(
            select(func.count(Workshop.id)).where(
                Workshop.id.in_(ws_ids) if ws_ids else True,
                Workshop.status == "ACTIVO",
            )
        )

        # Avg reputation
        avg_rep = await self._scalar(
            select(func.avg(Workshop.reputation_score)).where(
                Workshop.id.in_(ws_ids) if ws_ids else True
            )
        )

        # Assignments
        assignment_filter = (
            ServiceAssignment.tenant_id == tenant_id if tenant_id is not None else True
        )
        total_assign = await self._scalar(
            select(func.count(ServiceAssignment.id)).where(assignment_filter)
        )
        active_assign = await self._scalar(
            select(func.count(ServiceAssignment.id)).where(
                assignment_filter,
                ServiceAssignment.assignment_status.in_(["ASIGNADO", "EN_CAMINO", "EN_SERVICIO"]),
            )
        )

        # Revenue (scoped)
        rev_stmt = select(func.coalesce(func.sum(Payment.amount), 0))
        if tenant_id is not None and scoped_incident_ids:
            rev_stmt = rev_stmt.where(
                Payment.assignment_id.in_(
                    select(ServiceAssignment.id).where(ServiceAssignment.tenant_id == tenant_id)
                )
            )
        total_rev = await self._scalar(rev_stmt)

        # Avg rating
        rating_stmt = select(func.avg(Rating.score))
        if tenant_id is not None and scoped_incident_ids:
            rating_stmt = rating_stmt.where(
                Rating.assignment_id.in_(
                    select(ServiceAssignment.id).where(ServiceAssignment.tenant_id == tenant_id)
                )
            )
        avg_rating = await self._scalar(rating_stmt)

        # SLA compliance: % of finished incidents resolved within sla_minutes
        # Only calculable if incident_type has sla_minutes
        sla_pct = await self._calc_sla_compliance(tenant_id, scoped_incident_ids)

        # Avg response time (minutes from requested_at to accepted_at)
        avg_resp = await self._calc_avg_response_minutes(tenant_id, scoped_incident_ids)

        return KPIDashboard(
            tenant_id=tenant_id,
            total_incidents=total_inc or 0,
            incidents_last_30_days=inc_30d or 0,
            avg_response_minutes=avg_resp,
            sla_compliance_pct=sla_pct,
            total_assignments=total_assign or 0,
            active_assignments=active_assign or 0,
            active_workshops=active_ws or 0,
            avg_reputation_score=round(float(avg_rep), 2) if avg_rep else None,
            total_revenue=float(total_rev or 0),
            average_rating=round(float(avg_rating), 2) if avg_rating else None,
        )

    async def _calc_avg_response_minutes(
        self, tenant_id: int | None, scoped_ids: list[int]
    ) -> float | None:
        """Average minutes from incident creation to acceptance."""
        stmt = select(
            func.avg(
                func.extract("epoch", Incident.accepted_at) - func.extract("epoch", Incident.requested_at)
            )
            / 60
        ).where(Incident.accepted_at.isnot(None))
        if tenant_id is not None and scoped_ids:
            stmt = stmt.where(Incident.id.in_(scoped_ids))
        val = await self._scalar(stmt)
        return round(float(val), 2) if val else None

    async def _calc_sla_compliance(
        self, tenant_id: int | None, scoped_ids: list[int]
    ) -> float | None:
        """% of finished incidents resolved within their type's sla_minutes."""
        base = (
            select(Incident.id, Incident.requested_at, Incident.finished_at, IncidentType.sla_minutes)
            .join(IncidentType, Incident.incident_type_id == IncidentType.id)
            .where(
                Incident.finished_at.isnot(None),
                IncidentType.sla_minutes.isnot(None),
            )
        )
        if tenant_id is not None and scoped_ids:
            base = base.where(Incident.id.in_(scoped_ids))
        rows_result = await self.session.execute(base)
        rows = rows_result.all()
        if not rows:
            return None
        compliant = sum(
            1
            for _, requested_at, finished_at, sla_minutes in rows
            if (finished_at - requested_at).total_seconds() / 60 <= sla_minutes
        )
        return round(compliant / len(rows) * 100, 2)
