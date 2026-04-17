from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.schemas.auth import LoginRequest, TokenResponse, TokenPayload
from app.schemas.workshop import WorkshopCreate, WorkshopRead, WorkshopUpdate
from app.schemas.vehicle import VehicleCreate, VehicleRead, VehicleUpdate
from app.schemas.incident import IncidentCreate, IncidentRead, IncidentUpdate
from app.schemas.payment import PaymentCreate, PaymentRead, PaymentUpdate
from app.schemas.notification import NotificationCreate, NotificationRead
from app.schemas.specialty import SpecialtyCreate, SpecialtyRead, SpecialtyUpdate
from app.schemas.technician import TechnicianCreate, TechnicianRead, TechnicianUpdate
from app.schemas.rating import RatingCreate, RatingRead
from app.schemas.assignment import AssignmentCreate, AssignmentRead, AssignmentUpdate

__all__ = [
    "UserCreate", "UserRead", "UserUpdate",
    "LoginRequest", "TokenResponse", "TokenPayload",
    "WorkshopCreate", "WorkshopRead", "WorkshopUpdate",
    "VehicleCreate", "VehicleRead", "VehicleUpdate",
    "IncidentCreate", "IncidentRead", "IncidentUpdate",
    "PaymentCreate", "PaymentRead", "PaymentUpdate",
    "NotificationCreate", "NotificationRead",
    "SpecialtyCreate", "SpecialtyRead", "SpecialtyUpdate",
    "TechnicianCreate", "TechnicianRead", "TechnicianUpdate",
    "RatingCreate", "RatingRead",
    "AssignmentCreate", "AssignmentRead", "AssignmentUpdate",
]
