from fastapi import APIRouter

from app.api.deps import AdminTallerOrSuperAdmin, DbSession, PlatformAdminUser, TenantId
from app.schemas.metrics import KPIDashboard, MetricsDashboard, WorkshopEfficiency, ZoneIncidentCount
from app.services.metrics_service import MetricsService

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/dashboard", response_model=MetricsDashboard)
async def get_dashboard(
    session: DbSession,
    _user: AdminTallerOrSuperAdmin,
    tenant_id: TenantId,
):
    svc = MetricsService(session)
    return await svc.get_dashboard(tenant_id=tenant_id)


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


@router.get("/zones", response_model=list[ZoneIncidentCount])
async def get_incident_zones(
    session: DbSession,
    _user: AdminTallerOrSuperAdmin,
    tenant_id: TenantId,
):
    """Zonas con más incidentes, agrupadas por coordenadas redondeadas."""
    svc = MetricsService(session)
    return await svc.get_incident_zones(tenant_id=tenant_id)


@router.get("/workshops/efficiency", response_model=list[WorkshopEfficiency])
async def get_workshop_efficiency(
    session: DbSession,
    _user: AdminTallerOrSuperAdmin,
    tenant_id: TenantId,
):
    """Ranking de talleres más eficientes por tiempo de respuesta y finalización."""
    svc = MetricsService(session)
    return await svc.get_workshop_efficiency(tenant_id=tenant_id)
