from app.schemas.assignment import AssignmentCreate, AssignmentRead, AssignmentUpdate
from app.schemas.auth import LoginRequest, TokenPayload, TokenResponse
from app.schemas.incident import IncidentCreate, IncidentRead, IncidentUpdate
from app.schemas.incident_evidence import IncidentEvidenceCreate, IncidentEvidenceRead
from app.schemas.incident_status_history import (
    IncidentStatusHistoryCreate,
    IncidentStatusHistoryRead,
)
from app.schemas.notification import NotificationCreate, NotificationRead
from app.schemas.payment import PaymentCreate, PaymentRead, PaymentUpdate
from app.schemas.rating import RatingCreate, RatingRead
from app.schemas.specialty import SpecialtyCreate, SpecialtyRead, SpecialtyUpdate
from app.schemas.technician import TechnicianCreate, TechnicianRead, TechnicianUpdate
from app.schemas.technician_specialty import TechnicianSpecialtyCreate, TechnicianSpecialtyRead
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.schemas.vehicle import VehicleCreate, VehicleRead, VehicleUpdate
from app.schemas.workshop import WorkshopCreate, WorkshopRead, WorkshopUpdate
from app.schemas.workshop_candidate import (
    WorkshopCandidateCreate,
    WorkshopCandidateRead,
    WorkshopCandidateUpdate,
)
from app.schemas.workshop_schedule import (
    WorkshopScheduleCreate,
    WorkshopScheduleRead,
    WorkshopScheduleUpdate,
)
from app.schemas.workshop_specialty import WorkshopSpecialtyCreate, WorkshopSpecialtyRead

__all__ = [
    "AssignmentCreate",
    "AssignmentRead",
    "AssignmentUpdate",
    "IncidentCreate",
    "IncidentEvidenceCreate",
    "IncidentEvidenceRead",
    "IncidentRead",
    "IncidentStatusHistoryCreate",
    "IncidentStatusHistoryRead",
    "IncidentUpdate",
    "LoginRequest",
    "NotificationCreate",
    "NotificationRead",
    "PaymentCreate",
    "PaymentRead",
    "PaymentUpdate",
    "RatingCreate",
    "RatingRead",
    "SpecialtyCreate",
    "SpecialtyRead",
    "SpecialtyUpdate",
    "TechnicianCreate",
    "TechnicianRead",
    "TechnicianSpecialtyCreate",
    "TechnicianSpecialtyRead",
    "TechnicianUpdate",
    "TokenPayload",
    "TokenResponse",
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "VehicleCreate",
    "VehicleRead",
    "VehicleUpdate",
    "WorkshopCandidateCreate",
    "WorkshopCandidateRead",
    "WorkshopCandidateUpdate",
    "WorkshopCreate",
    "WorkshopRead",
    "WorkshopScheduleCreate",
    "WorkshopScheduleRead",
    "WorkshopScheduleUpdate",
    "WorkshopSpecialtyCreate",
    "WorkshopSpecialtyRead",
    "WorkshopUpdate",
]
