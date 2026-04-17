from app.schemas.assignment import AssignmentCreate, AssignmentRead, AssignmentUpdate
from app.schemas.auth import LoginRequest, TokenPayload, TokenResponse
from app.schemas.incident import IncidentCreate, IncidentRead, IncidentUpdate
from app.schemas.notification import NotificationCreate, NotificationRead
from app.schemas.payment import PaymentCreate, PaymentRead, PaymentUpdate
from app.schemas.rating import RatingCreate, RatingRead
from app.schemas.specialty import SpecialtyCreate, SpecialtyRead, SpecialtyUpdate
from app.schemas.technician import TechnicianCreate, TechnicianRead, TechnicianUpdate
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.schemas.vehicle import VehicleCreate, VehicleRead, VehicleUpdate
from app.schemas.workshop import WorkshopCreate, WorkshopRead, WorkshopUpdate

__all__ = [
    "AssignmentCreate",
    "AssignmentRead",
    "AssignmentUpdate",
    "IncidentCreate",
    "IncidentRead",
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
    "TechnicianUpdate",
    "TokenPayload",
    "TokenResponse",
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "VehicleCreate",
    "VehicleRead",
    "VehicleUpdate",
    "WorkshopCreate",
    "WorkshopRead",
    "WorkshopUpdate",
]
