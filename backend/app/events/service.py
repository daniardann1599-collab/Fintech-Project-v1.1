from sqlalchemy.orm import Session

from app.models.entities import OutboxEvent


def enqueue_event(
    db: Session,
    aggregate_type: str,
    aggregate_id: str,
    event_type: str,
    payload: dict,
) -> OutboxEvent:
    event = OutboxEvent(
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        event_type=event_type,
        payload=payload,
    )
    db.add(event)
    return event
