import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Logger propio → propaga al root → llega al RotatingFileHandler
logger = logging.getLogger("app.access")

# Rutas que no vale la pena loguear (health checks, docs)
_SKIP_PATHS = {"/", "/health", "/docs", "/redoc", "/openapi.json"}


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            request_id = getattr(request.state, "request_id", "-")
            client_ip = request.client.host if request.client else "-"
            level = logging.WARNING if status >= 400 else logging.INFO
            logger.log(
                level,
                "%s %s %d | %.1fms | ip=%s | req=%s",
                request.method,
                request.url.path,
                status,
                duration_ms,
                client_ip,
                request_id,
            )

        return response
