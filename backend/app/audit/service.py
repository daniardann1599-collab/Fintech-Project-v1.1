from sqlalchemy.orm import Session

from app.models.entities import AuditLog


def log_action(db: Session, user_id: int | None, action: str, outcome: str) -> AuditLog:
    log = AuditLog(user_id=user_id, action=action, outcome=outcome)
    db.add(log)
    return log
