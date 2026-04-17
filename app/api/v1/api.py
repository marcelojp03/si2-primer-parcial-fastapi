from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai_analysis,
    assignments,
    auth,
    health,
    incident_statuses,
    incident_types,
    incidents,
    notifications,
    payments,
    ratings,
    specialties,
    technicians,
    users,
    vehicles,
    workshops,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(workshops.router)
api_router.include_router(vehicles.router)
api_router.include_router(incidents.router)
api_router.include_router(incident_types.router)
api_router.include_router(incident_statuses.router)
api_router.include_router(ai_analysis.router)
api_router.include_router(assignments.router)
api_router.include_router(payments.router)
api_router.include_router(notifications.router)
api_router.include_router(specialties.router)
api_router.include_router(technicians.router)
api_router.include_router(ratings.router)
