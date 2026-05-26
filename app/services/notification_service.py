import logging
from collections.abc import Sequence
from datetime import UTC

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import NotificationCreate
from app.utils.firebase import send_push_notification
from app.ws.events import NotificationPayload, build_message
from app.ws.manager import ws_manager

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, session: AsyncSession):
        self.repo = NotificationRepository(session)

    async def create(self, data: NotificationCreate) -> Notification:
        notification = Notification(**data.model_dump())
        return await self.repo.create(notification)

    async def create_and_push(
        self, data: NotificationCreate, device_token: str | None = None
    ) -> Notification:
        """Create a DB notification record, emit WS, and optionally send FCM push."""
        notification = await self.create(data)

        # Always emit to the user's personal WebSocket channel
        if data.user_id:
            ws_payload = NotificationPayload(
                notification_id=notification.id,
                title=data.title,
                body=data.message,
                channel=data.channel,
            )
            await ws_manager.send_to_user(
                data.user_id,
                build_message("notification.new", ws_payload),
            )

        if device_token and data.channel == "PUSH":
            extra = {"incident_id": str(data.incident_id)} if data.incident_id else {}
            msg_id = await send_push_notification(
                device_token=device_token,
                title=data.title,
                body=data.message,
                data=extra,
            )
            if msg_id:
                from datetime import datetime

                notification.status = "ENVIADO"
                notification.sent_at = datetime.now(UTC)
                await self.repo.update(notification, {"status": "ENVIADO"})
                logger.info("Push sent for notification id=%d", notification.id)

        return notification

    async def get_by_user_id(self, user_id: int) -> Sequence[Notification]:
        return await self.repo.get_by_user_id(user_id)
