from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.schemas import AuditLogResponse, OutboxEventResponse
from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.entities import AuditLog, EventStatus, OutboxEvent, User

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs", response_model=list[AuditLogResponse])
def get_audit_logs(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[AuditLogResponse]:
    return list(db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(500)))


@router.get("/outbox", response_model=list[OutboxEventResponse])
def get_outbox_events(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[OutboxEventResponse]:
    return list(db.scalars(select(OutboxEvent).order_by(OutboxEvent.id.desc()).limit(500)))


@router.post("/outbox/flush", response_model=list[OutboxEventResponse])
def flush_outbox(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[OutboxEventResponse]:
    pending_events = list(
        db.scalars(select(OutboxEvent).where(OutboxEvent.status == EventStatus.PENDING))
    )
    for event in pending_events:
        event.status = EventStatus.PROCESSED
        event.processed_at = datetime.now(timezone.utc)
    db.commit()
    return pending_events
