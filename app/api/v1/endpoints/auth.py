from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=201)
async def register(data: UserCreate, session: DbSession):
    svc = AuthService(session)
    return await svc.register(data)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, session: DbSession):
    svc = AuthService(session)
    return await svc.login(data)
