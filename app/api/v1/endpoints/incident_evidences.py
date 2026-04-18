from fastapi import APIRouter

from app.api.deps import ClienteOrSuperAdmin, CurrentUser, DbSession
from app.schemas.incident_evidence import IncidentEvidenceCreate, IncidentEvidenceRead
from app.services.incident_evidence_service import IncidentEvidenceService

router = APIRouter(prefix="/incident-evidences", tags=["incident-evidences"])


@router.post("", response_model=IncidentEvidenceRead, status_code=201)
async def create_evidence(
    data: IncidentEvidenceCreate, session: DbSession, _user: ClienteOrSuperAdmin
):
    svc = IncidentEvidenceService(session)
    return await svc.create(data)


@router.get("/incident/{incident_id}", response_model=list[IncidentEvidenceRead])
async def list_evidences_by_incident(incident_id: int, session: DbSession, _user: CurrentUser):
    svc = IncidentEvidenceService(session)
    return await svc.get_by_incident(incident_id)


@router.get("/{evidence_id}", response_model=IncidentEvidenceRead)
async def read_evidence(evidence_id: int, session: DbSession, _user: CurrentUser):
    svc = IncidentEvidenceService(session)
    return await svc.get_by_id(evidence_id)


@router.delete("/{evidence_id}", status_code=204)
async def delete_evidence(evidence_id: int, session: DbSession, _user: ClienteOrSuperAdmin):
    svc = IncidentEvidenceService(session)
    await svc.delete(evidence_id)
