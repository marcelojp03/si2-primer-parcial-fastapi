from fastapi import APIRouter

from app.api.deps import AdminTallerOrSuperAdmin, DbSession
from app.schemas.metrics import MetricsDashboard
from app.services.metrics_service import MetricsService

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/dashboard", response_model=MetricsDashboard)
async def get_dashboard(session: DbSession, _user: AdminTallerOrSuperAdmin):
    svc = MetricsService(session)
    return await svc.get_dashboard()
