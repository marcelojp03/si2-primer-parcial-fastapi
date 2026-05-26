from fastapi import APIRouter

from app.api.deps import AdminTallerOrSuperAdmin, DbSession, PlatformAdminUser
from app.schemas.tenant import TenantCreate, TenantRead, TenantUpdate
from app.services.tenant_service import TenantService

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=TenantRead, status_code=201)
async def create_tenant(data: TenantCreate, session: DbSession, _admin: PlatformAdminUser):
    """Crea un nuevo tenant (taller SaaS). Solo ADMIN_PLATAFORMA."""
    svc = TenantService(session)
    return await svc.create(data)


@router.get("", response_model=list[TenantRead])
async def list_tenants(
    session: DbSession,
    _admin: PlatformAdminUser,
    skip: int = 0,
    limit: int = 100,
):
    """Lista todos los tenants. Solo ADMIN_PLATAFORMA."""
    svc = TenantService(session)
    return await svc.get_all(skip=skip, limit=limit)


@router.get("/{tenant_id}", response_model=TenantRead)
async def get_tenant(tenant_id: int, session: DbSession, _user: AdminTallerOrSuperAdmin):
    """Obtiene un tenant por ID."""
    svc = TenantService(session)
    return await svc.get_by_id(tenant_id)


@router.patch("/{tenant_id}", response_model=TenantRead)
async def update_tenant(
    tenant_id: int, data: TenantUpdate, session: DbSession, _admin: PlatformAdminUser
):
    """Actualiza nombre o estado de un tenant. Solo ADMIN_PLATAFORMA."""
    svc = TenantService(session)
    return await svc.update(tenant_id, data)
