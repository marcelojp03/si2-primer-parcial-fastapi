from typing import Annotated, AsyncGenerator

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
AdminTallerOrSuperAdmin = Annotated[User, Depends(require_role(UserRole.ADMIN_TALLER, UserRole.SUPERADMIN))]
ClienteUser = Annotated[User, Depends(require_role(UserRole.CLIENTE))]
ClienteOrSuperAdmin = Annotated[User, Depends(require_role(UserRole.CLIENTE, UserRole.SUPERADMIN))]
