import logging
from contextlib import asynccontextmanager

from app.core.logging import setup_logging

setup_logging()

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("watchfiles").setLevel(logging.WARNING)

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.api.v1.api import api_router  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.db.init_db import init_db  # noqa: E402
from app.middlewares.access_log import AccessLogMiddleware  # noqa: E402
from app.middlewares.error_handler import ErrorHandlerMiddleware  # noqa: E402
from app.middlewares.request_id import RequestIdMiddleware  # noqa: E402

_log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Re-aplicar el file handler por si uvicorn lo pisó con su dictConfig (--reload)
    setup_logging()

    try:
        await init_db()
    except Exception as e:
        _log.warning("Could not connect to DB on startup: %s", e)

    try:
        from app.utils.firebase import _get_firebase_app

        fb = _get_firebase_app()
        if fb:
            _log.info("Firebase Admin SDK ready (project=%s)", settings.FIREBASE_PROJECT_ID)
        else:
            _log.warning("Firebase not initialized — push notifications will be skipped")
    except Exception as e:
        _log.warning("Firebase initialization failed: %s", e)

    # VPAY token status
    if settings.VPAY_TOKEN:
        _log.info(
            "VPAY token loaded (len=%d) base_url=%s",
            len(settings.VPAY_TOKEN),
            settings.VPAY_BASE_URL,
        )
    else:
        _log.warning("VPAY_TOKEN not set — QR payments will run in DEMO mode")

    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.API_V1_STR)

    # WebSocket endpoint (no prefix — clients connect to ws://host/ws)
    from app.ws.router import router as ws_router

    app.include_router(ws_router)

    return app


app = create_app()
