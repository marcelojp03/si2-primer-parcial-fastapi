from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, SuperAdminUser
from app.schemas.user import UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_me(current_user: CurrentUser):
    return current_user


@router.get("/{user_id}", response_model=UserRead)
async def read_user(user_id: int, session: DbSession, _admin: SuperAdminUser):
    svc = UserService(session)
    return await svc.get_by_id(user_id)


@router.get("", response_model=list[UserRead])
async def list_users(session: DbSession, _admin: SuperAdminUser, skip: int = 0, limit: int = 100):
    svc = UserService(session)
    return await svc.get_all(skip=skip, limit=limit)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int, data: UserUpdate, session: DbSession, _current_user: CurrentUser
):
    svc = UserService(session)
    return await svc.update(user_id, data)
