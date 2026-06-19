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

    async def get_dashboard(self, tenant_id: int | None = None) -> MetricsDashboard:
        # Base scope: assignments filtered by tenant
        assign_filter = (
            ServiceAssignment.tenant_id == tenant_id if tenant_id is not None else True
        )
        scoped_inc_ids = None
        if tenant_id is not None:
            result = await self.session.execute(
                select(ServiceAssignment.incident_id).where(assign_filter)
            )
            scoped_inc_ids = [r[0] for r in result.all()]
        inc_filter = (
            Incident.id.in_(scoped_inc_ids)
            if tenant_id is not None and scoped_inc_ids
            else True
        )
        ws_filter = (
            Workshop.tenant_id == tenant_id if tenant_id is not None else True
        )

        # Total incidents
        inc_count_stmt = select(func.count(Incident.id))
        if inc_filter is not True:
            inc_count_stmt = inc_count_stmt.where(inc_filter)
        total_incidents = await self._scalar(inc_count_stmt)

        # Incidents by status
        stmt = (
            select(IncidentStatus.name, func.count(Incident.id))
            .join(IncidentStatus, Incident.incident_status_id == IncidentStatus.id)
        )
        if inc_filter is not True:
            stmt = stmt.where(inc_filter)
        stmt = stmt.group_by(IncidentStatus.name)
        result = await self.session.execute(stmt)
        incidents_by_status = dict(result.all())

        # Incidents by priority
        stmt = (
            select(Incident.priority_level, func.count(Incident.id))
            .where(Incident.priority_level.isnot(None))
        )
        if inc_filter is not True:
            stmt = stmt.where(inc_filter)
        stmt = stmt.group_by(Incident.priority_level)
        result = await self.session.execute(stmt)
        incidents_by_priority = dict(result.all())

        # Assignments
        total_assignments = await self._scalar(
            select(func.count(ServiceAssignment.id)).where(assign_filter)
        )
        stmt = select(
            ServiceAssignment.assignment_status, func.count(ServiceAssignment.id)
        ).where(assign_filter).group_by(ServiceAssignment.assignment_status)
        result = await self.session.execute(stmt)
        assignments_by_status = dict(result.all())

        # Payments (scoped via assignments)
        total_payments = await self._scalar(select(func.count(Payment.id)))
        total_revenue_val = await self._scalar(select(func.coalesce(func.sum(Payment.amount), 0)))
        if tenant_id is not None:
            rev_stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.service_assignment_id.in_(
                    select(ServiceAssignment.id).where(assign_filter)
                )
            )
            total_revenue_val = await self._scalar(rev_stmt)
            pay_count_stmt = select(func.count(Payment.id)).where(
                Payment.service_assignment_id.in_(
                    select(ServiceAssignment.id).where(assign_filter)
                )
            )
            total_payments = await self._scalar(pay_count_stmt)

        # Ratings
        total_ratings = await self._scalar(select(func.count(Rating.id)))
        avg_rating_val = await self._scalar(select(func.avg(Rating.score)))
        if tenant_id is not None:
            rating_stmt = select(func.avg(Rating.score)).where(
                Rating.service_assignment_id.in_(
                    select(ServiceAssignment.id).where(assign_filter)
                )
            )
            avg_rating_val = await self._scalar(rating_stmt)
            rating_count_stmt = select(func.count(Rating.id)).where(
                Rating.service_assignment_id.in_(
                    select(ServiceAssignment.id).where(assign_filter)
                )
            )
            total_ratings = await self._scalar(rating_count_stmt)

        # Workshops & technicians
        total_workshops = await self._scalar(
            select(func.count(Workshop.id)).where(ws_filter)
        )
        tech_stmt = select(func.count(Technician.id))
        if tenant_id is not None:
            tech_stmt = tech_stmt.where(
                Technician.workshop_id.in_(select(Workshop.id).where(ws_filter))
            )
        total_technicians = await self._scalar(tech_stmt)

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
        cutoff_30d = (datetime.now(UTC) - timedelta(days=30)).replace(tzinfo=None)

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
        elif tenant_id is not None:
            total_inc = 0
            inc_30d = 0
        else:
            total_inc = await self._scalar(select(func.count(Incident.id)))
            inc_30d = await self._scalar(
                select(func.count(Incident.id)).where(Incident.requested_at >= cutoff_30d)
            )

        # Active workshops in tenant
        if tenant_id is not None and not ws_ids:
            active_ws = 0
            avg_rep = None
        else:
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
        if tenant_id is not None and not scoped_incident_ids:
            total_rev = 0
        else:
            rev_stmt = select(func.coalesce(func.sum(Payment.amount), 0))
            if tenant_id is not None:
                rev_stmt = rev_stmt.where(
                    Payment.service_assignment_id.in_(
                        select(ServiceAssignment.id).where(ServiceAssignment.tenant_id == tenant_id)
                    )
                )
            total_rev = await self._scalar(rev_stmt)

        # Avg rating
        if tenant_id is not None and not scoped_incident_ids:
            avg_rating = None
        else:
            rating_stmt = select(func.avg(Rating.score))
            if tenant_id is not None:
                rating_stmt = rating_stmt.where(
                    Rating.service_assignment_id.in_(
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
        if tenant_id is not None and not scoped_ids:
            return None

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
        if tenant_id is not None and not scoped_ids:
            return None

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

    async def get_incident_zones(
        self, tenant_id: int | None = None
    ) -> list[dict]:
        """Group incidents by zone (rounded lat/lng) with count."""
        stmt = select(
            func.round(Incident.latitude, 2).label("lat"),
            func.round(Incident.longitude, 2).label("lng"),
            func.count(Incident.id).label("cnt"),
        ).where(
            Incident.latitude.isnot(None),
            Incident.longitude.isnot(None),
        )
        if tenant_id is not None:
            stmt = stmt.where(
                Incident.id.in_(
                    select(ServiceAssignment.incident_id).where(
                        ServiceAssignment.tenant_id == tenant_id
                    )
                )
            )
        stmt = stmt.group_by("lat", "lng").order_by(func.count(Incident.id).desc()).limit(20)
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            {"lat": float(r.lat), "lng": float(r.lng), "count": r.cnt, "label": f"{r.lat}, {r.lng}"}
            for r in rows
        ]

    async def get_workshop_efficiency(
        self, tenant_id: int | None = None
    ) -> list[dict]:
        """Rank workshops by efficiency (response time + completion rate + reputation)."""
        ws_stmt = select(Workshop.id)
        if tenant_id is not None:
            ws_stmt = ws_stmt.where(Workshop.tenant_id == tenant_id)
        ws_result = await self.session.execute(ws_stmt)
        ws_ids = [r[0] for r in ws_result.all()]

        rankings = []
        for ws_id in ws_ids:
            ws = await self.session.get(Workshop, ws_id)
            if not ws:
                continue

            total_assign = await self._scalar(
                select(func.count(ServiceAssignment.id)).where(
                    ServiceAssignment.workshop_id == ws_id
                )
            ) or 0

            completed_assign = await self._scalar(
                select(func.count(ServiceAssignment.id)).where(
                    ServiceAssignment.workshop_id == ws_id,
                    ServiceAssignment.assignment_status == "COMPLETADO",
                )
            ) or 0

            completion_rate = (
                round(completed_assign / total_assign, 4) if total_assign > 0 else None
            )

            # Avg response time (from assignment creation to EN_CAMINO or COMPLETADO)
            avg_resp = await self._scalar(
                select(
                    func.avg(
                        func.extract("epoch", ServiceAssignment.updated_at)
                        - func.extract("epoch", ServiceAssignment.assigned_at)
                    )
                    / 60
                ).where(
                    ServiceAssignment.workshop_id == ws_id,
                    ServiceAssignment.assignment_status.in_(["COMPLETADO", "EN_CAMINO"]),
                )
            )

            rankings.append({
                "workshop_id": ws.id,
                "name": ws.name,
                "score": round(float(ws.reputation_score or 0) * (completion_rate or 0.5), 2),
                "avg_response_minutes": round(float(avg_resp), 2) if avg_resp else None,
                "completion_rate": round(completion_rate * 100, 1) if completion_rate else None,
                "reputation_score": round(float(ws.reputation_score or 0), 2),
                "total_assignments": total_assign,
            })

        rankings.sort(key=lambda r: r["score"], reverse=True)
        return rankings[:20]
