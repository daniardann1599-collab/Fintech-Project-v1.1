from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.entities import OutboxEvent

logger = get_logger("banking.events")


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
    logger.info(
        "outbox.event_enqueued",
        extra={
            "extra_fields": {
                "aggregate_type": aggregate_type,
                "aggregate_id": aggregate_id,
                "event_type": event_type,
            }
        },
    )
    return event
