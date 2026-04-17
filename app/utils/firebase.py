import logging

import firebase_admin
from firebase_admin import credentials, messaging

from app.core.config import settings

logger = logging.getLogger(__name__)

_firebase_app: firebase_admin.App | None = None


def _get_firebase_app() -> firebase_admin.App | None:
    """Lazy-init the Firebase Admin SDK. Returns None if credentials are missing."""
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    cred_path = settings.FIREBASE_CREDENTIALS_FILE
    if not cred_path:
        logger.warning("FIREBASE_CREDENTIALS_FILE not set — push notifications disabled")
        return None

    import os

    if not os.path.isfile(cred_path):
        logger.warning("Firebase credentials file not found at '%s'", cred_path)
        return None

    cred = credentials.Certificate(cred_path)
    _firebase_app = firebase_admin.initialize_app(cred)
    logger.info("Firebase Admin SDK initialized (project=%s)", settings.FIREBASE_PROJECT_ID)
    return _firebase_app


async def send_push_notification(
    device_token: str,
    title: str,
    body: str,
    data: dict[str, str] | None = None,
) -> str | None:
    """
    Send a push notification via FCM.
    Returns the message ID on success, or None if Firebase is not configured.
    """
    app = _get_firebase_app()
    if app is None:
        logger.debug("Firebase not configured — skipping push for token=%s...", device_token[:12])
        return None

    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
        token=device_token,
    )

    try:
        response = messaging.send(message, app=app)
        logger.info("Push sent: message_id=%s", response)
        return response
    except messaging.UnregisteredError:
        logger.warning("Device token unregistered: %s...", device_token[:12])
        return None
    except Exception:
        logger.exception("Failed to send push notification")
        return None


async def send_push_to_multiple(
    device_tokens: list[str],
    title: str,
    body: str,
    data: dict[str, str] | None = None,
) -> int:
    """
    Send a push notification to multiple devices.
    Returns the count of successfully sent messages.
    """
    app = _get_firebase_app()
    if app is None:
        return 0

    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
        tokens=device_tokens,
    )

    try:
        response = messaging.send_each_for_multicast(message, app=app)
        logger.info(
            "Multicast push: success=%d failure=%d",
            response.success_count,
            response.failure_count,
        )
        return response.success_count
    except Exception:
        logger.exception("Failed to send multicast push")
        return 0
