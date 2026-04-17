from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, SuperAdminUser
from app.schemas.notification import NotificationCreate, NotificationRead
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("", response_model=NotificationRead, status_code=201)
async def create_notification(data: NotificationCreate, session: DbSession, _admin: SuperAdminUser):
    svc = NotificationService(session)
    return await svc.create(data)


@router.get("", response_model=list[NotificationRead])
async def list_my_notifications(session: DbSession, current_user: CurrentUser):
    svc = NotificationService(session)
    return await svc.get_by_user_id(current_user.id)
