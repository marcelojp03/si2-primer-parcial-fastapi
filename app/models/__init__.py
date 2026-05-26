# Re-export all models so that Alembic and the app can import them from a single place.
from app.models.incident import Incident
from app.models.incident_ai_analysis import IncidentAiAnalysis
from app.models.incident_evidence import IncidentEvidence
from app.models.incident_location_track import IncidentLocationTrack
from app.models.incident_status import IncidentStatus
from app.models.incident_status_history import IncidentStatusHistory
from app.models.incident_type import IncidentType
from app.models.notification import Notification
from app.models.payment import Payment
from app.models.rating import Rating
from app.models.service_assignment import ServiceAssignment
from app.models.specialty import Specialty
from app.models.technician import Technician
from app.models.technician_specialty import TechnicianSpecialty
from app.models.tenant import Tenant
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.workshop import Workshop
from app.models.workshop_candidate import WorkshopCandidate
from app.models.workshop_schedule import WorkshopSchedule
from app.models.workshop_specialty import WorkshopSpecialty

__all__ = [
    "Incident",
    "IncidentAiAnalysis",
    "IncidentEvidence",
    "IncidentLocationTrack",
    "IncidentStatus",
    "IncidentStatusHistory",
    "IncidentType",
    "Notification",
    "Payment",
    "Rating",
    "ServiceAssignment",
    "Specialty",
    "Technician",
    "TechnicianSpecialty",
    "Tenant",
    "User",
    "Vehicle",
    "Workshop",
    "WorkshopCandidate",
    "WorkshopSchedule",
    "WorkshopSpecialty",
]
