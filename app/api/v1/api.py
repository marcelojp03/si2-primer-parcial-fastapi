from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai_analysis,
    assignments,
    auth,
    health,
    incident_evidences,
    incident_status_history,
    incident_statuses,
    incident_types,
    incidents,
    metrics,
    notifications,
    payments,
    ratings,
    reports,
    specialties,
    technician_specialties,
    technicians,
    tenants,
    users,
    vehicles,
    workshop_schedules,
    workshop_specialties,
    workshops,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(tenants.router)
api_router.include_router(workshops.router)
api_router.include_router(workshop_schedules.router)
api_router.include_router(workshop_specialties.router)
api_router.include_router(vehicles.router)
api_router.include_router(incidents.router)
api_router.include_router(incident_types.router)
api_router.include_router(incident_statuses.router)
api_router.include_router(incident_evidences.router)
api_router.include_router(incident_status_history.router)
api_router.include_router(ai_analysis.router)
api_router.include_router(assignments.router)
api_router.include_router(payments.router)
api_router.include_router(notifications.router)
api_router.include_router(specialties.router)
api_router.include_router(technicians.router)
api_router.include_router(technician_specialties.router)
api_router.include_router(ratings.router)
api_router.include_router(metrics.router)
api_router.include_router(reports.router)
