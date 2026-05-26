"""WebSocket typed event schemas."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


class WSMessage(BaseModel):
    """Envelope for all WebSocket messages."""

    type: str
    version: int = 1
    payload: dict[str, Any]
    ts: datetime


# ── Payload schemas ────────────────────────────────────────────


class IncidentStatusChangedPayload(BaseModel):
    incident_id: int
    old_status: str
    new_status: str


class LocationUpdatedPayload(BaseModel):
    incident_id: int
    latitude: float
    longitude: float
    recorded_at: datetime


class AssignmentInvitedPayload(BaseModel):
    incident_id: int
    workshop_id: int
    candidate_id: int
    deadline: datetime | None = None


class AssignmentAcceptedPayload(BaseModel):
    incident_id: int
    workshop_id: int
    assignment_id: int


class AssignmentRejectedPayload(BaseModel):
    incident_id: int
    workshop_id: int
    candidate_id: int


class NotificationPayload(BaseModel):
    notification_id: int
    title: str
    body: str
    channel: str


# ── Event type literals ────────────────────────────────────────

EventType = Literal[
    "incident.status_changed",
    "incident.location_updated",
    "assignment.invited",
    "assignment.accepted",
    "assignment.rejected",
    "notification.new",
    "ping",
    "pong",
]


def build_message(event_type: EventType, payload: BaseModel | dict) -> dict:
    """Build a serializable WS message dict."""
    payload_dict = payload.model_dump(mode="json") if isinstance(payload, BaseModel) else payload
    return WSMessage(
        type=event_type,
        version=1,
        payload=payload_dict,
        ts=datetime.utcnow(),
    ).model_dump(mode="json")
