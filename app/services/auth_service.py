from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate
from app.utils.enums import UserRole

ALLOWED_REGISTER_ROLES = {UserRole.CLIENTE.value, UserRole.ADMIN_TALLER.value}


class AuthService:
    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)

    async def register(self, data: UserCreate) -> User:
        if data.role.lower() not in ALLOWED_REGISTER_ROLES:
            raise BadRequestError(
                f"Role '{data.role}' not allowed for self-registration. Use: {', '.join(ALLOWED_REGISTER_ROLES)}"
            )
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise ConflictError("Email already registered")
        user = User(
            role=data.role,
            full_name=data.full_name,
            ci=data.ci,
            phone=data.phone,
            email=data.email,
            password_hash=hash_password(data.password),
        )
        return await self.repo.create(user)

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self.repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        token = create_access_token(subject=user.id)
        return TokenResponse(access_token=token)
