from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.incident_evidence import IncidentEvidence
from app.repositories.incident_evidence_repository import IncidentEvidenceRepository
from app.schemas.incident_evidence import IncidentEvidenceCreate


class IncidentEvidenceService:
    def __init__(self, session: AsyncSession):
        self.repo = IncidentEvidenceRepository(session)

    async def create(self, data: IncidentEvidenceCreate) -> IncidentEvidence:
        evidence = IncidentEvidence(**data.model_dump())
        return await self.repo.create(evidence)

    async def get_by_id(self, evidence_id: int) -> IncidentEvidence:
        evidence = await self.repo.get_by_id(evidence_id)
        if not evidence:
            raise NotFoundError("Incident evidence not found")
        return evidence

    async def get_by_incident(self, incident_id: int) -> Sequence[IncidentEvidence]:
        return await self.repo.get_by_incident(incident_id)

    async def delete(self, evidence_id: int) -> None:
        evidence = await self.get_by_id(evidence_id)
        await self.repo.delete(evidence)
