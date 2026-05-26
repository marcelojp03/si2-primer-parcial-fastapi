import re

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.deps import AdminTallerOrSuperAdmin, DbSession, TenantId
from app.services.nl_report_service import NLReportService

router = APIRouter(prefix="/reports", tags=["reports"])

# ── Schemas ────────────────────────────────────────────────


class NLReportRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Pregunta en lenguaje natural, p.ej. '¿Cuántos incidentes hubo este mes?'",
    )


class NLReportResponse(BaseModel):
    query: str
    sql: str
    data: list[dict]
    rows_count: int


# ── Endpoints ─────────────────────────────────────────────


@router.post("/nl", response_model=NLReportResponse)
async def natural_language_report(
    body: NLReportRequest,
    session: DbSession,
    _user: AdminTallerOrSuperAdmin,
    tenant_id: TenantId,
):
    """Genera un reporte a partir de una consulta en lenguaje natural.

    El backend usa OpenAI para convertir la pregunta a SQL y ejecutarla
    de forma segura (solo SELECT). Solo devuelve datos del tenant del
    usuario (excepto ADMIN_PLATAFORMA que puede ver todo).
    """
    svc = NLReportService(session)
    return await svc.run(body.query, tenant_id=tenant_id)
