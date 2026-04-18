from pydantic import BaseModel


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
