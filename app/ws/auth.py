"""WebSocket JWT authentication helper."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.user_repository import UserRepository


async def authenticate_ws_token(token: str, session: AsyncSession) -> User:
    """Validate a JWT token for a WebSocket handshake.

    Raises UnauthorizedError if the token is invalid or the user is not found.
    """
    try:
        payload = decode_access_token(token)
    except Exception as exc:
        raise UnauthorizedError("Invalid or expired WebSocket token") from exc

    if payload is None:
        raise UnauthorizedError("Invalid WebSocket token payload")

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Missing subject in WebSocket token")

    repo = UserRepository(session)
    user = await repo.get_by_id(int(user_id))
    if user is None:
        raise UnauthorizedError("WebSocket user not found")

    return user


def extract_tenant_id(token: str) -> int | None:
    """Extract tenant_id from a JWT without re-validating the signature.

    Only call this AFTER authenticate_ws_token has already validated the token.
    """
    try:
        payload = decode_access_token(token)
        raw = payload.get("tenant_id")
        return int(raw) if raw is not None else None
    except Exception:
        return None


def extract_is_platform_admin(token: str) -> bool:
    """Extract is_platform_admin claim from an already-validated JWT."""
    try:
        payload = decode_access_token(token)
        return bool(payload.get("is_platform_admin", False))
    except Exception:
        return False
