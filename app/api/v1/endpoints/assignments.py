from fastapi import APIRouter

from app.api.deps import AdminTallerOrSuperAdmin, DbSession

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.post("/{incident_id}")
async def assign_workshop(incident_id: int, session: DbSession, _user: AdminTallerOrSuperAdmin):
    """Trigger intelligent assignment for an incident (placeholder)."""
    return {"detail": "Assignment engine not yet implemented", "incident_id": incident_id}
