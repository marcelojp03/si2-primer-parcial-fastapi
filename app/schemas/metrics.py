from pydantic import BaseModel, Field


class ZoneIncidentCount(BaseModel):
    lat: float
    lng: float
    count: int = 0
    label: str = ""


class WorkshopEfficiency(BaseModel):
    workshop_id: int
    name: str
    score: float = 0.0
    avg_response_minutes: float | None = None
    completion_rate: float | None = None
    reputation_score: float | None = None
    total_assignments: int = 0


class MetricsDashboard(BaseModel):
    total_incidents: int = 0
    incidents_by_status: dict[str, int] = {}
    incidents_by_priority: dict[str, int] = {}
    total_assignments: int = 0
    assignments_by_status: dict[str, int] = {}
    total_payments: int = 0
    total_revenue: float = 0.0
    average_rating: float | None = None
    total_ratings: int = 0
    total_workshops: int = 0
    total_technicians: int = 0


class KPIDashboard(BaseModel):
    """KPIs operacionales por tenant (CU33)."""

    tenant_id: int | None = None
    # Volumen
    total_incidents: int = 0
    incidents_last_30_days: int = 0
    # Tiempos de respuesta promedio (minutos)
    avg_response_minutes: float | None = None
    # SLA
    sla_compliance_pct: float | None = None  # % incidentes resueltos dentro del SLA
    # Asignaciones
    total_assignments: int = 0
    active_assignments: int = 0
    # Talleres
    active_workshops: int = 0
    avg_reputation_score: float | None = None
    # Ingresos
    total_revenue: float = 0.0
    # Calificaciones
    average_rating: float | None = None
