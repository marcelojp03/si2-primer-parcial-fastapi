import re
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.workshop import Workshop
from app.repositories.tenant_repository import TenantRepository
from app.repositories.workshop_repository import WorkshopRepository
from app.schemas.workshop import WorkshopCreate, WorkshopUpdate

_DEFAULT_TENANT_SLUG = "default"


class WorkshopService:
    def __init__(self, session: AsyncSession):
        self.repo = WorkshopRepository(session)
        self._session = session

    async def _resolve_tenant_id(self, tenant_id: int | None) -> int:
        """Return tenant_id if provided, otherwise fall back to the default tenant."""
        if tenant_id is not None:
            return tenant_id
        tenant_repo = TenantRepository(self._session)
        default = await tenant_repo.get_by_slug(_DEFAULT_TENANT_SLUG)
        if default is None:
            raise NotFoundError("Default tenant not found — run migrations first")
        return default.id

    async def create(self, data: WorkshopCreate, tenant_id: int | None = None) -> Workshop:
        # If no tenant_id provided, auto-create a tenant (1:1 workshop <-> tenant)
        if tenant_id is None:
            from app.models.tenant import Tenant
            slug = re.sub(r'[^a-z0-9]', '-', data.name.lower().strip())[:50]
            tenant = Tenant(name=data.name, slug=slug)
            self._session.add(tenant)
            await self._session.flush()
            resolved_tenant_id = tenant.id
        else:
            resolved_tenant_id = await self._resolve_tenant_id(tenant_id)
        workshop = Workshop(**data.model_dump(), tenant_id=resolved_tenant_id)
        return await self.repo.create(workshop)

    async def get_by_id(self, workshop_id: int) -> Workshop:
        workshop = await self.repo.get_by_id(workshop_id)
        if not workshop:
            raise NotFoundError("Workshop not found")
        return workshop

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Workshop]:
        return await self.repo.get_all(skip=skip, limit=limit)

    async def get_by_tenant(self, tenant_id: int, skip: int = 0, limit: int = 100) -> Sequence[Workshop]:
        return await self.repo.get_by_tenant(tenant_id, skip=skip, limit=limit)

    async def update(self, workshop_id: int, data: WorkshopUpdate) -> Workshop:
        workshop = await self.get_by_id(workshop_id)
        return await self.repo.update(workshop, data.model_dump(exclude_unset=True))
