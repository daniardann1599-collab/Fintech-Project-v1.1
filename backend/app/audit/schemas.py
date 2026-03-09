from datetime import datetime

from pydantic import BaseModel

from app.models.entities import EventStatus


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    action: str
    timestamp: datetime
    outcome: str

    class Config:
        from_attributes = True


class OutboxEventResponse(BaseModel):
    id: int
    aggregate_type: str
    aggregate_id: str
    event_type: str
    payload: dict
    status: EventStatus
    created_at: datetime
    processed_at: datetime | None

    class Config:
        from_attributes = True
