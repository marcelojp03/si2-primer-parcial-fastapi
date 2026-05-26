from fastapi import APIRouter

from app.api.deps import AdminTallerOrSuperAdmin, DbSession, PlatformAdminUser, TenantId
from app.schemas.metrics import KPIDashboard, MetricsDashboard
from app.services.metrics_service import MetricsService

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/dashboard", response_model=MetricsDashboard)
async def get_dashboard(session: DbSession, _user: AdminTallerOrSuperAdmin):
    svc = MetricsService(session)
    return await svc.get_dashboard()


@router.get("/kpis", response_model=KPIDashboard)
async def get_kpis(
    session: DbSession,
    _user: AdminTallerOrSuperAdmin,
    tenant_id: TenantId,
):
    """KPIs operacionales.

    - **ADMIN_TALLER**: recibe `tenant_id` automáticamente desde el JWT.
    - **ADMIN_PLATAFORMA**: puede pasar `?tenant_id=N` en el query para ver un tenant específico.
    """
    svc = MetricsService(session)
    return await svc.get_kpis(tenant_id=tenant_id)
