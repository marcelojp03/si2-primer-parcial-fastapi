from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.tenant import Tenant
from app.repositories.tenant_repository import TenantRepository
from app.schemas.tenant import TenantCreate, TenantUpdate


class TenantService:
    def __init__(self, session: AsyncSession):
        self.repo = TenantRepository(session)

    async def create(self, data: TenantCreate) -> Tenant:
        existing = await self.repo.get_by_slug(data.slug)
        if existing:
            raise ConflictError(f"Tenant with slug '{data.slug}' already exists")
        tenant = Tenant(name=data.name, slug=data.slug)
        return await self.repo.create(tenant)

    async def get_by_id(self, tenant_id: int) -> Tenant:
        tenant = await self.repo.get_by_id(tenant_id)
        if not tenant:
            raise NotFoundError("Tenant not found")
        return tenant

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Tenant]:
        return list(await self.repo.get_all(skip=skip, limit=limit))

    async def update(self, tenant_id: int, data: TenantUpdate) -> Tenant:
        tenant = await self.get_by_id(tenant_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(tenant, field, value)
        await self.repo.session.flush()
        await self.repo.session.refresh(tenant)
        return tenant
