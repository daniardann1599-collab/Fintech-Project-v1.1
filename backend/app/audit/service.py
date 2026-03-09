from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.entities import AuditLog

logger = get_logger("banking.audit")


def log_action(db: Session, user_id: int | None, action: str, outcome: str) -> AuditLog:
    log = AuditLog(user_id=user_id, action=action, outcome=outcome)
    db.add(log)
    logger.info(
        "audit.log_created",
        extra={
            "extra_fields": {
                "user_id": user_id,
                "action": action,
                "outcome": outcome,
            }
        },
    )
    return log
