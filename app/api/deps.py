from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_async_session
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.enums import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_async_session():
        yield session


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedError("Invalid or expired token")
    user_id: int | None = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token payload")
    repo = UserRepository(session)
    user = await repo.get_by_id(int(user_id))
    if user is None:
        raise UnauthorizedError("User not found")
    return user


def require_role(*allowed_roles: UserRole):
    """Dependency factory that restricts access to specific roles."""

    async def _check_role(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role.lower() not in {r.value for r in allowed_roles}:
            raise ForbiddenError(
                f"Role '{current_user.role}' not allowed. Required: {', '.join(r.value for r in allowed_roles)}"
            )
        return current_user

    return _check_role


CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db)]

# ── Role-scoped user dependencies ──────────────────────────────
SuperAdminUser = Annotated[User, Depends(require_role(UserRole.SUPERADMIN))]
AdminTallerUser = Annotated[User, Depends(require_role(UserRole.ADMIN_TALLER))]
AdminTallerOrSuperAdmin = Annotated[
    User, Depends(require_role(UserRole.ADMIN_TALLER, UserRole.SUPERADMIN))
]
ClienteUser = Annotated[User, Depends(require_role(UserRole.CLIENTE))]
ClienteOrSuperAdmin = Annotated[User, Depends(require_role(UserRole.CLIENTE, UserRole.SUPERADMIN))]


# ── Multi-tenant helpers ────────────────────────────────────────

async def _require_platform_admin(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Guard: user must be SUPERADMIN with is_platform_admin = True in the JWT."""
    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedError("Invalid or expired token")
    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token payload")
    repo = UserRepository(session)
    user = await repo.get_by_id(int(user_id))
    if user is None:
        raise UnauthorizedError("User not found")
    if not payload.get("is_platform_admin", False):
        raise ForbiddenError("Platform administrator access required")
    return user


def get_tenant_id_from_token(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> int | None:
    """Extract tenant_id claim from JWT. Returns None for CLIENTE / ADMIN_PLATAFORMA."""
    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedError("Invalid or expired token")
    raw = payload.get("tenant_id")
    return int(raw) if raw is not None else None


def require_tenant():
    """Dependency factory: ensures the caller has a tenant_id in JWT (ADMIN_TALLER)."""

    async def _check_tenant(
        token: Annotated[str, Depends(oauth2_scheme)],
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        payload = decode_access_token(token)
        if payload is None:
            raise UnauthorizedError("Invalid or expired token")
        if payload.get("tenant_id") is None:
            raise ForbiddenError("This endpoint requires a tenant-scoped account")
        return current_user

    return _check_tenant


AdminPlataformaUser = Annotated[User, Depends(_require_platform_admin)]
# Alias en inglés para consistencia con instrucciones del proyecto
PlatformAdminUser = AdminPlataformaUser
TenantScopedUser = Annotated[User, Depends(require_tenant())]
TenantId = Annotated[int | None, Depends(get_tenant_id_from_token)]
